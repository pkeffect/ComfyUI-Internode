# ComfyUI/custom_nodes/ComfyUI-Internode/internode/video_fx/universal_player.py
# VERSION: 3.0.9

import torch
import numpy as np
import os
import folder_paths
import subprocess
import scipy.io.wavfile
import cv2
import random

class InternodeUniversalPlayer:
    """
    A comprehensive media player for ComfyUI.
    Combines Images and Audio into a previewable video file using FFmpeg.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "fps": ("INT", {"default": 24, "min": 1, "max": 120, "step": 1}),
                "lossless": ("BOOLEAN", {"default": False, "tooltip": "Use CRF 0 for video (larger files, perfect quality) vs standard preview quality."}),
            },
            "optional": {
                "images": ("IMAGE",),
                "audio": ("AUDIO",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("IMAGE", "AUDIO")
    RETURN_NAMES = ("images", "audio")
    FUNCTION = "play_media"
    CATEGORY = "Internode/VideoFX"
    OUTPUT_NODE = True

    def play_media(self, fps, lossless, unique_id, images=None, audio=None):
        # Setup Paths
        output_dir = folder_paths.get_temp_directory()
        prefix = f"internode_preview_{unique_id}_{random.randint(0, 100000)}"
        
        # 1. Process Audio (if present)
        audio_path = None
        if audio is not None:
            audio_path = os.path.join(output_dir, f"{prefix}.wav")
            waveform = audio["waveform"]
            sample_rate = audio["sample_rate"]
            
            # Convert Tensor to Numpy
            if waveform.dim() == 3: waveform = waveform[0] # Take batch 0
            audio_np = waveform.cpu().numpy().T # [Samples, Channels]
            
            # Save WAV
            scipy.io.wavfile.write(audio_path, sample_rate, audio_np)

        # 2. Process Video (if present)
        video_path = None
        filename_out = None
        type_out = "none"

        if images is not None:
            # Check dimensions
            batch_size, height, width, channels = images.shape
            
            # Use OpenCV to write video frames to a temp file
            # We use 'mp4v' for temporary container before ffmpeg muxing
            temp_vid = os.path.join(output_dir, f"{prefix}_temp.mp4")
            
            # Convert tensor to uint8 numpy
            images_np = (images * 255).clip(0, 255).byte().cpu().numpy()
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_vid, fourcc, fps, (width, height))
            
            for i in range(batch_size):
                # RGB to BGR for OpenCV
                frame = images_np[i]
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)
            out.release()

            # 3. Muxing with FFmpeg
            final_vid = os.path.join(output_dir, f"{prefix}.mp4")
            filename_out = f"{prefix}.mp4"
            type_out = "video"
            
            cmd = [
                "ffmpeg", "-y",
                "-i", temp_vid
            ]
            
            if audio_path:
                cmd.extend(["-i", audio_path])
                
            # Encoding settings (H.264 for web compatibility)
            # -pix_fmt yuv420p is required for browser playback
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
            
            if lossless:
                cmd.extend(["-crf", "18", "-preset", "slow"])
            else:
                cmd.extend(["-crf", "23", "-preset", "fast"]) # Standard preview
                
            if audio_path:
                cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])
            
            cmd.append(final_vid)
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Cleanup temp
                if os.path.exists(temp_vid): os.remove(temp_vid)
                if audio_path and os.path.exists(audio_path): os.remove(audio_path)
            except Exception as e:
                print(f"#### Internode Error: FFmpeg muxing failed. {e}")
                # Fallback to temp video if ffmpeg fails (might not play in browser if encoding is wrong)
                if os.path.exists(temp_vid):
                    os.rename(temp_vid, final_vid)

        elif audio_path:
            # Audio Only
            filename_out = f"{prefix}.wav"
            type_out = "audio"
        
        # 4. Return UI update
        # ComfyUI frontend expects a list of images usually, but we define a custom structure
        # that our JS will intercept.
        
        return {
            "ui": {
                "file": [filename_out],
                "type": [type_out],
                "folder": ["_temp"] # Signal it's in temp folder
            }, 
            "result": (images, audio)
        }