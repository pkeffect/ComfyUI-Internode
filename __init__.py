# ComfyUI/custom_nodes/ComfyUI-Internode/__init__.py
# VERSION: 3.0.7 (Restructured)

import sys
import subprocess
import os
import importlib.util
import importlib.metadata
import re

print("#### Internode: Initializing Node Pack VERSION 3.0.7 (Studio Structure)...")

# --- Dependency Management ---

def get_reqs_path():
    # Requirements are still in the root folder
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
        print("#### Internode: Installing missing packages...")
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            subprocess.check_call(cmd)
            print("#### Internode: Dependencies installed successfully.")
            importlib.invalidate_caches()
        except subprocess.CalledProcessError as e:
            print(f"#### Internode Error: Dependency installation failed.")
            print(f"#### Error details: {e}")

# Run dependency check
ensure_dependencies()

# --- Node Registration (Mapped to Sub-Directories) ---

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 1. LLM / OpenWebUI -> internode.llm
try:
    from .internode.llm.openwebui_nodes import NODE_CLASS_MAPPINGS as OWUI, NODE_DISPLAY_NAME_MAPPINGS as OWUI_N
    NODE_CLASS_MAPPINGS.update(OWUI)
    NODE_DISPLAY_NAME_MAPPINGS.update(OWUI_N)
except Exception as e:
    print(f"#### Internode Error (LLM Module): {e}")

# 2. Generative / ACE-Step -> internode.generative
try:
    from .internode.generative.acestep_nodes import NODE_CLASS_MAPPINGS as ACE, NODE_DISPLAY_NAME_MAPPINGS as ACE_N
    NODE_CLASS_MAPPINGS.update(ACE)
    NODE_DISPLAY_NAME_MAPPINGS.update(ACE_N)
except Exception as e:
    print(f"#### Internode Error (Generative Module): {e}")

# 3. Utilities -> internode.utils
try:
    from .internode.utils.markdown_node import InternodeMarkdownNote
    from .internode.utils.sticky_note import InternodeStickyNote
    
    NODE_CLASS_MAPPINGS["InternodeMarkdownNote"] = InternodeMarkdownNote
    NODE_CLASS_MAPPINGS["InternodeStickyNote"] = InternodeStickyNote
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMarkdownNote"] = "Markdown Note (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStickyNote"] = "Sticky Note (Internode)"
except Exception as e:
    print(f"#### Internode Error (Utils Module): {e}")

# 4. Analysis -> internode.analysis
try:
    from .internode.analysis.analysis_nodes import (
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
    print(f"#### Internode Error (Analysis Module): {e}")

# 5. VST -> internode.vst
try:
    from .internode.vst.vst_nodes import (
        InternodeVST3Effect, 
        InternodeVST3Instrument, 
        InternodeMidiLoader, 
        InternodeVST3Param, 
        InternodeVST3Info,
        InternodeVSTLoader
    )
    NODE_CLASS_MAPPINGS["InternodeVST3Effect"] = InternodeVST3Effect
    NODE_CLASS_MAPPINGS["InternodeVST3Instrument"] = InternodeVST3Instrument
    NODE_CLASS_MAPPINGS["InternodeMidiLoader"] = InternodeMidiLoader
    NODE_CLASS_MAPPINGS["InternodeVST3Param"] = InternodeVST3Param
    NODE_CLASS_MAPPINGS["InternodeVST3Info"] = InternodeVST3Info
    NODE_CLASS_MAPPINGS["InternodeVSTLoader"] = InternodeVSTLoader
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Effect"] = "VST3 Effect Processor (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Instrument"] = "VST3 Instrument (MIDI) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMidiLoader"] = "MIDI Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Param"] = "VST3 Parameter Automation (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Info"] = "VST3 Info & Param List (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVSTLoader"] = "VST3 Loader (Legacy/Simple)"
except Exception as e:
    print(f"#### Internode Error (VST Module): {e}")
    import traceback
    traceback.print_exc()

# 6. DSP & Tools -> internode.dsp
try:
    from .internode.dsp.audio_tools_nodes import InternodeSidechain, InternodeStemSplitter
    from .internode.dsp.dsp_nodes import (
        InternodeAudioMixer, InternodeAudioMixer8,
        InternodeAudioLoader, InternodeVideoLoader, InternodeImageLoader,
        InternodeAudioSaver
    )
    
    # Register DSP
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

    # Register Tools
    NODE_CLASS_MAPPINGS["InternodeSidechain"] = InternodeSidechain
    NODE_CLASS_MAPPINGS["InternodeStemSplitter"] = InternodeStemSplitter
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSidechain"] = "Audio Sidechain/Ducker (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStemSplitter"] = "Audio Stem Splitter (Demucs) (Internode)"

except Exception as e:
    print(f"#### Internode Error (DSP Module): {e}")
    import traceback
    traceback.print_exc()

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]