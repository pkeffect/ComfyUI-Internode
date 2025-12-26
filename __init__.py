# ComfyUI/custom_nodes/ComfyUI-Internode/__init__.py
# VERSION: 3.0.0

import importlib.util
import importlib.metadata
import os
import sys
import subprocess
import re

print("#### Internode: Initializing Node Pack VERSION 3.0.0...")

# --- Dependency Management ---

def get_reqs_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")

def normalize_package_name(name):
    return name.lower().replace("_", "-")

def is_installed(package):
    # Mapping for packages where pip name != import name or special handling needed
    # (Though importlib.metadata checks the PIP name, not the import name)
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

    # Packages to exclude from auto-install (let ComfyUI manage these)
    EXCLUDES = {"torch", "torchaudio", "torchvision", "comfyui"}
    
    missing = []
    
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Extract package name (handles "package>=1.0", "package==2.0", etc.)
            # Split by comparison operators
            pkg_name = re.split(r'[<>=!]', line)[0].strip()
            
            if normalize_package_name(pkg_name) in EXCLUDES:
                continue

            if not is_installed(pkg_name):
                missing.append(line)

    if missing:
        print(f"#### Internode: Found missing dependencies: {', '.join(missing)}")
        print("#### Internode: Installing missing packages... (This may take a moment)")
        
        try:
            # Construct pip install command
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            
            # Run pip
            subprocess.check_call(cmd)
            print("#### Internode: Dependencies installed successfully.")
            
            # Force refresh of import mechanism for newly installed packages
            importlib.invalidate_caches()
            
        except subprocess.CalledProcessError as e:
            print(f"#### Internode Error: Dependency installation failed. Please install manually from {req_file}")
            print(f"#### Error details: {e}")

# Run the check immediately
ensure_dependencies()

# --- Node Imports ---

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    # Now that dependencies are checked, these imports should succeed
    from .openwebui_nodes import NODE_CLASS_MAPPINGS as OWUI, NODE_DISPLAY_NAME_MAPPINGS as OWUI_N
    NODE_CLASS_MAPPINGS.update(OWUI)
    NODE_DISPLAY_NAME_MAPPINGS.update(OWUI_N)
except Exception as e:
    print(f"#### Internode Error (OpenWebUI): {e}")

try:
    from .acestep_nodes import NODE_CLASS_MAPPINGS as ACE, NODE_DISPLAY_NAME_MAPPINGS as ACE_N
    NODE_CLASS_MAPPINGS.update(ACE)
    NODE_DISPLAY_NAME_MAPPINGS.update(ACE_N)
except Exception as e:
    print(f"#### Internode Error (ACE-Step): {e}")

try:
    from .markdown_node import InternodeMarkdownNote
    NODE_CLASS_MAPPINGS["InternodeMarkdownNote"] = InternodeMarkdownNote
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMarkdownNote"] = "Markdown Note (Internode)"
except Exception as e:
    print(f"#### Internode Error (Markdown): {e}")

try:
    from .analysis_nodes import InternodeAudioAnalyzer
    NODE_CLASS_MAPPINGS["InternodeAudioAnalyzer"] = InternodeAudioAnalyzer
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioAnalyzer"] = "Audio Analyzer (Curves)"
except Exception as e:
    print(f"#### Internode Error (Analysis): {e}")

try:
    from .vst_nodes import InternodeVSTLoader
    NODE_CLASS_MAPPINGS["InternodeVSTLoader"] = InternodeVSTLoader
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVSTLoader"] = "VST3 Plugin Host"
except Exception as e:
    print(f"#### Internode Error (VST): {e}")

try:
    from .audio_tools_nodes import InternodeSidechain, InternodeStemSplitter
    NODE_CLASS_MAPPINGS["InternodeSidechain"] = InternodeSidechain
    NODE_CLASS_MAPPINGS["InternodeStemSplitter"] = InternodeStemSplitter
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSidechain"] = "Audio Sidechain/Ducker (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStemSplitter"] = "Audio Stem Splitter (Demucs) (Internode)"
except Exception as e:
    print(f"#### Internode Error (Tools): {e}")

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