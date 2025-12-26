# ComfyUI/custom_nodes/ComfyUI-Internode/vst_nodes.py
import torch
import numpy as np
import os

try:
    from pedalboard import Pedalboard, VST3, load_plugin
    PEDALBOARD_AVAILABLE = True
except ImportError:
    PEDALBOARD_AVAILABLE = False

class InternodeVSTLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "vst_path": ("STRING", {"default": r"C:\Program Files\Common Files\VST3\YourPlugin.vst3"}),
                "dry_wet": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "process_vst"
    CATEGORY = "Internode/AudioFX"

    def process_vst(self, audio, vst_path, dry_wet):
        if not PEDALBOARD_AVAILABLE:
            print("#### Internode: 'pedalboard' not installed. VSTs disabled.")
            return (audio,)
            
        if not os.path.exists(vst_path) or not vst_path.endswith(".vst3"):
            print(f"#### Internode: VST3 not found at {vst_path}")
            return (audio,)

        waveform = audio["waveform"] # [batch, channels, samples]
        sample_rate = audio["sample_rate"]
        
        # Prepare Batch processing
        batch_out = []
        
        # Load Plugin
        try:
            plugin = load_plugin(vst_path)
        except Exception as e:
            print(f"#### Internode: Failed to load VST: {e}")
            return (audio,)

        for i in range(waveform.shape[0]):
            # Convert Torch -> Numpy (Channels, Samples)
            audio_np = waveform[i].cpu().numpy()
            
            # Pedalboard expects (Channels, Samples) float32
            # Process
            processed = plugin.process(audio_np, sample_rate)
            
            # Apply Dry/Wet manually
            if dry_wet < 1.0:
                processed = (processed * dry_wet) + (audio_np * (1.0 - dry_wet))
                
            batch_out.append(torch.from_numpy(processed))

        # Re-stack batch
        out_tensor = torch.stack(batch_out)
        
        return ({"waveform": out_tensor, "sample_rate": sample_rate},)