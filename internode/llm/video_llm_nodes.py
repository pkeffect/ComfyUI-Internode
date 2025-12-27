# ComfyUI/custom_nodes/ComfyUI-Internode/internode/llm/video_llm_nodes.py
# VERSION: 3.3.0

import torch
import numpy as np
import json
import re
from PIL import Image
from .openwebui_nodes import get_cached_models, load_config_file, tensor_to_pil, get_api

class InternodeVideoNarrator:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "images": ("IMAGE",),
                "frame_interval": ("INT", {"default": 30, "min": 1, "max": 300}),
                "narrative_style": (["Documentary", "Film Noir", "Excited Youtuber", "Poetic"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("script",)
    FUNCTION = "narrate"
    CATEGORY = "Internode/LLM Video"

    def narrate(self, model, images, frame_interval, narrative_style, server_config=None):
        api = get_api(server_config)
        
        # Select keyframes to avoid sending 1000 images
        keyframes = []
        total_frames = images.shape[0]
        for i in range(0, total_frames, frame_interval):
            keyframes.append(tensor_to_pil(images[i]))
        
        # Cap max images to avoid API timeout/limits
        if len(keyframes) > 10:
            # Resample to exactly 10 if too many
            step = len(keyframes) // 10
            keyframes = keyframes[::step][:10]

        sys_msg = (
            f"You are a Video Narrator. Analyze the sequence of frames provided. "
            f"Write a cohesive voiceover script in the style of '{narrative_style}'. "
            f"Focus on the progression of action and mood."
        )
        
        response = api.chat_completions(model, "Narrate this scene.", messages=[{"role": "system", "content": sys_msg}], images=keyframes)
        return (response.strip(),)

class InternodeAIColorist:
    """
    Analyzes a frame + prompt and generates Lift/Gamma/Gain values 
    compatible with the InternodeColorGrade node.
    """
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "image": ("IMAGE",),
                "mood_prompt": ("STRING", {"multiline": True, "default": "Cyberpunk, high contrast, neon green shadows, warm highlights"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    # Outputs match InternodeColorGrade inputs
    RETURN_TYPES = ("FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("lift_r", "lift_g", "lift_b", "gamma_r", "gamma_g", "gamma_b", "gain_r", "gain_g", "gain_b")
    FUNCTION = "generate_grade"
    CATEGORY = "Internode/LLM Video"

    def generate_grade(self, model, image, mood_prompt, server_config=None):
        api = get_api(server_config)
        pil_image = tensor_to_pil(image[0]) # Analyze first frame
        
        sys_msg = (
            "You are a Professional Colorist. "
            "Analyze the image and the user's desired mood. "
            "Output JSON ONLY with 3 keys: 'lift' (RGB offset, -0.5 to 0.5), 'gamma' (RGB power, 0.5 to 2.0), 'gain' (RGB mult, 0.5 to 2.0). "
            "Example: {\"lift\": [-0.1, 0.0, 0.1], \"gamma\": [1.0, 0.9, 1.1], \"gain\": [1.0, 1.2, 0.8]}"
        )
        
        response = api.chat_completions(model, f"Mood: {mood_prompt}", messages=[{"role": "system", "content": sys_msg}], images=[pil_image])
        
        # Safe Parsing Defaults
        l, gm, gn = [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]
        
        try:
            # Find JSON blob
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                l = data.get("lift", l)
                gm = data.get("gamma", gm)
                gn = data.get("gain", gn)
        except Exception as e:
            print(f"#### Internode Colorist Error: {e}")

        # Unpack
        return (l[0], l[1], l[2], gm[0], gm[1], gm[2], gn[0], gn[1], gn[2])

class InternodeVideoSceneDescriptor:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "images": ("IMAGE",),
                "frame_interval": ("INT", {"default": 10}),
                "detail_level": (["Short Tag", "Full Sentence"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING", "STRING_LIST")
    RETURN_NAMES = ("concatenated_text", "text_list")
    FUNCTION = "describe_sequence"
    CATEGORY = "Internode/LLM Video"

    def describe_sequence(self, model, images, frame_interval, detail_level, server_config=None):
        api = get_api(server_config)
        
        results = []
        total_frames = images.shape[0]
        
        # We process sequentially. This might be slow.
        sys_msg = "Describe this video frame briefly." if detail_level == "Short Tag" else "Describe the action and setting of this video frame in one sentence."
        
        for i in range(0, total_frames, frame_interval):
            pil_img = tensor_to_pil(images[i])
            desc = api.chat_completions(model, "Describe.", messages=[{"role": "system", "content": sys_msg}], images=[pil_img])
            formatted = f"Frame {i}: {desc.strip()}"
            results.append(formatted)
            
        return ("\n".join(results), results)

class InternodeVideoTrackerPrompt:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "images": ("IMAGE",),
                "target_hint": ("STRING", {"default": "the red car"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("tracking_prompts",)
    FUNCTION = "track_and_describe"
    CATEGORY = "Internode/LLM Video"

    def track_and_describe(self, model, images, target_hint, server_config=None):
        api = get_api(server_config)
        # To save tokens, we only look at Start, Middle, End
        indices = [0, len(images)//2, len(images)-1]
        
        descriptions = []
        for i in indices:
            pil_img = tensor_to_pil(images[i])
            prompt = f"Locate '{target_hint}' in this image and describe its movement, position, or appearance changes."
            desc = api.chat_completions(model, prompt, images=[pil_img])
            descriptions.append(f"Frame {i}: {desc}")
            
        return ("\n".join(descriptions),)