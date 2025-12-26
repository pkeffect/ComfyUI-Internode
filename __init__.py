# ComfyUI/custom_nodes/ComfyUI-Internode/__init__.py
# VERSION: 3.0.6

import importlib.util
import importlib.metadata
import os
import sys
import subprocess
import re

print("#### Internode: Initializing Node Pack VERSION 3.0.6...")

# --- Dependency Management ---

def get_reqs_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")

def normalize_package_name(name):
    return name.lower().replace("_", "-")

def is_installed(package):
    try:
        importlib.metadata.distribution(package)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False

def ensure_dependencies():
    req_file = get_reqs_path()
    if not os.path.exists(req_file):
        print(f"#### Internode: requirements.txt not found at {req_file}")
        return

    EXCLUDES = {"torch", "torchaudio", "torchvision", "comfyui"}
    missing = []
    
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            pkg_name = re.split(r'[<>=!]', line)[0].strip()
            if normalize_package_name(pkg_name) in EXCLUDES: continue
            if not is_installed(pkg_name): missing.append(line)

    if missing:
        print(f"#### Internode: Found missing dependencies: {', '.join(missing)}")
        print("#### Internode: Installing missing packages... (This may take a moment)")
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            subprocess.check_call(cmd)
            print("#### Internode: Dependencies installed successfully.")
            importlib.invalidate_caches()
        except subprocess.CalledProcessError as e:
            print(f"#### Internode Error: Dependency installation failed. Please install manually from {req_file}")
            print(f"#### Error details: {e}")

ensure_dependencies()

# --- Node Imports ---

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 1. OpenWebUI
try:
    from .openwebui_nodes import NODE_CLASS_MAPPINGS as OWUI, NODE_DISPLAY_NAME_MAPPINGS as OWUI_N
    NODE_CLASS_MAPPINGS.update(OWUI)
    NODE_DISPLAY_NAME_MAPPINGS.update(OWUI_N)
except Exception as e:
    print(f"#### Internode Error (OpenWebUI): {e}")

# 2. ACE-Step Music
try:
    from .acestep_nodes import NODE_CLASS_MAPPINGS as ACE, NODE_DISPLAY_NAME_MAPPINGS as ACE_N
    NODE_CLASS_MAPPINGS.update(ACE)
    NODE_DISPLAY_NAME_MAPPINGS.update(ACE_N)
except Exception as e:
    print(f"#### Internode Error (ACE-Step): {e}")

# 3. Utilities (Markdown)
try:
    from .markdown_node import InternodeMarkdownNote
    NODE_CLASS_MAPPINGS["InternodeMarkdownNote"] = InternodeMarkdownNote
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMarkdownNote"] = "Markdown Note (Internode)"
except Exception as e:
    print(f"#### Internode Error (Markdown): {e}")

# 4. Analysis & Reactivity & Spectral
try:
    from .analysis_nodes import (
        InternodeAudioAnalyzer, 
        InternodeAudioToKeyframes,
        InternodeSpectrogram,
        InternodeImageToAudio
    )
    NODE_CLASS_MAPPINGS["InternodeAudioAnalyzer"] = InternodeAudioAnalyzer
    NODE_CLASS_MAPPINGS["InternodeAudioToKeyframes"] = InternodeAudioToKeyframes
    NODE_CLASS_MAPPINGS["InternodeSpectrogram"] = InternodeSpectrogram
    NODE_CLASS_MAPPINGS["InternodeImageToAudio"] = InternodeImageToAudio
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioAnalyzer"] = "Audio Analyzer (Curves)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioToKeyframes"] = "Audio to Keyframes (React)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSpectrogram"] = "Audio to Spectrogram (Image)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeImageToAudio"] = "Spectrogram to Audio (Reconstruct)"
except Exception as e:
    print(f"#### Internode Error (Analysis): {e}")

# 5. VST3 Host
try:
    from .vst_nodes import (
        InternodeVST3Effect, 
        InternodeVST3Instrument, 
        InternodeMidiLoader, 
        InternodeVST3Param, 
        InternodeVST3Info,
        InternodeVSTLoader # RESTORED
    )
    NODE_CLASS_MAPPINGS["InternodeVST3Effect"] = InternodeVST3Effect
    NODE_CLASS_MAPPINGS["InternodeVST3Instrument"] = InternodeVST3Instrument
    NODE_CLASS_MAPPINGS["InternodeMidiLoader"] = InternodeMidiLoader
    NODE_CLASS_MAPPINGS["InternodeVST3Param"] = InternodeVST3Param
    NODE_CLASS_MAPPINGS["InternodeVST3Info"] = InternodeVST3Info
    NODE_CLASS_MAPPINGS["InternodeVSTLoader"] = InternodeVSTLoader # RESTORED
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Effect"] = "VST3 Effect Processor (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Instrument"] = "VST3 Instrument (MIDI) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMidiLoader"] = "MIDI Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Param"] = "VST3 Parameter Automation (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Info"] = "VST3 Info & Param List (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVSTLoader"] = "VST3 Loader (Legacy/Simple)" # RESTORED
except Exception as e:
    print(f"#### Internode Error (VST/MIDI): {e}")
    import traceback
    traceback.print_exc()

# 6. Audio Tools
try:
    from .audio_tools_nodes import InternodeSidechain, InternodeStemSplitter
    NODE_CLASS_MAPPINGS["InternodeSidechain"] = InternodeSidechain
    NODE_CLASS_MAPPINGS["InternodeStemSplitter"] = InternodeStemSplitter
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSidechain"] = "Audio Sidechain/Ducker (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStemSplitter"] = "Audio Stem Splitter (Demucs) (Internode)"
except Exception as e:
    print(f"#### Internode Error (Tools): {e}")

# 7. DSP & Media
try:
    from .dsp_nodes import (
        InternodeAudioMixer, InternodeAudioMixer8,
        InternodeAudioLoader, InternodeVideoLoader, InternodeImageLoader,
        InternodeAudioSaver
    )
    NODE_CLASS_MAPPINGS["InternodeAudioMixer"] = InternodeAudioMixer
    NODE_CLASS_MAPPINGS["InternodeAudioMixer8"] = InternodeAudioMixer8
    NODE_CLASS_MAPPINGS["InternodeAudioLoader"] = InternodeAudioLoader
    NODE_CLASS_MAPPINGS["InternodeVideoLoader"] = InternodeVideoLoader
    NODE_CLASS_MAPPINGS["InternodeImageLoader"] = InternodeImageLoader
    NODE_CLASS_MAPPINGS["InternodeAudioSaver"] = InternodeAudioSaver
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioMixer"] = "Audio Mixer 4-Ch + EQ (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioMixer8"] = "Audio Mixer 8-Ch + EQ (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioLoader"] = "Audio Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVideoLoader"] = "Video Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeImageLoader"] = "Image Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioSaver"] = "Audio Saver (Internode)"
except Exception as e:
    print(f"#### Internode Error (Media/DSP): {e}")
    import traceback
    traceback.print_exc()

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]