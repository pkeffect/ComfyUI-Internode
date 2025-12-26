# ComfyUI/custom_nodes/ComfyUI-Internode/analysis_nodes.py
# VERSION: 3.0.0

import torch
import numpy as np
import torchaudio

class InternodeAudioAnalyzer:
    """
    Analyzes audio using GPU-accelerated Torchaudio (Phase 2 Fix).
    Replaces Librosa.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "frame_rate": ("INT", {"default": 24, "min": 1, "max": 120}),
                "smoothness": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 0.99, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("FLOAT", "FLOAT", "FLOAT", "FLOAT") 
    RETURN_NAMES = ("bass_curve", "mid_curve", "high_curve", "vol_curve")
    FUNCTION = "analyze"
    CATEGORY = "Internode/Analysis"

    def analyze(self, audio, frame_rate, smoothness):
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]
        
        # Handle batch (take first) and stereo (mix to mono)
        if waveform.dim() == 3: waveform = waveform[0]
        # Mix to mono for analysis
        y = waveform.mean(dim=0) # [samples] Tensor

        # Calculate duration and target frames
        duration = len(y) / sample_rate
        n_frames = int(duration * frame_rate)
        if n_frames < 1: n_frames = 1
        
        # 1. Volume (RMS)
        # Use simple windowing
        hop_length = int(sample_rate / frame_rate)
        # Unfold creates sliding windows: [n_windows, window_size]
        # We handle padding to match size
        pad = hop_length - (len(y) % hop_length)
        if pad < hop_length:
            y_pad = torch.nn.functional.pad(y, (0, pad))
        else:
            y_pad = y
            
        # Reshape roughly to frames (approximation)
        # For exact frame matching with spectrogram, we calculate hop
        
        # 2. Spectrogram
        n_fft = 2048
        spec_transform = torchaudio.transforms.Spectrogram(
            n_fft=n_fft,
            hop_length=hop_length,
            power=2.0
        ).to(y.device)
        
        spectrogram = spec_transform(y) # [freq_bins, time_frames]
        
        # Spectrogram time frames might differ slightly from n_frames due to padding/centering
        # We will interpolate at the end.
        
        # Calculate Frequency Bins
        # bin = freq * n_fft / sample_rate
        def freq_to_bin(f):
            return int(f * n_fft / sample_rate)
            
        b_low = freq_to_bin(20)
        b_mid = freq_to_bin(250)
        b_high = freq_to_bin(4000)
        
        # Extract Bands energy (Sum over freq dim)
        # Handle index bounds
        max_bin = spectrogram.shape[0]
        
        bass_energy = spectrogram[b_low:min(b_mid, max_bin), :].mean(dim=0)
        mid_energy = spectrogram[b_mid:min(b_high, max_bin), :].mean(dim=0)
        high_energy = spectrogram[b_high:, :].mean(dim=0)
        
        # RMS Energy from waveform (or spectrogram sum)
        vol_energy = spectrogram.sum(dim=0)
        
        # Helper to process to list
        def process_curve(energy_tensor, target_len):
            arr = energy_tensor.cpu().numpy()
            # Resample to exact target frames (sync with video)
            arr = np.interp(
                np.linspace(0, len(arr), target_len),
                np.arange(len(arr)),
                arr
            )
            # Normalize
            m = np.max(arr)
            if m > 0: arr = arr / m
            
            # Smooth
            out = np.zeros_like(arr)
            curr = 0
            for i in range(len(arr)):
                curr = (smoothness * curr) + ((1 - smoothness) * arr[i])
                out[i] = curr
                
            return out.tolist()

        bass = process_curve(bass_energy, n_frames)
        mid = process_curve(mid_energy, n_frames)
        high = process_curve(high_energy, n_frames)
        vol = process_curve(vol_energy, n_frames)

        return (bass, mid, high, vol)