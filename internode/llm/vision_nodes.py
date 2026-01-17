# ComfyUI/custom_nodes/ComfyUI-Internode/internode/llm/vision_nodes.py
# VERSION: 3.3.0

import torch
import numpy as np
from PIL import Image
import re
import json

from .openwebui_nodes import get_cached_models, load_config_file, tensor_to_pil, get_api

class InternodeVisionRefiner:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "image": ("IMAGE",),
                "original_prompt": ("STRING", {"multiline": True, "rows": 5}),
                "feedback_strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("refined_prompt",)
    FUNCTION = "refine"
    CATEGORY = "Internode/LLM Vision"

    def refine(self, model, image, original_prompt, feedback_strength, server_config=None):
        api = get_api(server_config)
        pil_image = tensor_to_pil(image[0])
        
        sys_msg = (
            "You are an expert AI Art critic. Compare the image provided with the prompt below. "
            "Identify what is missing or poorly rendered. "
            "Output a REVISED prompt that includes corrections to better match the original intent."
        )
        
        user_msg = f"Original Prompt: {original_prompt}"
        response = api.chat_completions(model, user_msg, messages=[{"role": "system", "content": sys_msg}], images=[pil_image])
        
        return (response.strip(),)

class InternodeVisionStyleMatcher:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "image": ("IMAGE",),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("style_prompt",)
    FUNCTION = "analyze"
    CATEGORY = "Internode/LLM Vision"

    def analyze(self, model, image, server_config=None):
        api = get_api(server_config)
        pil_image = tensor_to_pil(image[0])
        
        sys_msg = (
            "Analyze the artistic style of this image. Focus on: Medium (oil, digital, photo), "
            "Lighting (soft, cinematic, hard), Color Palette, and Artist influences. "
            "Output ONLY a comma-separated string of style descriptors suitable for Stable Diffusion."
        )
        
        response = api.chat_completions(model, "Describe the style.", messages=[{"role": "system", "content": sys_msg}], images=[pil_image])
        return (response.strip(),)

class InternodeVisionContentExtractor:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "image": ("IMAGE",),
                "mode": (["List (Comma)", "JSON", "Detailed Description"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("content_data",)
    FUNCTION = "extract"
    CATEGORY = "Internode/LLM Vision"

    def extract(self, model, image, mode, server_config=None):
        api = get_api(server_config)
        pil_image = tensor_to_pil(image[0])
        
        prompt = "Describe the contents of this image."
        if mode == "List (Comma)":
            prompt += " Output a simple comma-separated list of objects and main concepts."
        elif mode == "JSON":
            prompt += " Output valid JSON with keys: 'objects', 'setting', 'colors', 'mood'."
        
        response = api.chat_completions(model, prompt, images=[pil_image])
        
        # Cleanup JSON if needed
        if mode == "JSON":
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match: response = match.group(0)
            
        return (response.strip(),)

class InternodeVisionInpaintPrompter:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "image": ("IMAGE",),
                "task": ("STRING", {"default": "fill the empty space with a futuristic city"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("inpaint_prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "Internode/LLM Vision"

    def generate_prompt(self, model, image, task, server_config=None):
        api = get_api(server_config)
        pil_image = tensor_to_pil(image[0])
        
        sys_msg = (
            "You are assisting with Image Inpainting/Outpainting. "
            "Analyze the image context (lighting, perspective, style). "
            "Based on the user's task, write a prompt that ensures the new content blends perfectly with the existing image."
        )
        
        response = api.chat_completions(model, f"Task: {task}", messages=[{"role": "system", "content": sys_msg}], images=[pil_image])
        return (response.strip(),)