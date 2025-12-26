# ComfyUI/custom_nodes/ComfyUI-Internode/acestep_nodes.py
# VERSION: 3.0.1

import os
import sys
import threading
import folder_paths
import torch
import numpy as np

# Try imports
DiffusionPipeline = None
write_wav = None

try:
    from diffusers import DiffusionPipeline
    from scipy.io.wavfile import write as write_wav
except ImportError:
    print("#### Internode: Missing dependencies (diffusers/scipy). Please run install.py or use ComfyUI Manager to install.")

# --- Model Cache Management ---
_model_cache = {}
_cache_lock = threading.Lock()

def get_cached_model(model_name, device, dtype):
    """Get or load model with caching"""
    cache_key = f"{model_name}_{device}_{dtype}"
    
    with _cache_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]
    
    # Load outside lock to avoid blocking
    model = DiffusionPipeline.from_pretrained(
        model_name,
        torch_dtype=dtype,
        custom_pipeline="ACE-Step/ACE-Step-v1-music"
    )
    model.to(device)
    
    with _cache_lock:
        _model_cache[cache_key] = model
    
    return model

def clear_model_cache():
    """Clear all cached models to free memory"""
    global _model_cache
    with _cache_lock:
        for key in list(_model_cache.keys()):
            try:
                del _model_cache[key]
            except Exception:
                pass
        _model_cache = {}
    
    # Force garbage collection
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    print("#### Internode: ACE-Step model cache cleared")

# --- Node Logic ---

class InternodeAceStepLoader:
    """
    Loads ACE-Step model with caching support.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_name": (["ACE-Step/ACE-Step-v1-music"],),
                "device": (["auto", "cpu", "cuda"],),
            },
            "optional": {
                "clear_cache": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("ACE_MODEL",)
    FUNCTION = "load_model"
    CATEGORY = "Internode/ACE-Step"

    def load_model(self, model_name, device, clear_cache=False):
        if DiffusionPipeline is None:
            raise ImportError("Diffusers library not loaded. Please run 'install.py' inside the custom node folder or install requirements via ComfyUI Manager.")

        if clear_cache:
            clear_model_cache()

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        dtype = torch.float16 if device == "cuda" else torch.float32
        model = get_cached_model(model_name, device, dtype)
        
        return (model,)

class InternodeAceStepGenerator:
    """
    Generates audio using ACE-Step model.
    Phase 3 Update: Added Preview Mode.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ace_model": ("ACE_MODEL",),
                "preview_mode": ("BOOLEAN", {"default": False, "tooltip": "Overrides duration to 10s and steps to 20 for fast testing."}),
                "audio_duration": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 120.0, "step": 1.0, "display": "slider"}),
                "prompt": ("STRING", {"default": "funk, pop, soul, rock, melodic, guitar, drums, bass, keyboard, percussion, 105 BPM, energetic, upbeat, groovy, vibrant, dynamic", "multiline": False}),
                "lyrics": ("STRING", {"default": "[verse]\nNeon lights they flicker bright", "multiline": True}),
                "infer_step": ("INT", {"default": 60, "min": 1, "max": 200, "step": 1, "display": "slider"}),
                "guidance_scale": ("FLOAT", {"default": 15.0, "min": 0.0, "max": 30.0, "step": 0.1, "display": "slider"}),
                "scheduler_type": (["euler", "heun"],),
                "cfg_type": (["cfg", "apg", "cfg_star"],),
                "omega_scale": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 20.0, "step": 0.1, "display": "slider"}),
                "manual_seeds": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
                "guidance_interval": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "display": "slider"}),
                "guidance_interval_decay": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01, "display": "slider"}),
                "min_guidance_scale": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1, "display": "slider"}),
                "use_erg_tag": ("BOOLEAN", {"default": True}),
                "use_erg_lyric": ("BOOLEAN", {"default": False}),
                "use_erg_diffusion": ("BOOLEAN", {"default": True}),
                "oss_steps": ("INT", {"default": 0, "min": 0, "max": 100}),
                "guidance_scale_text": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.1, "display": "slider"}),
                "guidance_scale_lyric": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.1, "display": "slider"}),
                "lora_name_or_path": (["none", "ACE-Step/ACE-Step-v1-chinese-rap-LoRA"],),
                "filename_prefix": ("STRING", {"default": "ace-step-audio"}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio_output",)
    FUNCTION = "generate_audio"
    CATEGORY = "Internode/ACE-Step"
    OUTPUT_NODE = True

    def generate_audio(self, ace_model, preview_mode, audio_duration, prompt, lyrics, infer_step, guidance_scale, scheduler_type, cfg_type, omega_scale, manual_seeds, guidance_interval, guidance_interval_decay, min_guidance_scale, use_erg_tag, use_erg_lyric, use_erg_diffusion, oss_steps, guidance_scale_text, guidance_scale_lyric, lora_name_or_path, filename_prefix):
        
        # Phase 3: Preview Mode Logic
        if preview_mode:
            print("#### Internode: ACE-Step Preview Mode Enabled (10s @ 20 steps)")
            audio_duration = 10.0
            infer_step = 20
        
        if lora_name_or_path != "none":
            ace_model.load_lora_weights(lora_name_or_path)
        else:
            try:
                ace_model.unload_lora_weights()
            except Exception:
                pass

        generator = torch.Generator(device=ace_model.device)
        seed = manual_seeds if manual_seeds != -1 else generator.seed()
        generator.manual_seed(seed)
        
        audio_output = ace_model(
            prompt=prompt,
            lyrics=lyrics,
            duration=audio_duration,
            guidance_scale=guidance_scale,
            num_inference_steps=infer_step,
            generator=generator,
            scheduler_type=scheduler_type,
            cfg_type=cfg_type,
            omega_scale=omega_scale,
            guidance_interval=guidance_interval,
            guidance_interval_decay=guidance_interval_decay,
            min_guidance_scale=min_guidance_scale,
            use_erg_tag=use_erg_tag,
            use_erg_lyric=use_erg_lyric,
            use_erg_diffusion=use_erg_diffusion,
            oss_steps=oss_steps if oss_steps > 0 else None,
            guidance_scale_text=guidance_scale_text,
            guidance_scale_lyric=guidance_scale_lyric
        ).audios[0]

        # Get sample rate with fallback
        sample_rate = getattr(ace_model.config, 'sample_rate', 44100)

        # Generate unique filename
        full_output_folder, filename, counter, subfolder, filename_prefix_out = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir
        )
        
        file_name = f"{filename_prefix_out}_{counter:05d}.wav"
        file_path = os.path.join(full_output_folder, file_name)
        
        # Convert and save audio
        audio_int16 = (audio_output * 32767).astype('int16')

        if audio_int16.ndim == 2:
            audio_int16 = audio_int16.T
        
        if write_wav is not None:
            write_wav(file_path, rate=sample_rate, data=audio_int16)
            print(f"#### Internode: Audio saved to {file_path}")
        else:
            print("#### Internode Warning: scipy not available, audio not saved to file")

        # Convert to ComfyUI AUDIO format: {"waveform": tensor[batch, channels, samples], "sample_rate": int}
        if isinstance(audio_output, np.ndarray):
            audio_tensor = torch.from_numpy(audio_output).float()
        else:
            audio_tensor = audio_output.float()
        
        # Ensure shape is [batch, channels, samples]
        if audio_tensor.ndim == 1:
            audio_tensor = audio_tensor.unsqueeze(0).unsqueeze(0)
        elif audio_tensor.ndim == 2:
            if audio_tensor.shape[0] <= 2:
                audio_tensor = audio_tensor.unsqueeze(0)
            else:
                audio_tensor = audio_tensor.T.unsqueeze(0)

        return ({"waveform": audio_tensor, "sample_rate": sample_rate},)

class InternodeAceStepCacheClear:
    """
    Utility node to clear ACE-Step model cache.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "trigger": ("*",),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "clear"
    CATEGORY = "Internode/ACE-Step"
    OUTPUT_NODE = True

    def clear(self, trigger):
        clear_model_cache()
        return ("Cache cleared",)

# Export mappings
NODE_CLASS_MAPPINGS = {
    "InternodeAceStepLoader": InternodeAceStepLoader,
    "InternodeAceStepGenerator": InternodeAceStepGenerator,
    "InternodeAceStepCacheClear": InternodeAceStepCacheClear,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "InternodeAceStepLoader": "ACE-Step Loader (Internode)",
    "InternodeAceStepGenerator": "ACE-Step Generator (Internode)",
    "InternodeAceStepCacheClear": "ACE-Step Clear Cache (Internode)",
}