# ComfyUI/custom_nodes/ComfyUI-Internode/internode/utils/asset_browser.py
# VERSION: 3.1.0

import torch
import numpy as np
import os
import folder_paths
from PIL import Image, ImageOps
import cv2

# Helper to load audio (reused from dsp_nodes logic roughly)
# We won't import the full heavy DSP chain here to keep utils light, 
# but we need basic audio loading if video is selected.
try:
    import soundfile as sf
except ImportError:
    sf = None

class InternodeAssetBrowser:
    """
    A visual file explorer for your 'input' directory.
    - Frontend: Displays thumbnails grid.
    - Backend: Smart loads Image or Video based on selection.
    """
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        # We perform a basic sort, but the JS will handle the heavy lifting/filtering
        files.sort()
        
        return {
            "required": {
                "filename": (sorted(files), {"default": "none"}),
            },
            "optional": {
                # Video specific controls
                "frame_load_cap": ("INT", {"default": 150, "min": 0, "max": 10000}),
                "start_frame": ("INT", {"default": 0, "min": 0}),
                "resize_mode": (["Original", "512x512", "768x768", "1024x1024"],),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "AUDIO", "STRING")
    RETURN_NAMES = ("media", "mask", "audio", "filename")
    FUNCTION = "load_media"
    CATEGORY = "Internode/Utils"

    @classmethod
    def IS_CHANGED(s, filename, **kwargs):
        path = folder_paths.get_annotated_filepath(filename)
        return os.path.getmtime(path) if os.path.exists(path) else float("nan")

    def load_media(self, filename, frame_load_cap=150, start_frame=0, resize_mode="Original"):
        path = folder_paths.get_annotated_filepath(filename)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {filename}")

        # Check Extension
        ext = os.path.splitext(filename)[1].lower()
        VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.gif'}
        
        # --- VIDEO LOADER LOGIC ---
        if ext in VIDEO_EXTS:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened(): raise RuntimeError("Failed to open video.")
            
            # Setup Resize
            target_size = None
            if resize_mode != "Original":
                try:
                    parts = resize_mode.split('x')
                    target_size = (int(parts[0]), int(parts[1]))
                except: pass

            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frames = []
            count = 0
            effective_cap = frame_load_cap if frame_load_cap > 0 else 999999
            
            while len(frames) < effective_cap:
                ret, frame = cap.read()
                if not ret: break
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if target_size:
                    frame = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
                
                frame = frame.astype(np.float32) / 255.0
                frames.append(torch.from_numpy(frame))
            
            cap.release()
            
            if not frames: raise RuntimeError("No frames extracted from video.")
            out_img = torch.stack(frames)
            
            # Dummy Mask/Audio for now (Advanced audio loading requires dependencies)
            out_mask = torch.zeros((out_img.shape[0], out_img.shape[1], out_img.shape[2]), dtype=torch.float32)
            out_audio = {"waveform": torch.zeros((1, 2, 44100)), "sample_rate": 44100}
            
            return (out_img, out_mask, out_audio, filename)

        # --- IMAGE LOADER LOGIC ---
        else:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            
            # Handle RGBA/Mask
            if "A" in img.getbands():
                mask = np.array(img.getchannel("A")).astype(np.float32) / 255.0
                mask = torch.from_numpy(mask).unsqueeze(0)
            else:
                mask = torch.zeros((1, img.height, img.width), dtype=torch.float32)
            
            img = img.convert("RGB")
            img_np = np.array(img).astype(np.float32) / 255.0
            out_img = torch.from_numpy(img_np).unsqueeze(0)
            
            # Dummy Audio
            out_audio = {"waveform": torch.zeros((1, 2, 44100)), "sample_rate": 44100}
            
            return (out_img, mask, out_audio, filename)