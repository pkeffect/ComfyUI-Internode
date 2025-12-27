import torch
from .openwebui_api import OpenWebUIAPI
import numpy as np
from PIL import Image, PngInfo
import os
import json
import time
import base64
import re
from io import BytesIO
import random

# ComfyUI Imports
import folder_paths

# Optional Audio Support
try:
    from scipy.io import wavfile
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# --- Caching & Config Helpers ---

_model_cache = {
    "models": None,
    "timestamp": 0,
    "ttl": 300 
}

def load_config_file():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.json")
    config = { "host": "http://localhost:3000", "api_key": "" }
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_data = json.load(f)
                config["host"] = file_data.get("host", config["host"])
                config["api_key"] = file_data.get("api_key", config["api_key"])
        except Exception as e:
            print(f"#### Internode Error reading config.json: {e}")
    return config

def get_cached_models(host, api_key):
    global _model_cache
    now = time.time()
    if _model_cache["models"] is not None and (now - _model_cache["timestamp"]) < _model_cache["ttl"]:
        return _model_cache["models"]
    
    model_list = []
    try:
        # Only fetch if host looks valid
        if api_key or "localhost" in host or "127.0.0.1" in host:
            api = OpenWebUIAPI(host=host, api_key=api_key)
            model_list = api.get_models()
        if model_list:
            _model_cache["models"] = model_list
            _model_cache["timestamp"] = now
    except Exception as e:
        print(f"#### Internode Model Fetch Error: {e}")
        # Fallback to cache even if expired to prevent blocking UI
        if _model_cache["models"]: return _model_cache["models"]
    
    if not model_list: model_list = ["default"]
    return model_list

def tensor_to_pil(img):
    return Image.fromarray(np.clip(255. * img.cpu().numpy(), 0, 255).astype(np.uint8))

# --- Node Definitions ---

class OpenWebUIServerConfig:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "host": ("STRING", {"default": "http://localhost:3000"}),
                "api_key": ("STRING", {"default": ""}), 
            },
        }
    RETURN_TYPES = ("OPENWEBUI_CONFIG",)
    FUNCTION = "get_config"
    CATEGORY = "Internode/OpenWebUI"
    def get_config(self, host, api_key):
        return ({"host": host, "api_key": api_key},)

class OpenWebUINode:
    """
    Unified node for OpenWebUI supporting Context/History.
    """
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        default_host = config["host"]
        default_key = config["api_key"]
        model_list = get_cached_models(default_host, default_key)

        return {
            "required": {
                "model": (model_list,), 
                "manual_model": ("STRING", {"default": "", "multiline": False, "placeholder": "Model name override (Optional)"}),
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "rows": 10}),
            },
            "optional": {
                "server_config": ("OPENWEBUI_CONFIG",),
                "history": ("STRING", {"default": "", "forceInput": True}),
                "image": ("IMAGE",),
                "audio": ("AUDIO",),
                "video": ("IMAGE",), 
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "history")
    FUNCTION = "process"
    CATEGORY = "Internode/OpenWebUI"

    def process(self, model, prompt, manual_model="", server_config=None, history="", image=None, audio=None, video=None):
        if server_config:
            host = server_config["host"]
            api_key = server_config["api_key"]
        else:
            file_config = load_config_file()
            host = file_config["host"]
            api_key = file_config["api_key"]
        
        target_model = manual_model.strip() if manual_model.strip() else model
        api = OpenWebUIAPI(host=host, api_key=api_key)
        
        # Load History
        messages = []
        if history and history.strip():
            try:
                messages = json.loads(history)
                if not isinstance(messages, list): messages = []
            except: messages = []

        # Process Multimodal Inputs
        pil_images = []
        # Single Images
        if image is not None:
            for img in image:
                pil_images.append(tensor_to_pil(img))
        # Video Frames
        if video is not None:
            for img in video:
                pil_images.append(tensor_to_pil(img))

        # Audio
        b64_audio = None
        if audio is not None and SCIPY_AVAILABLE:
            waveform = audio["waveform"]
            sample_rate = audio["sample_rate"]
            if waveform.dim() == 3: waveform = waveform[0] 
            audio_np = waveform.cpu().numpy().T
            buffered = BytesIO()
            wavfile.write(buffered, sample_rate, audio_np)
            b64_audio = base64.b64encode(buffered.getvalue()).decode()

        print(f"#### Internode: Sending to OpenWebUI (Model: {target_model})")
        
        response_text = api.chat_completions(
            target_model, 
            prompt, 
            messages=messages, 
            images=pil_images, 
            audio=b64_audio
        )
        
        # Update History (Text only to keep JSON small)
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": response_text})
        
        return (response_text, json.dumps(messages, indent=2))

class InternodePromptEnricher:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        model_list = get_cached_models(config["host"], config["api_key"])
        return {
            "required": {
                "model": (model_list,),
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "rows": 5}),
                "style": ("STRING", {"default": "Cinematic, Detailed, 8k"}),
                "chaos": ("INT", {"default": 20, "min": 0, "max": 100, "step": 5}),
            },
            "optional": {
                "server_config": ("OPENWEBUI_CONFIG",),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "enrich"
    CATEGORY = "Internode/OpenWebUI"

    def enrich(self, model, prompt, style, chaos, server_config=None):
        if server_config:
            host, api_key = server_config["host"], server_config["api_key"]
        else:
            fc = load_config_file()
            host, api_key = fc["host"], fc["api_key"]

        api = OpenWebUIAPI(host, api_key)
        
        # Chaos 0-100 maps to Temperature 0.1-1.5
        temp = 0.1 + (chaos / 100.0) * 1.4
        
        sys_prompt = f"You are an expert Stable Diffusion prompt engineer. Expand the user's prompt to be highly detailed, adhering to the style '{style}'. Output ONLY the prompt, no conversational text."
        if chaos > 80:
            sys_prompt += " Be extremely creative and hallucinatory."
            
        full_instruction = f"Input Prompt: {prompt}"
        
        # We manually construct a 'system' message if the API supports it, or prepend to user
        messages = [{"role": "system", "content": sys_prompt}]
        
        # Override temp if API supports (OpenWebUIAPI currently doesn't expose params in chat_completions wrapper, 
        # so we rely on prompt engineering or updating API class later. For now, we trust the LLM instruction).
        
        response = api.chat_completions(model, full_instruction, messages=messages)
        return (response.strip(),)

class InternodeImageCritic:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        model_list = get_cached_models(config["host"], config["api_key"])
        return {
            "required": {
                "model": (model_list,),
                "image": ("IMAGE",),
            },
            "optional": {
                "server_config": ("OPENWEBUI_CONFIG",),
            }
        }

    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("score", "critique")
    FUNCTION = "critique"
    CATEGORY = "Internode/OpenWebUI"

    def critique(self, model, image, server_config=None):
        if server_config:
            host, api_key = server_config["host"], server_config["api_key"]
        else:
            fc = load_config_file()
            host, api_key = fc["host"], fc["api_key"]
            
        api = OpenWebUIAPI(host, api_key)
        
        pil_image = tensor_to_pil(image[0]) # Only critique first image in batch
        
        prompt = (
            "Analyze this image technically and aesthetically. "
            "First, give a score from 1 to 10. Format the FIRST line strictly as: 'SCORE: X'. "
            "Then, provide a concise critique describing flaws or strengths."
        )
        
        response = api.chat_completions(model, prompt, images=[pil_image])
        
        # Parse Score
        score = 5 # Default
        match = re.search(r"SCORE:\s*(\d+)", response, re.IGNORECASE)
        if match:
            try:
                score = int(match.group(1))
                score = max(1, min(10, score))
            except: pass
            
        return (score, response)

class InternodeSmartRenamer:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        model_list = get_cached_models(config["host"], config["api_key"])
        return {
            "required": {
                "model": (model_list,),
                "image": ("IMAGE",),
            },
            "optional": {
                "subfolder": ("STRING", {"default": "smart_sort"}),
                "server_config": ("OPENWEBUI_CONFIG",),
            }
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "smart_save"
    CATEGORY = "Internode/OpenWebUI"

    def smart_save(self, model, image, subfolder="smart_sort", server_config=None):
        if server_config:
            host, api_key = server_config["host"], server_config["api_key"]
        else:
            fc = load_config_file()
            host, api_key = fc["host"], fc["api_key"]

        api = OpenWebUIAPI(host, api_key)
        output_dir = folder_paths.get_output_directory()
        full_output_dir = os.path.join(output_dir, subfolder)
        os.makedirs(full_output_dir, exist_ok=True)
        
        results = list()
        
        # 1. Get base name from LLM using the first image
        first_pil = tensor_to_pil(image[0])
        prompt = (
            "Generate a short, descriptive filename for this image. "
            "Use lowercase, underscores instead of spaces, max 5 words. "
            "Do NOT include file extension. Example: black_cat_forest_sunset. "
            "Output ONLY the filename string."
        )
        
        filename_base = api.chat_completions(model, prompt, images=[first_pil]).strip()
        
        # Sanitize
        filename_base = re.sub(r'[\\/*?:"<>|.\n]', "", filename_base)
        filename_base = filename_base.replace(" ", "_")
        if len(filename_base) > 50: filename_base = filename_base[:50]
        if not filename_base: filename_base = "image"
        
        # 2. Save Batch
        for i, img_tensor in enumerate(image):
            img = tensor_to_pil(img_tensor)
            
            # Find unique filename
            counter = 1
            file_suffix = f"_{i:02d}" if len(image) > 1 else ""
            
            while True:
                filename = f"{filename_base}{file_suffix}_{counter:04d}.png"
                file_path = os.path.join(full_output_dir, filename)
                if not os.path.exists(file_path):
                    break
                counter += 1
            
            # Metadata
            metadata = PngInfo()
            # (Optional: Add standard Comfy metadata if accessible, simplified here)
            
            img.save(file_path, pnginfo=metadata, compress_level=4)
            
            results.append({
                "filename": filename,
                "subfolder": subfolder,
                "type": "output"
            })
            
        return { "ui": { "images": results } }

class OpenWebUIRefreshModels:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "trigger": ("INT", {"default": 0, "min": 0, "max": 1000}),
            },
            "optional": {
                "server_config": ("OPENWEBUI_CONFIG",),
            }
        }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_list",)
    FUNCTION = "refresh"
    CATEGORY = "Internode/OpenWebUI"

    def refresh(self, trigger, server_config=None):
        global _model_cache
        if server_config:
            host, api_key = server_config["host"], server_config["api_key"]
        else:
            fc = load_config_file()
            host, api_key = fc["host"], fc["api_key"]
        
        _model_cache["models"] = None
        _model_cache["timestamp"] = 0
        models = get_cached_models(host, api_key)
        return ("\n".join(models),)

# --- Registration ---

NODE_CLASS_MAPPINGS = {
    "Internode_OpenWebUIServerConfig": OpenWebUIServerConfig,
    "Internode_OpenWebUINode": OpenWebUINode,
    "Internode_OpenWebUIRefreshModels": OpenWebUIRefreshModels,
    "InternodePromptEnricher": InternodePromptEnricher,
    "InternodeImageCritic": InternodeImageCritic,
    "InternodeSmartRenamer": InternodeSmartRenamer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Internode_OpenWebUIServerConfig": "OpenWebUI Server Config (Internode)",
    "Internode_OpenWebUINode": "OpenWebUI Unified (Internode)",
    "Internode_OpenWebUIRefreshModels": "OpenWebUI Refresh Models (Internode)",
    "InternodePromptEnricher": "Prompt Enricher (LLM) (Internode)",
    "InternodeImageCritic": "Image Critic (Vision) (Internode)",
    "InternodeSmartRenamer": "Smart Renamer & Save (Vision) (Internode)",
}