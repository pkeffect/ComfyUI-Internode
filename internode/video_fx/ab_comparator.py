# ComfyUI/custom_nodes/ComfyUI-Internode/internode/video_fx/ab_comparator.py
# VERSION: 3.1.0

import torch
import numpy as np
import os
import folder_paths
import subprocess
import cv2
import random
from PIL import Image

class InternodeABComparator:
    """
    A visual comparison tool.
    Accepts two inputs (A and B).
    - If single frames: displays Image comparison with slider.
    - If multi-frames: renders temporary MP4s and displays Video comparison with synchronized playback.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_a": ("IMAGE",),
                "image_b": ("IMAGE",),
                "fps": ("INT", {"default": 24, "min": 1, "max": 120}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "compare"
    CATEGORY = "Internode/VideoFX"
    OUTPUT_NODE = True

    def save_temp_content(self, images, fps, prefix):
        output_dir = folder_paths.get_temp_directory()
        batch_size, height, width, channels = images.shape
        
        # Scenario 1: Single Image
        if batch_size == 1:
            file_name = f"{prefix}.png"
            full_path = os.path.join(output_dir, file_name)
            img_np = (images[0] * 255).byte().cpu().numpy()
            img_pil = Image.fromarray(img_np)
            img_pil.save(full_path)
            return file_name, "image"

        # Scenario 2: Video (Batch)
        file_name = f"{prefix}.mp4"
        full_path = os.path.join(output_dir, file_name)
        
        # Write temp video via OpenCV then FFMPEG for web compatibility
        temp_vid = os.path.join(output_dir, f"{prefix}_raw.mp4")
        images_np = (images * 255).clip(0, 255).byte().cpu().numpy()
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_vid, fourcc, fps, (width, height))
        
        for i in range(batch_size):
            frame = cv2.cvtColor(images_np[i], cv2.COLOR_RGB2BGR)
            out.write(frame)
        out.release()
        
        # Remux to H.264 for browser support
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_vid,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "23", "-preset", "ultrafast",
            full_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(temp_vid): os.remove(temp_vid)
        except:
            print("#### Internode: FFmpeg failed, falling back to raw (might not play in browser)")
            if os.path.exists(temp_vid): os.rename(temp_vid, full_path)
            
        return file_name, "video"

    def compare(self, image_a, image_b, fps, unique_id):
        # Generate random ID to avoid browser cache issues
        rand_id = random.randint(0, 100000)
        
        file_a, type_a = self.save_temp_content(image_a, fps, f"ab_compare_A_{unique_id}_{rand_id}")
        file_b, type_b = self.save_temp_content(image_b, fps, f"ab_compare_B_{unique_id}_{rand_id}")
        
        return {
            "ui": {
                "files": [file_a, file_b],
                "types": [type_a, type_b],
                "folder": "_temp"
            }
        }