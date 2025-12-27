# ComfyUI/custom_nodes/ComfyUI-Internode/__init__.py
# VERSION: 3.2.1

import importlib.util
import importlib.metadata
import os
import sys
import subprocess
import re

print("#### Internode: Initializing Node Pack VERSION 3.2.1...")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 1. OpenWebUI (LLM)
try:
    from .internode.llm.openwebui_nodes import NODE_CLASS_MAPPINGS as OWUI, NODE_DISPLAY_NAME_MAPPINGS as OWUI_N
    NODE_CLASS_MAPPINGS.update(OWUI)
    NODE_DISPLAY_NAME_MAPPINGS.update(OWUI_N)
except Exception as e:
    print(f"#### Internode Error (LLM): {e}")

# 2. ACE-Step (Generative)
try:
    from .internode.generative.acestep_nodes import NODE_CLASS_MAPPINGS as ACE, NODE_DISPLAY_NAME_MAPPINGS as ACE_N
    NODE_CLASS_MAPPINGS.update(ACE)
    NODE_DISPLAY_NAME_MAPPINGS.update(ACE_N)
except Exception as e:
    print(f"#### Internode Error (Generative): {e}")

# 3. Utilities (Utils)
try:
    from .internode.utils.markdown_node import InternodeMarkdownNote
    from .internode.utils.sticky_note import InternodeStickyNote
    from .internode.utils.asset_browser import InternodeAssetBrowser
    from .internode.utils.metadata_inspector import InternodeMetadataInspector
    
    NODE_CLASS_MAPPINGS["InternodeMarkdownNote"] = InternodeMarkdownNote
    NODE_CLASS_MAPPINGS["InternodeStickyNote"] = InternodeStickyNote
    NODE_CLASS_MAPPINGS["InternodeAssetBrowser"] = InternodeAssetBrowser
    NODE_CLASS_MAPPINGS["InternodeMetadataInspector"] = InternodeMetadataInspector
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMarkdownNote"] = "Markdown Note (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStickyNote"] = "Sticky Note (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAssetBrowser"] = "Asset Browser (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMetadataInspector"] = "Metadata Inspector (Internode)"
except Exception as e:
    print(f"#### Internode Error (Utils): {e}")

# 4. Analysis
try:
    from .internode.analysis.analysis_nodes import (
        InternodeAudioAnalyzer, InternodeAudioToKeyframes,
        InternodeSpectrogram, InternodeImageToAudio
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
    from .internode.vst.vst_nodes import (
        InternodeVST3Effect, InternodeVST3Instrument, InternodeMidiLoader,
        InternodeVST3Param, InternodeVST3Info, InternodeVSTLoader
    )
    from .internode.vst.studio_surface import InternodeStudioSurface

    NODE_CLASS_MAPPINGS["InternodeStudioSurface"] = InternodeStudioSurface
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStudioSurface"] = "Internode Studio Surface (UI)"
    
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
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVSTLoader"] = "VST3 Loader (Legacy)"
except Exception as e:
    print(f"#### Internode Error (VST): {e}")

# 6. DSP & Audio Tools
try:
    from .internode.dsp.audio_tools_nodes import InternodeSidechain, InternodeStemSplitter
    from .internode.dsp.dsp_nodes import (
        InternodeAudioMixer, InternodeAudioMixer8,
        InternodeAudioLoader, InternodeVideoLoader, InternodeImageLoader,
        InternodeAudioSaver
    )
    
    NODE_CLASS_MAPPINGS["InternodeSidechain"] = InternodeSidechain
    NODE_CLASS_MAPPINGS["InternodeStemSplitter"] = InternodeStemSplitter
    NODE_CLASS_MAPPINGS["InternodeAudioMixer"] = InternodeAudioMixer
    NODE_CLASS_MAPPINGS["InternodeAudioMixer8"] = InternodeAudioMixer8
    NODE_CLASS_MAPPINGS["InternodeAudioLoader"] = InternodeAudioLoader
    NODE_CLASS_MAPPINGS["InternodeVideoLoader"] = InternodeVideoLoader
    NODE_CLASS_MAPPINGS["InternodeImageLoader"] = InternodeImageLoader
    NODE_CLASS_MAPPINGS["InternodeAudioSaver"] = InternodeAudioSaver
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSidechain"] = "Audio Sidechain/Ducker (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStemSplitter"] = "Audio Stem Splitter (Demucs) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioMixer"] = "Audio Mixer 4-Ch + EQ (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioMixer8"] = "Audio Mixer 8-Ch + EQ (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioLoader"] = "Audio Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVideoLoader"] = "Video Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeImageLoader"] = "Image Loader (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioSaver"] = "Audio Saver (Internode)"
except Exception as e:
    print(f"#### Internode Error (DSP): {e}")

# 7. Video FX
try:
    from .internode.video_fx.universal_player import InternodeUniversalPlayer
    from .internode.video_fx.ab_comparator import InternodeABComparator
    from .internode.video_fx.post_production_nodes import (
        InternodeColorGrade, InternodeFilmGrain, InternodeGlitch, InternodeSpeedRamp
    )
    
    NODE_CLASS_MAPPINGS["InternodeUniversalPlayer"] = InternodeUniversalPlayer
    NODE_CLASS_MAPPINGS["InternodeABComparator"] = InternodeABComparator
    NODE_CLASS_MAPPINGS["InternodeColorGrade"] = InternodeColorGrade
    NODE_CLASS_MAPPINGS["InternodeFilmGrain"] = InternodeFilmGrain
    NODE_CLASS_MAPPINGS["InternodeGlitch"] = InternodeGlitch
    NODE_CLASS_MAPPINGS["InternodeSpeedRamp"] = InternodeSpeedRamp
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeUniversalPlayer"] = "Universal Media Player (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeABComparator"] = "A/B Comparator (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeColorGrade"] = "Color Grade 3-Way (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeFilmGrain"] = "Film Grain / Overlay (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeGlitch"] = "Datamosh / Glitch (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSpeedRamp"] = "Frame Speed Ramp (Internode)"
except Exception as e:
    print(f"#### Internode Error (VideoFX): {e}")

# 8. Control & Logic
try:
    from .internode.control.control_nodes import NODE_CLASS_MAPPINGS as CONTROL, NODE_DISPLAY_NAME_MAPPINGS as CONTROL_N
    NODE_CLASS_MAPPINGS.update(CONTROL)
    NODE_DISPLAY_NAME_MAPPINGS.update(CONTROL_N)
except Exception as e:
    print(f"#### Internode Error (Control): {e}")


WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]