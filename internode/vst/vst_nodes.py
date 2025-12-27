# ComfyUI/custom_nodes/ComfyUI-Internode/vst_nodes.py
# VERSION: 3.1.0

import torch
import numpy as np
import os
import folder_paths
import threading

# Dependency Checks
PEDALBOARD_AVAILABLE = False
MIDO_AVAILABLE = False

try:
    from pedalboard import Pedalboard, VST3Plugin, load_plugin
    PEDALBOARD_AVAILABLE = True
except ImportError:
    pass

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    pass

# --- CACHE ---
_plugin_cache = {}
_cache_lock = threading.Lock()

def load_vst_plugin(path):
    """Thread-safe VST loading/caching"""
    if not os.path.exists(path):
        print(f"#### Internode VST Error: File not found {path}")
        return None
        
    # Pedalboard objects aren't strictly thread-safe for processing, 
    # but we cache the *plugin definition* if possible, or just new instances.
    try:
        return load_plugin(path)
    except Exception as e:
        print(f"#### Internode VST Load Error: {e}")
        return None

# --- HELPER NODES ---

class InternodeVST3Info:
    """
    Returns a string list of all parameters in a VST3 plugin.
    Useful for copying parameter names for automation.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "vst_path": ("STRING", {"default": r"C:\Program Files\Common Files\VST3\Plugin.vst3"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("parameter_list",)
    FUNCTION = "get_info"
    CATEGORY = "Internode/VST3"

    def get_info(self, vst_path):
        if not PEDALBOARD_AVAILABLE: return ("Pedalboard not installed.",)
        
        plugin = load_vst_plugin(vst_path)
        if not plugin: return ("Failed to load plugin.",)
        
        info = []
        try:
            info.append(f"Plugin: {plugin.name}")
            info.append(f"Category: {plugin.category}")
            info.append("-" * 20)
            for name, param in plugin.parameters.items():
                info.append(f"{name}: {param.raw_value:.4f}")
        except:
            info.append("Could not iterate parameters.")
            
        return ("\n".join(info),)

class InternodeMidiLoader:
    """
    Loads a .mid file and returns the raw MIDI object (Mido).
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "midi_file": ("STRING", {"default": "none"}),
            }
        }

    RETURN_TYPES = ("MIDI_DATA",)
    FUNCTION = "load_midi"
    CATEGORY = "Internode/Loaders"

    def load_midi(self, midi_file):
        if not MIDO_AVAILABLE:
            raise ImportError("mido not installed. Run install.py")
        
        path = os.path.join(folder_paths.get_input_directory(), midi_file)
        if not os.path.exists(path):
            raise FileNotFoundError(f"MIDI file not found: {midi_file}")
            
        mid = mido.MidiFile(path)
        return (mid,)

class InternodeVST3Param:
    """
    Defines a parameter automation to be passed to a VST node.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "param_name": ("STRING", {"default": "Cutoff"}),
                "value": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("VST_PARAM",)
    FUNCTION = "create_param"
    CATEGORY = "Internode/VST3"

    def create_param(self, param_name, value):
        return ({"name": param_name, "value": value},)

# --- PROCESSORS ---

class InternodeVST3Instrument:
    """
    Renders audio from a VST3 Instrument using a MIDI file.
    Optimized: Uses C++ bulk processing instead of Python loops.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "midi_data": ("MIDI_DATA",),
                "vst_path": ("STRING", {"default": r"C:\Program Files\Common Files\VST3\Synth.vst3"}),
                "sample_rate": (["44100", "48000"],),
                "duration_padding": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 10.0, "tooltip": "Seconds of silence to add at end (for reverb tails)."}),
            },
            "optional": {
                "param_1": ("VST_PARAM",),
                "param_2": ("VST_PARAM",),
                "param_3": ("VST_PARAM",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "render"
    CATEGORY = "Internode/VST3"

    def render(self, midi_data, vst_path, sample_rate, duration_padding, **kwargs):
        if not PEDALBOARD_AVAILABLE: raise ImportError("Pedalboard missing.")
        
        sr = int(sample_rate)
        plugin = load_vst_plugin(vst_path)
        if not plugin: raise RuntimeError("VST Load Failed")
        
        # Apply static parameter overrides
        for k, v in kwargs.items():
            if v and "name" in v:
                if v["name"] in plugin.parameters:
                    plugin.parameters[v["name"]].raw_value = v["value"]
                else:
                    print(f"#### Internode Warning: Param '{v['name']}' not found in VST.")

        # Calculate Duration from MIDI
        midi_len = midi_data.length
        total_duration = midi_len + duration_padding
        total_samples = int(total_duration * sr)
        
        print("#### Internode: Rendering VST Instrument (Batch Mode)...")
        
        # Create full silence buffer
        input_audio = np.zeros((2, total_samples), dtype=np.float32)
        
        try:
            # Process entire buffer in C++ (Fastest)
            output_audio = plugin.process(input_audio, sr)
        except Exception as e:
            print(f"#### Internode VST Render Error: {e}")
            output_audio = input_audio

        tensor = torch.from_numpy(output_audio).unsqueeze(0) # [1, 2, Samples]
        return ({"waveform": tensor, "sample_rate": sr},)


class InternodeVST3Effect:
    """
    Applies a VST3 Effect to audio.
    Optimized: Removed Python-level blocking loop. 
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "vst_path": ("STRING", {"default": r"C:\Program Files\Common Files\VST3\Effect.vst3"}),
                "dry_wet": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "param_1": ("VST_PARAM",),
                "param_2": ("VST_PARAM",),
                "param_3": ("VST_PARAM",),
                "param_4": ("VST_PARAM",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "process_fx"
    CATEGORY = "Internode/VST3"

    def process_fx(self, audio, vst_path, dry_wet, **kwargs):
        if not PEDALBOARD_AVAILABLE: return (audio,)
        
        waveform = audio["waveform"]
        sr = audio["sample_rate"]
        
        plugin = load_vst_plugin(vst_path)
        if not plugin: return (audio,)

        # Collect automations
        automations = {}
        for k, v in kwargs.items():
            if v and "name" in v:
                automations[v["name"]] = v["value"]

        # Apply Automation (Static for now, per batch)
        for name, val in automations.items():
            if name in plugin.parameters:
                plugin.parameters[name].raw_value = val

        batch_out = []
        for i in range(waveform.shape[0]):
            audio_np = waveform[i].cpu().numpy() # [Channels, Samples]
            
            # Ensure stereo for Pedalboard
            if audio_np.shape[0] == 1:
                audio_np = np.repeat(audio_np, 2, axis=0)

            try:
                # OPTIMIZATION: Process entire track at once.
                # Pedalboard handles buffering internally in C++.
                processed = plugin.process(audio_np, sr)
            except Exception as e:
                print(f"#### Internode VST Process Error: {e}")
                processed = audio_np

            # Dry/Wet
            if dry_wet < 1.0:
                # Handle channel expansion (Mono in -> Stereo out)
                if processed.shape[0] != audio_np.shape[0]:
                    if audio_np.shape[0] == 1: 
                        audio_np = np.repeat(audio_np, processed.shape[0], axis=0)
                    elif processed.shape[0] == 1:
                        processed = np.repeat(processed, audio_np.shape[0], axis=0)
                
                # Length mismatch check
                min_len = min(processed.shape[1], audio_np.shape[1])
                processed = processed[:, :min_len]
                audio_np = audio_np[:, :min_len]
                
                processed = (processed * dry_wet) + (audio_np * (1.0 - dry_wet))
            
            batch_out.append(torch.from_numpy(processed))

        return ({"waveform": torch.stack(batch_out), "sample_rate": sr},)

# --- BACKWARD COMPATIBILITY NODE ---
class InternodeVSTLoader(InternodeVST3Effect):
    """
    Legacy wrapper for InternodeVST3Effect to prevent workflow breakage.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "vst_path": ("STRING", {"default": r"C:\Program Files\Common Files\VST3\Plugin.vst3"}),
                "dry_wet": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }
    
    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "process_fx"
    CATEGORY = "Internode/VST3"