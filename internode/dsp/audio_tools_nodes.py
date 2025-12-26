# ComfyUI/custom_nodes/ComfyUI-Internode/audio_tools_nodes.py
# VERSION: 3.0.0

import torch
import numpy as np
import os
import folder_paths

# Try importing Demucs
DEMUCS_AVAILABLE = False
try:
    from demucs.apply import apply_model
    from demucs.pretrained import get_model
    DEMUCS_AVAILABLE = True
except ImportError:
    pass

class InternodeSidechain:
    """
    Automatically lowers the volume of 'music' when 'voice' has signal.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "music": ("AUDIO",),
                "voice": ("AUDIO",),
                "threshold": ("FLOAT", {"default": 0.02, "min": 0.001, "max": 0.5, "step": 0.001, "display": "slider"}),
                "ratio": ("FLOAT", {"default": 4.0, "min": 1.1, "max": 20.0, "step": 0.1, "display": "slider"}),
                "attack": ("FLOAT", {"default": 0.1, "min": 0.01, "max": 1.0, "step": 0.01}),
                "release": ("FLOAT", {"default": 0.5, "min": 0.01, "max": 2.0, "step": 0.01}),
                "makeup_gain": ("FLOAT", {"default": 1.0, "min": 1.0, "max": 2.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("ducked_music",)
    FUNCTION = "apply_sidechain"
    CATEGORY = "Internode/AudioFX"

    def apply_sidechain(self, music, voice, threshold, ratio, attack, release, makeup_gain):
        music_wav = music["waveform"] 
        voice_wav = voice["waveform"]
        sr = music["sample_rate"]

        if music_wav.shape[0] != voice_wav.shape[0]:
            voice_wav = voice_wav[0].repeat(music_wav.shape[0], 1, 1)

        target_len = music_wav.shape[-1]
        voice_len = voice_wav.shape[-1]
        
        if voice_len < target_len:
            pad = target_len - voice_len
            voice_wav = torch.nn.functional.pad(voice_wav, (0, pad))
        elif voice_len > target_len:
            voice_wav = voice_wav[..., :target_len]

        output_batch = []
        
        for b in range(music_wav.shape[0]):
            m_track = music_wav[b]
            v_track = voice_wav[b]
            
            control = torch.mean(torch.abs(v_track), dim=0) 
            
            # Envelope
            kernel_size = int(sr * attack)
            if kernel_size % 2 == 0: kernel_size += 1
            if kernel_size > 1:
                envelope = torch.nn.functional.avg_pool1d(
                    control.unsqueeze(0).unsqueeze(0), 
                    kernel_size=kernel_size, 
                    stride=1, 
                    padding=kernel_size//2
                ).squeeze()
                envelope = envelope[:target_len]
            else:
                envelope = control

            # Ducking
            gain_map = torch.ones_like(envelope)
            over_thresh = envelope > threshold
            
            compression = (envelope[over_thresh] - threshold) * (1.0 - (1.0 / ratio))
            gain_map[over_thresh] = 1.0 - (compression * 2.0)
            
            gain_map = torch.clamp(gain_map, 0.0, 1.0)
            
            if release > 0:
                rel_k = int(sr * release * 0.5) 
                if rel_k % 2 == 0: rel_k += 1
                gain_map = torch.nn.functional.avg_pool1d(
                    gain_map.unsqueeze(0).unsqueeze(0),
                    kernel_size=rel_k,
                    stride=1,
                    padding=rel_k//2
                ).squeeze()[:target_len]

            gain_map_expanded = gain_map.unsqueeze(0).repeat(m_track.shape[0], 1)
            out_track = m_track * gain_map_expanded * makeup_gain
            output_batch.append(out_track)

        return ({"waveform": torch.stack(output_batch), "sample_rate": sr},)


class InternodeStemSplitter:
    """
    Splits audio using Demucs. Phase 2 Fix: Added progress logs.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "model_name": (["htdemucs", "htdemucs_ft", "hdemucs_mmi", "mdx_extra"], {"default": "htdemucs"}),
                "device": (["auto", "cuda", "cpu"],),
            }
        }

    RETURN_TYPES = ("AUDIO", "AUDIO", "AUDIO", "AUDIO")
    RETURN_NAMES = ("drums", "bass", "vocals", "other")
    FUNCTION = "split"
    CATEGORY = "Internode/AudioFX"

    def split(self, audio, model_name, device):
        if not DEMUCS_AVAILABLE:
            blank = {"waveform": torch.zeros_like(audio["waveform"]), "sample_rate": audio["sample_rate"]}
            return (blank, blank, blank, blank)

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        waveform = audio["waveform"]
        sr = audio["sample_rate"]
        
        print(f"#### Internode: Loading Demucs model '{model_name}' on {device}...")
        try:
            model = get_model(model_name)
            model.to(device)
        except Exception as e:
            print(f"#### Internode Error: Could not load Demucs model: {e}")
            return (audio, audio, audio, audio)

        batch_drums = []
        batch_bass = []
        batch_vocal = []
        batch_other = []

        # Process Batch
        for i in range(waveform.shape[0]):
            print(f"#### Internode: Demucs Splitting track {i+1}/{waveform.shape[0]}...")
            wav = waveform[i]
            
            # Normalize input
            ref = wav.mean(0)
            wav = (wav - ref.mean()) / (ref.std() + 1e-8)
            
            with torch.no_grad():
                # apply_model usually has its own progress bar if 'progress=True' is set,
                # which prints to stdout.
                sources = apply_model(model, wav.unsqueeze(0).to(device), shifts=0, split=True, overlap=0.25, progress=True)[0]

            src_map = {}
            for idx, name in enumerate(model.sources):
                src_map[name] = sources[idx].cpu()

            batch_drums.append(src_map.get("drums", torch.zeros_like(wav.cpu())))
            batch_bass.append(src_map.get("bass", torch.zeros_like(wav.cpu())))
            batch_vocal.append(src_map.get("vocals", torch.zeros_like(wav.cpu())))
            batch_other.append(src_map.get("other", torch.zeros_like(wav.cpu())))

        return (
            {"waveform": torch.stack(batch_drums), "sample_rate": sr},
            {"waveform": torch.stack(batch_bass), "sample_rate": sr},
            {"waveform": torch.stack(batch_vocal), "sample_rate": sr},
            {"waveform": torch.stack(batch_other), "sample_rate": sr},
        )