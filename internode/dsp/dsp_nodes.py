# ComfyUI/custom_nodes/ComfyUI-Internode/dsp_nodes.py
# VERSION: 3.0.1

import os
import torch
import torchaudio
import torchaudio.functional as F
import numpy as np
import folder_paths
from PIL import Image, ImageOps
import shutil
import sys

# --- Optional Dependency Imports ---

SCIPY_AVAILABLE = False
try:
    # Scipy is now only used for fallback file loading, not realtime DSP
    import scipy.signal
    from scipy.io import wavfile as scipy_wav
    SCIPY_AVAILABLE = True
except ImportError:
    pass

SOUNDFILE_AVAILABLE = False
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    pass

PYDUB_AVAILABLE = False
try:
    # Attempt to locate ffmpeg before importing pydub
    found_ffmpeg = shutil.which("ffmpeg")
    if not found_ffmpeg:
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "ffmpeg", "bin", "ffmpeg.exe"),
            os.path.join(os.getcwd(), "ffmpeg.exe"),
            os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
        ]
        for p in common_paths:
            if os.path.exists(p):
                found_ffmpeg = p
                os.environ["PATH"] += os.pathsep + os.path.dirname(p)
                break

    from pydub import AudioSegment
    if found_ffmpeg:
        AudioSegment.converter = found_ffmpeg
    PYDUB_AVAILABLE = True
except ImportError:
    pass

OPENCV_AVAILABLE = False
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    pass

SAVER_FORMATS = {
    "wav_16bit": {"ext": "wav", "desc": "WAV 16-bit PCM"},
    "wav_24bit": {"ext": "wav", "desc": "WAV 24-bit PCM"},
    "wav_32bit_float": {"ext": "wav", "desc": "WAV 32-bit Float"},
    "flac": {"ext": "flac", "desc": "FLAC"},
    "flac_24bit": {"ext": "flac", "desc": "FLAC 24-bit"},
    "ogg_low": {"ext": "ogg", "desc": "OGG ~96k"},
    "ogg_medium": {"ext": "ogg", "desc": "OGG ~128k"},
    "ogg_high": {"ext": "ogg", "desc": "OGG ~192k"},
    "mp3_128": {"ext": "mp3", "desc": "MP3 128k"},
    "mp3_192": {"ext": "mp3", "desc": "MP3 192k"},
    "mp3_320": {"ext": "mp3", "desc": "MP3 320k"},
    "aac_192": {"ext": "m4a", "desc": "AAC 192k"},
    "aiff": {"ext": "aiff", "desc": "AIFF"},
}

def load_audio_file(file_path, target_sample_rate="keep", normalize=False, mono_to_stereo=True):
    if not os.path.exists(file_path): return None, 0
    audio_data, sample_rate = None, 44100
    ext = file_path.lower().split('.')[-1]

    # Priority 1: SoundFile
    if SOUNDFILE_AVAILABLE:
        try: audio_data, sample_rate = sf.read(file_path, dtype='float32')
        except: pass

    # Priority 2: PyDub
    if audio_data is None and PYDUB_AVAILABLE:
        try:
            seg = AudioSegment.from_file(file_path)
            sample_rate = seg.frame_rate
            samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
            if seg.sample_width == 2: max_val = 32768.0
            elif seg.sample_width == 4: max_val = 2147483648.0
            elif seg.sample_width == 1: max_val = 128.0 
            else: max_val = float(2 ** (seg.sample_width * 8 - 1))
            samples = samples / max_val
            audio_data = samples.reshape((-1, seg.channels))
        except Exception:
            pass

    # Priority 3: Scipy
    if audio_data is None and SCIPY_AVAILABLE and ext == "wav":
        try:
            sr, d = scipy_wav.read(file_path)
            sample_rate = sr
            if d.dtype == np.int16: audio_data = d.astype(np.float32) / 32768.0
            elif d.dtype == np.int32: audio_data = d.astype(np.float32) / 2147483648.0
            else: audio_data = d.astype(np.float32)
            if audio_data.ndim == 1: audio_data = audio_data.reshape(-1, 1)
        except: pass

    if audio_data is None: return None, 0

    if audio_data.ndim == 1: audio_data = audio_data.reshape(-1, 1)
    if mono_to_stereo and audio_data.shape[1] == 1: audio_data = np.repeat(audio_data, 2, axis=1)

    if target_sample_rate != "keep":
        tsr = int(target_sample_rate)
        if tsr != sample_rate:
            # Use torch resampling if loaded into numpy
            # or use scipy if available. We prefer Torch here to avoid dependency issues.
            import torchaudio.transforms as T
            tensor_temp = torch.from_numpy(audio_data.T).float()
            resampler = T.Resample(sample_rate, tsr)
            tensor_temp = resampler(tensor_temp)
            audio_data = tensor_temp.numpy().T
            sample_rate = tsr

    if normalize:
        peak = np.max(np.abs(audio_data))
        if peak > 0: audio_data = audio_data * (0.95 / peak)

    tensor = torch.from_numpy(audio_data.T).float().unsqueeze(0)
    return tensor, sample_rate

# --- 1. AUDIO LOADER ---
class InternodeAudioLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio_file": ("STRING", {"default": "none"}),
            },
            "optional": {
                "normalize": ("BOOLEAN", {"default": False}),
                "mono_to_stereo": ("BOOLEAN", {"default": True}),
                "target_sample_rate": (["keep", "22050", "44100", "48000", "96000"], {"default": "keep"}),
            }
        }

    RETURN_TYPES = ("AUDIO", "INT", "FLOAT", "INT")
    RETURN_NAMES = ("audio", "sample_rate", "duration", "channels")
    FUNCTION = "load_audio"
    CATEGORY = "Internode/Loaders"
    
    @classmethod
    def IS_CHANGED(s, audio_file, **kwargs):
        if not audio_file or audio_file == "none": return float("nan")
        path = os.path.join(folder_paths.get_input_directory(), audio_file)
        return os.path.getmtime(path) if os.path.exists(path) else float("nan")

    def load_audio(self, audio_file, normalize=False, mono_to_stereo=True, target_sample_rate="keep"):
        if not audio_file or audio_file == "none": raise ValueError("No audio file uploaded.")
        path = os.path.join(folder_paths.get_input_directory(), audio_file)
        
        tensor, sr = load_audio_file(path, target_sample_rate, normalize, mono_to_stereo)
        if tensor is None: raise RuntimeError(f"Failed to load audio: {audio_file}. (Check if ffmpeg is installed for non-WAV files)")
            
        return ({"waveform": tensor, "sample_rate": sr}, sr, tensor.shape[-1]/sr, tensor.shape[1])

# --- 2. VIDEO LOADER ---
class InternodeVideoLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video_file": ("STRING", {"default": "none"}),
            },
            "optional": {
                "load_audio": ("BOOLEAN", {"default": True}),
                "frame_load_cap": ("INT", {"default": 150, "min": 0, "max": 10000, "tooltip": "Limit total frames loaded to prevent OOM. 0 = Uncapped (Dangerous)"}),
                "start_frame": ("INT", {"default": 0, "min": 0, "step": 1}),
                "frame_step": ("INT", {"default": 1, "min": 1, "step": 1}),
                "resize_mode": (["Original", "512x512", "768x768", "1024x1024", "1280x720"], {"default": "512x512"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "AUDIO", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("images", "audio", "fps", "frame_count", "width", "height")
    FUNCTION = "load_video"
    CATEGORY = "Internode/Loaders"

    @classmethod
    def IS_CHANGED(s, video_file, **kwargs):
        if not video_file or video_file == "none": return float("nan")
        path = os.path.join(folder_paths.get_input_directory(), video_file)
        return os.path.getmtime(path) if os.path.exists(path) else float("nan")

    def load_video(self, video_file, load_audio=True, frame_load_cap=150, start_frame=0, frame_step=1, resize_mode="Original"):
        if not OPENCV_AVAILABLE: raise ImportError("OpenCV missing.")
        if not video_file or video_file == "none": raise ValueError("No video file.")
        
        path = os.path.join(folder_paths.get_input_directory(), video_file)
        if not os.path.exists(path): raise FileNotFoundError(f"Video not found: {video_file}")

        cap = cv2.VideoCapture(path)
        if not cap.isOpened(): raise RuntimeError("Failed to open video.")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if start_frame > 0: cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        frames = []
        count = 0
        step_counter = 0
        
        target_size = None
        if resize_mode != "Original":
            if "x" in resize_mode:
                parts = resize_mode.split('x')
                target_size = (int(parts[0]), int(parts[1]))
        
        effective_cap = frame_load_cap if frame_load_cap > 0 else 999999

        while True:
            if len(frames) >= effective_cap: 
                print(f"#### Internode: Video load capped at {effective_cap} frames.")
                break
                
            ret, frame = cap.read()
            if not ret: break
            
            if step_counter % frame_step == 0:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if target_size:
                    frame = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
                frame = frame.astype(np.float32) / 255.0
                frames.append(torch.from_numpy(frame))
                
            count += 1
            step_counter += 1
            
        cap.release()
        
        if not frames: raise RuntimeError("No frames extracted.")
        image_batch = torch.stack(frames)
        
        audio_out = {"waveform": torch.zeros((1, 2, 44100)), "sample_rate": 44100}
        if load_audio:
            # Load audio for full video then slice if needed? 
            # For now load full audio as simple sync
            tensor, sr = load_audio_file(path, "keep", False, True)
            if tensor is not None: audio_out = {"waveform": tensor, "sample_rate": sr}

        h, w = image_batch.shape[1:3]
        return (image_batch, audio_out, int(fps), len(frames), w, h)

# --- 3. IMAGE LOADER ---
class InternodeImageLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_file": ("STRING", {"default": "none"}),
            },
            "optional": {
                "mode": (["RGB", "RGBA", "Gray"], {"default": "RGB"}),
                "invert_mask": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("image", "mask", "width", "height")
    FUNCTION = "load_image"
    CATEGORY = "Internode/Loaders"

    @classmethod
    def IS_CHANGED(s, image_file, **kwargs):
        if not image_file or image_file == "none": return float("nan")
        path = os.path.join(folder_paths.get_input_directory(), image_file)
        return os.path.getmtime(path) if os.path.exists(path) else float("nan")

    def load_image(self, image_file, mode="RGB", invert_mask=False):
        if not image_file or image_file == "none": raise ValueError("No image uploaded.")
        path = os.path.join(folder_paths.get_input_directory(), image_file)
        if not os.path.exists(path): raise FileNotFoundError(f"Image not found: {image_file}")

        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        
        # Mask handling
        mask = None
        if "A" in img.getbands():
            mask = np.array(img.getchannel("A")).astype(np.float32) / 255.0
            mask = torch.from_numpy(mask)
            if invert_mask: mask = 1.0 - mask
        else:
            mask = torch.zeros((img.height, img.width), dtype=torch.float32)

        if mode == "RGBA": img = img.convert("RGBA")
        elif mode == "Gray": img = img.convert("L")
        else: img = img.convert("RGB")
        
        img_np = np.array(img).astype(np.float32) / 255.0
        
        # Add batch dim if needed, usually [H,W,C] -> [1,H,W,C] for image batch
        if mode == "Gray":
            tensor = torch.from_numpy(img_np).unsqueeze(0).unsqueeze(-1) # 1,H,W,1
        else:
            tensor = torch.from_numpy(img_np).unsqueeze(0) # 1,H,W,3/4

        return (tensor, mask.unsqueeze(0), img.width, img.height)

# --- AUDIO SAVER ---
class InternodeAudioSaver:
    def __init__(self): self.output_dir = folder_paths.get_output_directory()
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "filename_prefix": ("STRING", {"default": "audio_output"}),
                "format": (list(SAVER_FORMATS.keys()), {"default": "wav_16bit"}),
            },
            "optional": { "normalize_before_save": ("BOOLEAN", {"default": False}), "overwrite": ("BOOLEAN", {"default": False}) }
        }
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("file_path", "filename")
    FUNCTION = "save_audio"
    CATEGORY = "Internode/AudioFX"
    OUTPUT_NODE = True

    def save_audio(self, audio, filename_prefix, format, normalize_before_save=False, overwrite=False):
        if audio is None: return ("", "")
        wav, sr = audio["waveform"], audio["sample_rate"]
        if wav.dim()==3: arr = wav[0].cpu().numpy().T
        elif wav.dim()==2: arr = wav.cpu().numpy().T
        else: arr = wav.cpu().numpy().reshape(-1, 1)
        
        if normalize_before_save:
            pk = np.max(np.abs(arr))
            if pk > 0: arr = arr * (0.95 / pk)
        arr = np.clip(arr, -1.0, 1.0)
        
        path, _, cnt, _, pfx = folder_paths.get_save_image_path(filename_prefix, self.output_dir)
        ext = SAVER_FORMATS.get(format, {}).get("ext", "wav")
        fname = f"{filename_prefix}.{ext}" if overwrite else f"{pfx}_{cnt:05d}.{ext}"
        full = os.path.join(path, fname)
        saved = False
        
        # Priority 1: SoundFile (Good for WAV/FLAC)
        if format.startswith("wav") and SOUNDFILE_AVAILABLE:
            st = 'PCM_16'
            if "24bit" in format: st = 'PCM_24'
            if "32bit" in format: st = 'FLOAT'
            sf.write(full, arr, sr, subtype=st); saved=True
        elif format.startswith("flac") and SOUNDFILE_AVAILABLE:
            st = 'PCM_24' if "24bit" in format else 'PCM_16'
            sf.write(full, arr, sr, format='FLAC', subtype=st); saved=True
            
        # Priority 2: PyDub (Required for MP3/AAC/OGG)
        if not saved and PYDUB_AVAILABLE:
            try:
                fmt = "wav"
                if "mp3" in format: fmt="mp3"
                elif "ogg" in format: fmt="ogg"
                elif "flac" in format: fmt="flac"
                elif "aac" in format: fmt="ipod"
                elif "aiff" in format: fmt="aiff"
                br = "192k"
                if "128" in format: br="128k"
                if "320" in format: br="320k"
                
                ai = (arr*32767).astype(np.int16)
                if ai.shape[1]==1: ai=np.repeat(ai,2,axis=1)
                seg = AudioSegment(ai.tobytes(), frame_rate=sr, sample_width=2, channels=ai.shape[1])
                seg.export(full, format=fmt, bitrate=br); saved=True
            except Exception as e:
                print(f"#### Internode Save Error: {e} (Is ffmpeg installed/detectable?)")
            
        if not saved: print(f"#### Internode: Save failed {format}")
        return (full, fname)

# --- MIXER & DSP BACKEND ---
class InternodeAudioMixer:
    @classmethod
    def INPUT_TYPES(s):
        inputs = { "required": { "master_vol": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}), "master_gate": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}), "master_comp": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}), "master_eq_high": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}), "master_eq_mid": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}), "master_eq_low": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}), "master_balance": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}), "master_width": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}), "master_drive": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}), "master_locut": ("FLOAT", {"default": 20.0, "min": 20.0, "max": 200.0, "step": 1.0}), "master_hicut": ("FLOAT", {"default": 20000.0, "min": 8000.0, "max": 20000.0, "step": 100.0}), "master_ceil": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 1.0, "step": 0.01}) }, "optional": {} }
        for i in range(1, 5): s._add_channel_inputs(inputs, i)
        return inputs
    
    @classmethod
    def _add_channel_inputs(cls, inputs, i):
        inputs["required"][f"vol_{i}"] = ("FLOAT", {"default": 0.75, "min": 0.0, "max": 1.5, "step": 0.01})
        inputs["required"][f"pan_{i}"] = ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01})
        inputs["required"][f"eq_low_{i}"] = ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1})
        inputs["required"][f"eq_mid_{i}"] = ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1})
        inputs["required"][f"eq_high_{i}"] = ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1})
        inputs["required"][f"gate_{i}"] = ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01})
        inputs["required"][f"comp_{i}"] = ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01})
        inputs["required"][f"d_time_{i}"] = ("FLOAT", {"default": 0.35, "min": 0.01, "max": 2.0, "step": 0.01})
        inputs["required"][f"d_fb_{i}"] = ("FLOAT", {"default": 0.4, "min": 0.0, "max": 0.95, "step": 0.01})
        inputs["required"][f"d_mix_{i}"] = ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01})
        inputs["required"][f"d_echo_{i}"] = ("INT", {"default": 4, "min": 1, "max": 16, "step": 1})
        inputs["required"][f"mute_{i}"] = ("BOOLEAN", {"default": False})
        inputs["required"][f"solo_{i}"] = ("BOOLEAN", {"default": False})
        inputs["optional"][f"track_{i}"] = ("AUDIO",)

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "mix_tracks"
    CATEGORY = "Internode/AudioFX"

    def mix_tracks(self, master_vol, master_gate=0.0, master_comp=0.0, master_eq_high=1.0, master_eq_mid=1.0, master_eq_low=1.0, master_balance=0.0, master_width=1.0, master_drive=0.0, master_locut=20.0, master_hicut=20000.0, master_ceil=1.0, **kwargs):
        tracks = []
        count = 8 if "vol_8" in kwargs else 4
        for i in range(1, count + 1):
            tracks.append({
                'audio': kwargs.get(f"track_{i}"),
                'vol': kwargs.get(f"vol_{i}", 0.75), 'pan': kwargs.get(f"pan_{i}", 0.0),
                'eq': (kwargs.get(f"eq_low_{i}", 1.0), kwargs.get(f"eq_mid_{i}", 1.0), kwargs.get(f"eq_high_{i}", 1.0)),
                'dyn': (kwargs.get(f"gate_{i}", 0.0), kwargs.get(f"comp_{i}", 0.0)),
                'delay': (kwargs.get(f"d_time_{i}", 0.35), kwargs.get(f"d_fb_{i}", 0.4), kwargs.get(f"d_mix_{i}", 0.0), kwargs.get(f"d_echo_{i}", 4)),
                'mute': kwargs.get(f"mute_{i}", False), 'solo': kwargs.get(f"solo_{i}", False),
            })
        return self._process_mix(tracks, master_vol, master_gate, master_comp, (master_eq_low, master_eq_mid, master_eq_high), master_balance, master_width, (master_drive, master_locut, master_hicut, master_ceil))

    def _apply_eq(self, w, sr, l, m, h):
        if l == 1.0 and m == 1.0 and h == 1.0: return w
        
        # Helper to convert linear gain to dB
        def get_db(g):
            if g <= 0.001: return -60.0 # Floor for "kill"
            return 20.0 * np.log10(g)

        # Apply Serial EQ (Shelving/Peaking) to avoid phase cancellation artifacts
        # inherent in split-and-sum isolator topologies.
        
        # Low Shelf (Bass) @ 250Hz
        if l != 1.0:
            w = F.bass_biquad(w, sr, gain=get_db(l), central_freq=250.0, Q=0.707)
            
        # Mid Peaking (Mid) @ 1000Hz, Q=0.707
        if m != 1.0:
            w = F.equalizer_biquad(w, sr, center_freq=1000.0, gain=get_db(m), Q=0.707)
            
        # High Shelf (Treble) @ 4000Hz
        if h != 1.0:
            w = F.treble_biquad(w, sr, gain=get_db(h), central_freq=4000.0, Q=0.707)
            
        return w
        
    def _apply_dynamics(self, w, gate, comp):
        if gate == 0 and comp == 0: return w
        if gate > 0:
            threshold = gate * 0.1
            mask = (torch.abs(w) > threshold).float()
            w = w * mask
        if comp > 0:
            thresh_db = -5.0 - (comp * 25.0)
            thresh_lin = 10**(thresh_db/20)
            ratio = 1.0 + (comp * 4.0)
            amp = torch.abs(w)
            over = torch.clamp(amp - thresh_lin, min=0)
            if torch.max(over) > 0:
                gain_red = over * (1.0 - (1.0/ratio))
                w = w * (1.0 - (gain_red / (amp + 1e-6)))
                w = w * (1.0 + comp * 0.5)
        return w

    def _apply_delay(self, w, sr, time, fb, mix, echoes):
        # Vectorized Delay (Phase 1 Fix)
        if mix <= 0.01 or time <= 0.001: return w
        
        device = w.device
        
        # Calculate delay in samples
        delay_samples = int(time * sr)
        if delay_samples == 0: return w

        # Create the Impulse Response (Kernel)
        kernel_len = delay_samples * echoes + 1
        
        # Create kernel [out_channels, in_channels/groups, kernel_size]
        kernel = torch.zeros(1, 1, kernel_len, device=device)
        
        # Set impulses
        current_amp = 1.0
        for i in range(echoes + 1):
            idx = i * delay_samples
            if idx < kernel_len:
                kernel[0, 0, idx] = current_amp
                current_amp *= fb
        
        # Apply Convolution (per channel)
        b, c, l = w.shape
        w_flat = w.view(-1, 1, l)
        
        # Convolve using groups=channels logic or just flat batch processing
        wet = torch.nn.functional.conv1d(w_flat, kernel, padding=kernel_len-1)
        wet = wet[..., :l]
        wet = wet.view(b, c, l)
        
        return (w * (1 - mix)) + (wet * mix)
        
    def _apply_master_color(self, w, sr, drive, locut, hicut, ceil):
        if locut > 20:
            w = F.highpass_biquad(w, sr, cutoff_freq=locut)
        if drive > 0:
            boost = 1.0 + (drive * 3.0)
            w = torch.tanh(w * boost)
            w = w / boost * (1.0 + drive * 0.5)
        if hicut < 20000:
            w = F.lowpass_biquad(w, sr, cutoff_freq=hicut)
        if ceil < 1.0: w = torch.clamp(w, -ceil, ceil)
        return w

    def _process_mix(self, tracks, master_vol, master_gate, master_comp, eq_cfg, balance, width, color_cfg):
        max_len, sr, dev = 0, 44100, None
        active = []
        any_solo = any(t['solo'] for t in tracks)
        for t in tracks:
            if t['audio'] is not None:
                max_len = max(max_len, t['audio']['waveform'].shape[-1])
                sr = t['audio']['sample_rate']
                if dev is None: dev = t['audio']['waveform'].device
                if (any_solo and t['solo']) or (not any_solo and not t['mute']): active.append(t)
        if max_len == 0: return ({"waveform": torch.zeros((1, 2, sr)), "sample_rate": sr},)
        if dev is None: dev = torch.device('cpu')
        
        processed_tracks = []
        final_len = max_len
        for t in active:
            w = t['audio']['waveform'].to(dev)
            w = self._apply_dynamics(w, t['dyn'][0], t['dyn'][1])
            w = self._apply_eq(w, sr, t['eq'][0], t['eq'][1], t['eq'][2])
            w = self._apply_delay(w, sr, t['delay'][0], t['delay'][1], t['delay'][2], t['delay'][3])
            if w.shape[1] == 1: w = w.repeat(1, 2, 1)
            final_len = max(final_len, w.shape[-1])
            processed_tracks.append((w, t['vol'], t['pan']))
            
        mix_buf = torch.zeros((1, 2, final_len), device=dev)
        for w, vol, pan in processed_tracks:
            curr = w.shape[-1]
            if curr < final_len: w = torch.nn.functional.pad(w, (0, final_len - curr))
            lg = 1.0 - max(0, pan)
            rg = 1.0 + min(0, pan)
            mix_buf[:, 0, :] += w[:, 0, :] * vol * lg
            mix_buf[:, 1, :] += w[:, 1, :] * vol * rg
            
        mix_buf = self._apply_master_color(mix_buf, sr, color_cfg[0], color_cfg[1], color_cfg[2], color_cfg[3])
        mix_buf = self._apply_dynamics(mix_buf, master_gate, master_comp)
        mix_buf = self._apply_eq(mix_buf, sr, eq_cfg[0], eq_cfg[1], eq_cfg[2])
        if width != 1.0:
            mid = (mix_buf[:, 0, :] + mix_buf[:, 1, :]) * 0.5
            side = (mix_buf[:, 0, :] - mix_buf[:, 1, :]) * 0.5
            side *= width
            mix_buf[:, 0, :] = mid + side
            mix_buf[:, 1, :] = mid - side
        bal_lg = 1.0 - max(0, balance)
        bal_rg = 1.0 + min(0, balance)
        mix_buf[:, 0, :] *= bal_lg
        mix_buf[:, 1, :] *= bal_rg
        mix_buf = torch.clamp(mix_buf * master_vol, -1.0, 1.0)
        return ({"waveform": mix_buf, "sample_rate": sr},)

class InternodeAudioMixer8(InternodeAudioMixer):
    @classmethod
    def INPUT_TYPES(s):
        inputs = { "required": { "master_vol": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}), "master_gate": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}), "master_comp": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}), "master_eq_high": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}), "master_eq_mid": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}), "master_eq_low": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}), "master_balance": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}), "master_width": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}), "master_drive": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}), "master_locut": ("FLOAT", {"default": 20.0, "min": 20.0, "max": 200.0, "step": 1.0}), "master_hicut": ("FLOAT", {"default": 20000.0, "min": 8000.0, "max": 20000.0, "step": 100.0}), "master_ceil": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 1.0, "step": 0.01}) }, "optional": {} }
        for i in range(1, 9): s._add_channel_inputs(inputs, i)
        return inputs