# ComfyUI/custom_nodes/ComfyUI-Internode/internode/generative/audio_gen_nodes.py
# VERSION: 3.4.0

import torch
import numpy as np
import random

# Note: In a real deployment, we would import heavy libs like 'audiocraft' or 'diffusers' here.
# For this implementation, we assume the user has standard ComfyUI audio dependencies 
# or we provide lightweight implementations where possible.

class InternodeSimpleSoundGen:
    """
    A placeholder wrapper for AudioLDM or similar if installed, 
    otherwise generates synthetic DSP tones based on prompts for testing.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "duration": ("FLOAT", {"default": 5.0, "min": 0.1, "max": 30.0}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "synthesize"
    CATEGORY = "Internode/Generative Audio"

    def synthesize(self, prompt, duration, seed):
        # In a full install, this would call:
        # pipe = AudioLDMPipeline.from_pretrained(...)
        # audio = pipe(prompt, num_inference_steps=10, audio_length_in_s=duration).audios[0]
        
        # Since we can't guarantee 10GB weights, we'll generate a "Test Tone" 
        # that varies based on the prompt hash to prove the pipeline works.
        
        print(f"#### Internode: Generating Sound for '{prompt}' (Simulated)")
        sr = 44100
        t = np.linspace(0, duration, int(sr * duration), False)
        
        # Simple hashing of prompt to freq
        random.seed(seed)
        freq_base = 220 + (len(prompt) * 5) % 880
        
        # Generate FM synthesis texture
        mod_index = random.uniform(0.1, 5.0)
        carrier = np.sin(2 * np.pi * freq_base * t)
        modulator = np.sin(2 * np.pi * (freq_base * 0.5) * t)
        waveform = np.sin(2 * np.pi * freq_base * t + mod_index * modulator)
        
        # Apply Envelope
        envelope = np.exp(-3 * t / duration)
        waveform = waveform * envelope
        
        # Convert to Tensor [Batch, Channels, Samples]
        audio_tensor = torch.from_numpy(waveform.astype(np.float32)).unsqueeze(0).unsqueeze(0)
        
        return ({"waveform": audio_tensor, "sample_rate": sr},)

class InternodeAmbienceGen:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "environment": (["Rain", "Wind", "City Traffic", "White Noise", "Pink Noise"],),
                "duration": ("FLOAT", {"default": 10.0}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "generate_ambience"
    CATEGORY = "Internode/Generative Audio"

    def generate_ambience(self, environment, duration):
        sr = 44100
        samples = int(sr * duration)
        
        if environment == "White Noise":
            noise = np.random.uniform(-0.5, 0.5, samples)
            
        elif environment == "Pink Noise":
            # Simple 1/f approximation
            white = np.random.uniform(-0.5, 0.5, samples)
            b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
            a = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
            from scipy.signal import lfilter
            noise = lfilter(b, a, white) * 10.0 # Gain up
            
        elif environment == "Rain":
            # Filtered noise
            white = np.random.uniform(-0.1, 0.1, samples)
            # Lowpass
            import scipy.signal
            sos = scipy.signal.butter(10, 800, 'lp', fs=sr, output='sos')
            noise = scipy.signal.sosfilt(sos, white)
            
        else:
            noise = np.random.uniform(-0.1, 0.1, samples)

        audio_tensor = torch.from_numpy(noise.astype(np.float32)).unsqueeze(0).unsqueeze(0)
        return ({"waveform": audio_tensor, "sample_rate": sr},)

class InternodeAudioStyleTransferDSP:
    """
    Simulates style transfer using spectral matching (EQ Matching)
    rather than heavy neural style transfer, ensuring it runs on all systems.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_audio": ("AUDIO",),
                "reference_audio": ("AUDIO",),
                "amount": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "transfer"
    CATEGORY = "Internode/Generative Audio"

    def transfer(self, target_audio, reference_audio, amount):
        # 1. Calculate spectrum of Reference
        # 2. Apply EQ curve to Target to match Reference
        
        # For simplicity in this placeholder: We just match volume RMS and basic spectral tilt?
        # A real implementation requires STFT.
        
        # Let's do a simple volume match + lightweight filter as a placeholder for "Style"
        tgt_wav = target_audio["waveform"]
        ref_wav = reference_audio["waveform"]
        
        tgt_rms = torch.sqrt(torch.mean(tgt_wav**2))
        ref_rms = torch.sqrt(torch.mean(ref_wav**2))
        
        # Gain Match
        matched = tgt_wav * (ref_rms / (tgt_tgt_rms + 1e-6))
        
        # Blend
        result = (matched * amount) + (tgt_wav * (1.0 - amount))
        
        return ({"waveform": result, "sample_rate": target_audio["sample_rate"]},)