# ComfyUI/custom_nodes/ComfyUI-Internode/internode/utils/metadata_inspector.py
# VERSION: 3.1.0

import os
import json
import folder_paths
from PIL import Image
import torchaudio
import re

class InternodeMetadataInspector:
    """
    Inspects a file (Image/Audio) for embedded metadata.
    - Images: Extracts PNG Info (Parameters, Workflow), Dimensions.
    - Audio: Extracts Sample Rate, Channels, Duration, Encoding.
    - Features: Regex parsing for 'Seed' from generation text.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files.sort()
        
        return {
            "required": {
                "filename": (files, {"default": "none"}),
                "extract_key": ("STRING", {"default": "Seed", "multiline": False, "tooltip": "Key to extract to 'extracted_value' output."}),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("json_view", "width_or_duration", "height_or_sr", "extracted_value")
    FUNCTION = "inspect"
    CATEGORY = "Internode/Utils"
    OUTPUT_NODE = True

    def inspect(self, filename, extract_key):
        path = folder_paths.get_annotated_filepath(filename)
        
        data = {
            "filename": filename,
            "exists": os.path.exists(path),
            "path": path
        }
        
        meta_str = ""
        val_1 = 0 # Width / Duration
        val_2 = 0 # Height / SampleRate
        extracted = "None"

        if os.path.exists(path):
            ext = os.path.splitext(filename)[1].lower()
            
            # --- IMAGE HANDLING ---
            if ext in ['.png', '.jpg', '.jpeg', '.webp']:
                try:
                    with Image.open(path) as img:
                        data["type"] = "Image"
                        data["format"] = img.format
                        data["mode"] = img.mode
                        data["size"] = img.size
                        val_1, val_2 = img.size
                        
                        # Extract PNG Info / Exif
                        info = img.info
                        # Handle A1111/Comfy parameters
                        if "parameters" in info:
                            data["generation_data"] = info["parameters"]
                            meta_str = info["parameters"]
                        elif "workflow" in info:
                            data["workflow"] = "ComfyUI Workflow Found"
                            # Workflow is often too huge to display fully in raw text, maybe summarize
                            try:
                                wf = json.loads(info["workflow"])
                                data["node_count"] = len(wf.get("nodes", []))
                            except: pass
                        elif "comment" in info:
                            data["comment"] = info["comment"]
                            meta_str = info["comment"]
                            
                except Exception as e:
                    data["error"] = str(e)

            # --- AUDIO HANDLING ---
            elif ext in ['.wav', '.mp3', '.flac', '.ogg', '.m4a']:
                try:
                    info = torchaudio.info(path)
                    data["type"] = "Audio"
                    data["sample_rate"] = info.sample_rate
                    data["channels"] = info.num_channels
                    data["bits_per_sample"] = info.bits_per_sample
                    data["encoding"] = info.encoding
                    data["num_frames"] = info.num_frames
                    
                    duration = info.num_frames / info.sample_rate
                    data["duration_sec"] = round(duration, 3)
                    
                    val_1 = int(duration)
                    val_2 = info.sample_rate
                    
                except Exception as e:
                    data["error"] = f"Torchaudio failed: {e}"
            else:
                data["type"] = "Unknown"

        # --- EXTRACTION LOGIC ---
        # 1. Try to find key in top-level dict
        if extract_key in data:
            extracted = str(data[extract_key])
        
        # 2. If we have a generation string, try Regex for "Key: Value"
        # Standard A1111 format: "Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 12345"
        if meta_str and extract_key:
            # Regex look for "Key: Value" or "Key:Value"
            # Case insensitive
            pattern = r"(?i)" + re.escape(extract_key) + r"\s*:\s*([^,]+)"
            match = re.search(pattern, meta_str)
            if match:
                extracted = match.group(1).strip()

        # Final JSON formatting
        json_output = json.dumps(data, indent=2)
        
        # Return UI object
        return {
            "ui": {"json": [json_output]},
            "result": (json_output, val_1, val_2, extracted)
        }