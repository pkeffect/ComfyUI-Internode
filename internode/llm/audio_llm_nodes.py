# ComfyUI/custom_nodes/ComfyUI-Internode/internode/llm/audio_llm_nodes.py
# VERSION: 3.4.0

import json
import re
from .openwebui_nodes import get_cached_models, load_config_file, get_api

class InternodeMusicPromptGen:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "genre": ("STRING", {"default": "Cinematic Score"}),
                "mood": ("STRING", {"default": "Epic, Tense, Building"}),
                "tempo": (["Slow", "Medium", "Fast", "Variable"],),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("music_prompt",)
    FUNCTION = "generate"
    CATEGORY = "Internode/LLM Audio"

    def generate(self, model, genre, mood, tempo, server_config=None):
        api = get_api(server_config)
        sys_msg = (
            "You are an expert Music Producer. Create a detailed text prompt for an AI Music Generator (like MusicGen or AudioLDM). "
            "Include instruments, bpm, key, and textural descriptors. Output ONLY the prompt."
        )
        user_msg = f"Genre: {genre}. Mood: {mood}. Tempo: {tempo}."
        res = api.chat_completions(model, user_msg, messages=[{"role": "system", "content": sys_msg}])
        return (res.strip(),)

class InternodeMusicStructureGen:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "style": ("STRING", {"default": "Pop Song"}),
                "length_seconds": ("INT", {"default": 180}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("structure_plan",)
    FUNCTION = "plan"
    CATEGORY = "Internode/LLM Audio"

    def plan(self, model, style, length_seconds, server_config=None):
        api = get_api(server_config)
        sys_msg = (
            "You are a Music Arranger. Create a timeline structure for a track. "
            "Format as a list of timestamps and sections (e.g., '0:00 - 0:30: Intro')."
        )
        user_msg = f"Style: {style}. Total Length: {length_seconds} seconds."
        res = api.chat_completions(model, user_msg, messages=[{"role": "system", "content": sys_msg}])
        return (res.strip(),)

class InternodeMusicCritic:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "description": ("STRING", {"multiline": True, "default": "A fast techno track with a weak bassline."}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("feedback",)
    FUNCTION = "critique"
    CATEGORY = "Internode/LLM Audio"

    def critique(self, model, description, server_config=None):
        api = get_api(server_config)
        sys_msg = (
            "You are a Mix Engineer. Read the description of the generated music/audio. "
            "Provide specific, technical suggestions to improve it (e.g., 'Boost 60Hz', 'Add sidechain compression')."
        )
        res = api.chat_completions(model, description, messages=[{"role": "system", "content": sys_msg}])
        return (res.strip(),)

class InternodeVocalScriptGen:
    @classmethod
    def INPUT_TYPES(s):
        config = load_config_file()
        return {
            "required": {
                "model": (get_cached_models(config["host"], config["api_key"]),),
                "topic": ("STRING", {"default": "Love and Loss"}),
                "singer_persona": ("STRING", {"default": "A soulful jazz singer"}),
            },
            "optional": {"server_config": ("OPENWEBUI_CONFIG",)}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("lyrics_script",)
    FUNCTION = "write_lyrics"
    CATEGORY = "Internode/LLM Audio"

    def write_lyrics(self, model, topic, singer_persona, server_config=None):
        api = get_api(server_config)
        sys_msg = (
            f"You are a Songwriter. Write a short verse and chorus about '{topic}' "
            f"suitable for {singer_persona}. Include bracketed performance notes like [breath], [vibrato]."
        )
        res = api.chat_completions(model, "Write lyrics.", messages=[{"role": "system", "content": sys_msg}])
        return (res.strip(),)