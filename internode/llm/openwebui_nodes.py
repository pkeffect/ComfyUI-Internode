# ComfyUI/custom_nodes/ComfyUI-Internode/internode/llm/openwebui_nodes.py
# VERSION: 3.3.0

import torch
from .openwebui_api import OpenWebUIAPI
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
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
        if api_key or "localhost" in host or "127.0.0.1" in host:
            api = OpenWebUIAPI(host=host, api_key=api_key)
            model_list = api.get_models()
        if model_list:
            _model_cache["models"] = model_list
            _model_cache["timestamp"] = now
    except Exception as e:
        print(f"#### Internode Model Fetch Error: {e}")
        if _model_cache["models"]: return _model_cache["models"]
    
    if not model_list: model_list = ["default"]
    return model_list

def tensor_to_pil(img):
    return Image.fromarray(np.clip(255. * img.cpu().numpy(), 0, 255).astype(np.uint8))

def get_api(server_config):
    if server_config:
        return OpenWebUIAPI(server_config["host"], server_config["api_key"])
    fc = load_config_file()
    return OpenWebUIAPI(fc["host"], fc["api_key"])

# --- Existing Core Nodes ---

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
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        model_list = get_cached_models(config["host"], config["api_key"])
        return {
            "required": {
                "model": (model_list,), 
                "manual_model": ("STRING", {"default": "", "placeholder": "Model name override"}),
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
        api = get_api(server_config)
        target_model = manual_model.strip() if manual_model.strip() else model
        
        messages = []
        if history and history.strip():
            try:
                messages = json.loads(history)
                if not isinstance(messages, list): messages = []
            except: messages = []

        pil_images = []
        if image is not None:
            for img in image: pil_images.append(tensor_to_pil(img))
        if video is not None:
            for img in video: pil_images.append(tensor_to_pil(img))

        b64_audio = None
        if audio is not None and SCIPY_AVAILABLE:
            waveform = audio["waveform"]
            sample_rate = audio["sample_rate"]
            if waveform.dim() == 3: waveform = waveform[0] 
            audio_np = waveform.cpu().numpy().T
            buffered = BytesIO()
            wavfile.write(buffered, sample_rate, audio_np)
            b64_audio = base64.b64encode(buffered.getvalue()).decode()
        
        response_text = api.chat_completions(target_model, prompt, messages=messages, images=pil_images, audio=b64_audio)
        
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": response_text})
        
        return (response_text, json.dumps(messages, indent=2))

class OpenWebUIRefreshModels:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"trigger": ("INT", {"default": 0, "min": 0, "max": 1000})}, "optional": {"server_config": ("OPENWEBUI_CONFIG",)}}
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_list",)
    FUNCTION = "refresh"
    CATEGORY = "Internode/OpenWebUI"
    def refresh(self, trigger, server_config=None):
        global _model_cache
        api = get_api(server_config)
        _model_cache["models"] = None
        _model_cache["timestamp"] = 0
        models = get_cached_models(api.host, api.api_key)
        return ("\n".join(models),)

# --- Expanded Text Generation Nodes ---

class InternodeLLMPromptOptimizer:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "prompt": ("STRING", {"multiline": True, "rows": 5}),
                "level": (["Light Polish", "Detail Expansion", "Creative Overhaul"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "optimize"
    CATEGORY = "Internode/LLM Text"

    def optimize(self, model, prompt, level, server_config=None):
        api = get_api(server_config)
        sys_msg = "You are a prompt engineering expert. Improve the user's prompt for an image generation model."
        if level == "Light Polish": sys_msg += " Fix grammar and clarity only. Keep it concise."
        elif level == "Detail Expansion": sys_msg += " Add descriptive details about lighting, texture, and composition."
        elif level == "Creative Overhaul": sys_msg += " Reimagine the concept creatively. Be verbose and artistic."
        
        messages = [{"role": "system", "content": sys_msg}]
        res = api.chat_completions(model, f"Prompt: {prompt}", messages=messages)
        return (res.strip(),)

class InternodeLLMStyleTransfer:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "text": ("STRING", {"multiline": True, "rows": 5}),
                "target_style": ("STRING", {"default": "Cyberpunk, Neon, Gritty"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "transfer"
    CATEGORY = "Internode/LLM Text"

    def transfer(self, model, text, target_style, server_config=None):
        api = get_api(server_config)
        sys_msg = f"Rewrite the following text description to match this style: '{target_style}'. output ONLY the rewritten prompt."
        res = api.chat_completions(model, text, messages=[{"role": "system", "content": sys_msg}])
        return (res.strip(),)

class InternodeLLMStoryBrancher:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "narrative_prompt": ("STRING", {"multiline": True, "rows": 5}),
                "num_branches": ("INT", {"default": 3, "min": 1, "max": 5}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING", "STRING_LIST")
    RETURN_NAMES = ("combined_text", "branches_list")
    FUNCTION = "branch"
    CATEGORY = "Internode/LLM Text"

    def branch(self, model, narrative_prompt, num_branches, server_config=None):
        api = get_api(server_config)
        sys_msg = f"You are a storyteller. Given a scenario, generate {num_branches} distinct, creative plot twists or continuation options. Format them as a numbered list."
        res = api.chat_completions(model, narrative_prompt, messages=[{"role": "system", "content": sys_msg}])
        
        # Simple parser to split lines into a list
        lines = res.split('\n')
        branches = [line.strip() for line in lines if line.strip() and (line[0].isdigit() or line.startswith('-'))]
        if not branches: branches = [res] # Fallback
        
        return (res, branches)

class InternodeLLMCharacterGen:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "name": ("STRING", {"default": "Unknown"}),
                "archetype": ("STRING", {"default": "The Reluctant Hero"}),
                "traits": ("STRING", {"default": "Brave, clumsy, likes cats"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate"
    CATEGORY = "Internode/LLM Text"

    def generate(self, model, name, archetype, traits, server_config=None):
        api = get_api(server_config)
        prompt = f"Create a detailed character profile for '{name}'. Archetype: {archetype}. Traits: {traits}. Include Backstory, Appearance, and Motivation."
        res = api.chat_completions(model, prompt)
        return (res,)

class InternodeLLMDialogue:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "characters": ("STRING", {"default": "Alice (Optimist), Bob (Pessimist)"}),
                "scenario": ("STRING", {"multiline": True, "rows": 5}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "write"
    CATEGORY = "Internode/LLM Text"

    def write(self, model, characters, scenario, server_config=None):
        api = get_api(server_config)
        sys_msg = f"Write a short dialogue scene between these characters: {characters}. Keep it engaging and true to their personalities."
        res = api.chat_completions(model, f"Scenario: {scenario}", messages=[{"role": "system", "content": sys_msg}])
        return (res,)

class InternodeLLMWorldBuilder:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "concept": ("STRING", {"default": "A floating city powered by steam"}),
                "focus": (["Geography", "Culture", "Lore/History", "Flora/Fauna"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "build"
    CATEGORY = "Internode/LLM Text"

    def build(self, model, concept, focus, server_config=None):
        api = get_api(server_config)
        sys_msg = f"You are a world-building expert. Expand on the user's concept, focusing specifically on '{focus}'."
        res = api.chat_completions(model, concept, messages=[{"role": "system", "content": sys_msg}])
        return (res,)

class InternodeLLMCodeGen:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "description": ("STRING", {"multiline": True, "rows": 5}),
                "language": (["Python", "JavaScript", "GLSL", "HTML/CSS", "Regex"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "code"
    CATEGORY = "Internode/LLM Text"

    def code(self, model, description, language, server_config=None):
        api = get_api(server_config)
        sys_msg = f"You are an expert programmer. Write high-quality, commented code in {language}. Output ONLY the code block, no conversational text."
        res = api.chat_completions(model, description, messages=[{"role": "system", "content": sys_msg}])
        # Strip markdown code fences if present
        clean_res = re.sub(r'^```\w*\n', '', res)
        clean_res = re.sub(r'\n```$', '', clean_res)
        return (clean_res.strip(),)

class InternodeLLMSummarizer:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "text": ("STRING", {"multiline": True, "rows": 10}),
                "length": (["One Sentence", "Short Paragraph", "Bullet Points"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "summarize"
    CATEGORY = "Internode/LLM Text"

    def summarize(self, model, text, length, server_config=None):
        api = get_api(server_config)
        sys_msg = f"Summarize the following text. Format: {length}."
        res = api.chat_completions(model, text, messages=[{"role": "system", "content": sys_msg}])
        return (res,)

class InternodeLLMClassifier:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "text": ("STRING", {"multiline": True, "rows": 5}),
                "categories": ("STRING", {"default": "Positive, Negative, Neutral"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "classify"
    CATEGORY = "Internode/LLM Text"

    def classify(self, model, text, categories, server_config=None):
        api = get_api(server_config)
        sys_msg = f"Classify the input text into exactly one of these categories: [{categories}]. Output ONLY the category name."
        res = api.chat_completions(model, text, messages=[{"role": "system", "content": sys_msg}])
        return (res.strip(),)

class InternodeLLMPersona:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "text": ("STRING", {"multiline": True, "rows": 5}),
                "persona": ("STRING", {"default": "A pirate"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "rewrite"
    CATEGORY = "Internode/LLM Text"

    def rewrite(self, model, text, persona, server_config=None):
        api = get_api(server_config)
        sys_msg = f"Rewrite the user's text as if you were {persona}. Maintain the original meaning."
        res = api.chat_completions(model, text, messages=[{"role": "system", "content": sys_msg}])
        return (res,)

# --- Previous Extras ---

class InternodePromptEnricher:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "prompt": ("STRING", {"multiline": True, "rows": 5}),
                "style": ("STRING", {"default": "Cinematic, Detailed, 8k"}),
                "chaos": ("INT", {"default": 20, "min": 0, "max": 100}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "enrich"
    CATEGORY = "Internode/LLM Text"
    def enrich(self, model, prompt, style, chaos, server_config=None):
        api = get_api(server_config)
        sys_msg = f"You are a prompt engineer. Expand the prompt to be highly detailed in style '{style}'."
        if chaos > 80: sys_msg += " Be extremely creative."
        res = api.chat_completions(model, f"Prompt: {prompt}", messages=[{"role": "system", "content": sys_msg}])
        return (res.strip(),)

class InternodeImageCritic:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {"model": (get_cached_models(config["host"], config["api_key"]),), "image": ("IMAGE",)},
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("score", "critique")
    FUNCTION = "critique"
    CATEGORY = "Internode/LLM Vision"
    def critique(self, model, image, server_config=None):
        api = get_api(server_config)
        pil_image = tensor_to_pil(image[0])
        prompt = "Analyze this image. First line: 'SCORE: X' (1-10). Then critique."
        res = api.chat_completions(model, prompt, images=[pil_image])
        score = 5
        match = re.search(r"SCORE:\s*(\d+)", res, re.IGNORECASE)
        if match: score = max(1, min(10, int(match.group(1))))
        return (score, res)

class InternodeSmartRenamer:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {"model": (get_cached_models(config["host"], config["api_key"]),), "image": ("IMAGE",)},
            "optional": {"subfolder": ("STRING", {"default": "smart_sort"}), "server_config": ("OPENWEBUI_CONFIG",)}
        }
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "smart_save"
    CATEGORY = "Internode/LLM Vision"
    def smart_save(self, model, image, subfolder="smart_sort", server_config=None):
        api = get_api(server_config)
        out_dir = folder_paths.get_output_directory()
        full_path_base = os.path.join(out_dir, subfolder)
        os.makedirs(full_path_base, exist_ok=True)
        results = []
        
        # Name generation
        prompt = "Generate a short filename (lowercase, underscores, max 5 words) for this image. No extension."
        fname = api.chat_completions(model, prompt, images=[tensor_to_pil(image[0])]).strip()
        fname = re.sub(r'[\\/*?:"<>|.\n]', "", fname).replace(" ", "_")[:50] or "image"
        
        for i, img_tensor in enumerate(image):
            img = tensor_to_pil(img_tensor)
            cnt = 1
            suffix = f"_{i:02d}" if len(image) > 1 else ""
            while True:
                fn = f"{fname}{suffix}_{cnt:04d}.png"
                fp = os.path.join(full_path_base, fn)
                if not os.path.exists(fp): break
                cnt += 1
            img.save(fp, pnginfo=PngInfo(), compress_level=4)
            results.append({"filename": fn, "subfolder": subfolder, "type": "output"})
        return { "ui": { "images": results } }

# --- Registration ---

NODE_CLASS_MAPPINGS = {
    "Internode_OpenWebUIServerConfig": OpenWebUIServerConfig,
    "Internode_OpenWebUINode": OpenWebUINode,
    "Internode_OpenWebUIRefreshModels": OpenWebUIRefreshModels,
    # New Text Nodes
    "InternodeLLMPromptOptimizer": InternodeLLMPromptOptimizer,
    "InternodeLLMStyleTransfer": InternodeLLMStyleTransfer,
    "InternodeLLMStoryBrancher": InternodeLLMStoryBrancher,
    "InternodeLLMCharacterGen": InternodeLLMCharacterGen,
    "InternodeLLMDialogue": InternodeLLMDialogue,
    "InternodeLLMWorldBuilder": InternodeLLMWorldBuilder,
    "InternodeLLMCodeGen": InternodeLLMCodeGen,
    "InternodeLLMSummarizer": InternodeLLMSummarizer,
    "InternodeLLMClassifier": InternodeLLMClassifier,
    "InternodeLLMPersona": InternodeLLMPersona,
    # Vision Extras
    "InternodePromptEnricher": InternodePromptEnricher,
    "InternodeImageCritic": InternodeImageCritic,
    "InternodeSmartRenamer": InternodeSmartRenamer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Internode_OpenWebUIServerConfig": "OpenWebUI Server Config (Internode)",
    "Internode_OpenWebUINode": "OpenWebUI Unified (Internode)",
    "Internode_OpenWebUIRefreshModels": "OpenWebUI Refresh Models (Internode)",
    "InternodeLLMPromptOptimizer": "LLM Prompt Optimizer (Internode)",
    "InternodeLLMStyleTransfer": "LLM Style Transfer (Internode)",
    "InternodeLLMStoryBrancher": "LLM Story Brancher (Internode)",
    "InternodeLLMCharacterGen": "LLM Character Generator (Internode)",
    "InternodeLLMDialogue": "LLM Dialogue Writer (Internode)",
    "InternodeLLMWorldBuilder": "LLM World Builder (Internode)",
    "InternodeLLMCodeGen": "LLM Code Generator (Internode)",
    "InternodeLLMSummarizer": "LLM Text Summarizer (Internode)",
    "InternodeLLMClassifier": "LLM Text Classifier (Internode)",
    "InternodeLLMPersona": "LLM Persona Switcher (Internode)",
    "InternodePromptEnricher": "Prompt Enricher (Legacy) (Internode)",
    "InternodeImageCritic": "Image Critic (Vision) (Internode)",
    "InternodeSmartRenamer": "Smart Renamer & Save (Vision) (Internode)",
}