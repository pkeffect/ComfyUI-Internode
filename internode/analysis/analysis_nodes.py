# ComfyUI/custom_nodes/ComfyUI-Internode/analysis_nodes.py
# VERSION: 3.0.4

import torch
import numpy as np
import torchaudio
from PIL import Image, ImageDraw

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

class InternodeAudioToKeyframes:
    """
    Converts audio analysis into control signals for video generation.
    Outputs:
    - FLOAT: List of floats (for batch inputs)
    - STRING: Formatted schedule (0:(0.0), 1:(0.5)...) for AnimateDiff/ControlNet
    - IMAGE: Visual graph of the curve for debugging
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "fps": ("INT", {"default": 24, "min": 1, "max": 120}),
                "mode": (["RMS (Volume)", "Low (Bass/Kick)", "Mid (Vocals)", "High (Hats)", "Beat (Trigger)"],),
                "smoothing": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 0.99, "step": 0.01}),
                "amp_scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "y_offset": ("FLOAT", {"default": 0.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                "beat_threshold": ("FLOAT", {"default": 0.4, "min": 0.01, "max": 1.0, "step": 0.01, "tooltip": "Only used in Beat mode. Threshold to trigger 1.0."}),
            }
        }

    RETURN_TYPES = ("FLOAT", "STRING", "IMAGE", "INT")
    RETURN_NAMES = ("float_curve", "schedule_str", "curve_image", "frame_count")
    FUNCTION = "generate_keyframes"
    CATEGORY = "Internode/Analysis"

    def generate_keyframes(self, audio, fps, mode, smoothing, amp_scale, y_offset, beat_threshold):
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]
        
        # 1. Preprocess: Mono mix
        if waveform.dim() == 3: waveform = waveform[0]
        y = waveform.mean(dim=0)
        
        # 2. Setup FFT
        n_fft = 2048
        hop_length = int(sample_rate / fps) # Align hops with frames
        
        spec_transform = torchaudio.transforms.Spectrogram(
            n_fft=n_fft, hop_length=hop_length, power=2.0
        ).to(y.device)
        
        spectrogram = spec_transform(y) # [bins, frames]
        
        # 3. Frequency Extraction
        def freq_to_bin(f): return int(f * n_fft / sample_rate)
        max_bin = spectrogram.shape[0]
        
        raw_curve = None
        
        if mode == "RMS (Volume)":
            raw_curve = spectrogram.sum(dim=0)
        elif mode == "Low (Bass/Kick)":
            b0 = freq_to_bin(20)
            b1 = freq_to_bin(250)
            raw_curve = spectrogram[b0:min(b1, max_bin), :].mean(dim=0)
        elif mode == "Mid (Vocals)":
            b0 = freq_to_bin(250)
            b1 = freq_to_bin(4000)
            raw_curve = spectrogram[b0:min(b1, max_bin), :].mean(dim=0)
        elif mode == "High (Hats)":
            b0 = freq_to_bin(4000)
            raw_curve = spectrogram[b0:, :].mean(dim=0)
        elif mode == "Beat (Trigger)":
            # For beat detection, we use Low band + transient detection
            b0 = freq_to_bin(20)
            b1 = freq_to_bin(200)
            raw_curve = spectrogram[b0:min(b1, max_bin), :].mean(dim=0)
        
        # 4. Processing to Numpy
        arr = raw_curve.cpu().numpy()
        
        # Normalize (0.0 - 1.0)
        mx = np.max(arr)
        if mx > 1e-6:
            arr = arr / mx
        
        # 5. Beat Detection Logic (Binary Gate)
        if mode == "Beat (Trigger)":
            # Simple thresholding
            beat_curve = np.zeros_like(arr)
            # Find local peaks above threshold
            # Simple approach: if val > thresh and val > prev_val
            for i in range(1, len(arr) - 1):
                if arr[i] > beat_threshold and arr[i] > arr[i-1] and arr[i] > arr[i+1]:
                    beat_curve[i] = 1.0 # Trigger
                else:
                    # Decay or Zero? Request says "1.0 otherwise 0.0"
                    beat_curve[i] = 0.0
            arr = beat_curve
        else:
            # 6. Smoothing (EMA)
            if smoothing > 0:
                smoothed = np.zeros_like(arr)
                curr = 0
                for i in range(len(arr)):
                    curr = (smoothing * curr) + ((1 - smoothing) * arr[i])
                    smoothed[i] = curr
                arr = smoothed
        
        # 7. Scaling and Offset
        arr = (arr * amp_scale) + y_offset
        
        # 8. Align Frame Count exactly to Duration * FPS
        duration = len(y) / sample_rate
        target_frames = int(duration * fps)
        
        # Resample array to exact frame count
        if len(arr) != target_frames:
            arr = np.interp(
                np.linspace(0, len(arr), target_frames),
                np.arange(len(arr)),
                arr
            )
            
        # 9. Format Outputs
        
        # A. Schedule String: "0:(0.5), 1:(0.6)..."
        sched_items = []
        for i, val in enumerate(arr):
            sched_items.append(f"{i}:({val:.3f})")
        sched_str = ",\n".join(sched_items)
        
        # B. Curve Image (Visualization)
        img_w, img_h = 1024, 256
        vis_img = Image.new("RGB", (img_w, img_h), (20, 20, 20))
        draw = ImageDraw.Draw(vis_img)
        
        # Draw grid
        draw.line([(0, img_h/2), (img_w, img_h/2)], fill=(50, 50, 50))
        
        # Normalize for drawing (-1 to 2 range approx visualization)
        # We assume typical range 0-1, but scale/offset can shift it
        # Map Y: (val) -> pixels
        # Let's map visual range 0.0 at bottom, 1.0 at top, allowing overflow
        def val_to_y(v):
            norm = v # 0..1
            y_px = img_h - (norm * img_h)
            return np.clip(y_px, 0, img_h)
            
        points = []
        for i in range(len(arr)):
            x = (i / len(arr)) * img_w
            y = val_to_y(arr[i])
            points.append((x, y))
            
        if len(points) > 1:
            draw.line(points, fill=(0, 255, 200), width=2)
            
        # To Tensor [1, H, W, 3]
        vis_tensor = torch.from_numpy(np.array(vis_img).astype(np.float32) / 255.0).unsqueeze(0)
        
        # C. Float output (Batch)
        # ComfyUI nodes expecting a batch of floats usually handle a list
        float_out = [float(x) for x in arr]
        
        return (float_out, sched_str, vis_tensor, target_frames)

class InternodeSpectrogram:
    """
    Converts audio waveform to a spectrogram image suitable for Stable Diffusion Inpainting.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "n_fft": ("INT", {"default": 1024, "min": 64, "max": 4096}),
                "hop_length": ("INT", {"default": 256, "min": 32, "max": 2048}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "to_spectrogram"
    CATEGORY = "Internode/Spectral"

    def to_spectrogram(self, audio, n_fft, hop_length):
        waveform = audio["waveform"]
        if waveform.dim() == 3: waveform = waveform[0] # Take batch 0
        waveform = waveform.mean(dim=0) # Mono

        spectrogram_transform = torchaudio.transforms.Spectrogram(
            n_fft=n_fft,
            hop_length=hop_length,
            power=1.0 # Magnitude
        ).to(waveform.device)

        spec = spectrogram_transform(waveform)
        
        # Log magnitude (standard for visual representation)
        spec = torch.log1p(spec)

        # Normalize 0-1
        max_val = spec.max()
        if max_val > 0:
            spec = spec / max_val
            
        # Spec is [Freq, Time]
        # Image expects [Batch, Height, Width, Channels]
        # We flip Y axis so Low Frequencies are at the bottom (Standard view)
        spec = torch.flip(spec, [0])

        img = spec.unsqueeze(0).unsqueeze(-1) # [1, H, W, 1]
        # Expand to 3 channels for compatibility with Standard SD VAE
        img = img.repeat(1, 1, 1, 3) 
        
        return (img,)

class InternodeImageToAudio:
    """
    Converts a spectrogram image back to audio using Griffin-Lim phase reconstruction.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "sample_rate": ("INT", {"default": 44100, "min": 8000, "max": 96000}),
                "n_iter": ("INT", {"default": 32, "min": 1, "max": 256}),
                "hop_length": ("INT", {"default": 256, "min": 32, "max": 2048}),
                "amp_scale": ("FLOAT", {"default": 100.0, "min": 1.0, "max": 1000.0, "tooltip": "Boosts volume to recover range lost during 0-1 normalization."}),
            }
        }
    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "from_spectrogram"
    CATEGORY = "Internode/Spectral"

    def from_spectrogram(self, image, sample_rate, n_iter, hop_length, amp_scale):
        # Image: [Batch, H, W, C]
        # Take batch 0, channel 0 (Greyscale info)
        img = image[0, :, :, 0] # [H, W]
        
        # Unflip (Low freq was at bottom)
        img = torch.flip(img, [0])
        
        # Denormalize (Log -> Linear)
        # We apply amp_scale here to recover dynamic range before exponentiation
        # Formula inverse of: log1p(x / max)
        spec = torch.expm1(img * np.log1p(amp_scale)) 
        
        # Determine n_fft from image height
        # Spectrogram Height = n_fft // 2 + 1
        # Therefore: n_fft = (Height - 1) * 2
        height = img.shape[0]
        n_fft = (height - 1) * 2

        griffin_lim = torchaudio.transforms.GriffinLim(
            n_fft=n_fft,
            hop_length=hop_length,
            n_iter=n_iter,
            power=1.0
        ).to(img.device)

        waveform = griffin_lim(spec)
        
        # Reshape for Comfy Audio format [1, Channels, Samples]
        waveform = waveform.unsqueeze(0).unsqueeze(0)
        
        return ({"waveform": waveform, "sample_rate": sample_rate},)