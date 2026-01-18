# ComfyUI/custom_nodes/ComfyUI-Internode/__init__.py
# VERSION: 3.6.0

import importlib.util
import importlib.metadata
import os
import sys

print("#### Internode: Initializing Node Pack VERSION 3.6.0...")

# --- Main Registry ---
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# ==============================================================================
# 1. LLM & TEXT GENERATION (OpenWebUI)
# ==============================================================================
try:
    from .internode.llm.openwebui_nodes import NODE_CLASS_MAPPINGS as LLM_CORE, NODE_DISPLAY_NAME_MAPPINGS as LLM_CORE_N
    NODE_CLASS_MAPPINGS.update(LLM_CORE)
    NODE_DISPLAY_NAME_MAPPINGS.update(LLM_CORE_N)
    
    # Standardize Names
    NODE_DISPLAY_NAME_MAPPINGS["Internode_OpenWebUIServerConfig"] = "OpenWebUI Server Config (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["Internode_OpenWebUINode"] = "OpenWebUI Unified Chat (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["Internode_OpenWebUIRefreshModels"] = "OpenWebUI Refresh Models (Internode)"
    
    # Text Intelligence
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMPromptOptimizer"] = "LLM Prompt Optimizer (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMStyleTransfer"] = "LLM Style Transfer (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMStoryBrancher"] = "LLM Story Brancher (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMCharacterGen"] = "LLM Character Generator (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMDialogue"] = "LLM Dialogue Writer (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMWorldBuilder"] = "LLM World Builder (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMCodeGen"] = "LLM Code Generator (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMSummarizer"] = "LLM Summarizer (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMClassifier"] = "LLM Classifier (Text) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeLLMPersona"] = "LLM Persona Switcher (Text) (Internode)"
except Exception as e:
    print(f"#### Internode Error (LLM Core): {e}")

# ==============================================================================
# 2. VISION INTELLIGENCE (LLM-Based)
# ==============================================================================
try:
    from .internode.llm.vision_nodes import (
        InternodeVisionRefiner, InternodeVisionStyleMatcher, 
        InternodeVisionContentExtractor, InternodeVisionInpaintPrompter
    )
    # Import legacy/utility vision nodes from openwebui_nodes if they exist there
    from .internode.llm.openwebui_nodes import (
        InternodePromptEnricher, InternodeImageCritic, InternodeSmartRenamer
    )

    NODE_CLASS_MAPPINGS["InternodeVisionRefiner"] = InternodeVisionRefiner
    NODE_CLASS_MAPPINGS["InternodeVisionStyleMatcher"] = InternodeVisionStyleMatcher
    NODE_CLASS_MAPPINGS["InternodeVisionContentExtractor"] = InternodeVisionContentExtractor
    NODE_CLASS_MAPPINGS["InternodeVisionInpaintPrompter"] = InternodeVisionInpaintPrompter
    NODE_CLASS_MAPPINGS["InternodePromptEnricher"] = InternodePromptEnricher
    NODE_CLASS_MAPPINGS["InternodeImageCritic"] = InternodeImageCritic
    NODE_CLASS_MAPPINGS["InternodeSmartRenamer"] = InternodeSmartRenamer

    NODE_DISPLAY_NAME_MAPPINGS["InternodeVisionRefiner"] = "Image Prompt Refiner (Vision) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVisionStyleMatcher"] = "Image Style Matcher (Vision) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVisionContentExtractor"] = "Image Content Extractor (Vision) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVisionInpaintPrompter"] = "Inpaint Prompt Generator (Vision) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodePromptEnricher"] = "Prompt Enricher (Legacy) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeImageCritic"] = "Image Critic (Vision) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSmartRenamer"] = "Smart Renamer & Save (Vision) (Internode)"
except Exception as e:
    print(f"#### Internode Error (Vision LLM): {e}")

# ==============================================================================
# 3. VIDEO INTELLIGENCE (LLM-Based)
# ==============================================================================
try:
    from .internode.llm.video_llm_nodes import (
        InternodeVideoNarrator, InternodeAIColorist, 
        InternodeVideoSceneDescriptor, InternodeVideoTrackerPrompt
    )

    NODE_CLASS_MAPPINGS["InternodeVideoNarrator"] = InternodeVideoNarrator
    NODE_CLASS_MAPPINGS["InternodeAIColorist"] = InternodeAIColorist
    NODE_CLASS_MAPPINGS["InternodeVideoSceneDescriptor"] = InternodeVideoSceneDescriptor
    NODE_CLASS_MAPPINGS["InternodeVideoTrackerPrompt"] = InternodeVideoTrackerPrompt

    NODE_DISPLAY_NAME_MAPPINGS["InternodeVideoNarrator"] = "Video Scene Narrator (LLM) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAIColorist"] = "AI Video Colorist (LLM) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVideoSceneDescriptor"] = "Video Scene Descriptor (LLM) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVideoTrackerPrompt"] = "Video Object Tracker (LLM) (Internode)"
except Exception as e:
    print(f"#### Internode Error (Video LLM): {e}")

# ==============================================================================
# 4. GENERATIVE AUDIO (ACE-Step)
# ==============================================================================
try:
    from .internode.generative.acestep_nodes import NODE_CLASS_MAPPINGS as ACE, NODE_DISPLAY_NAME_MAPPINGS as ACE_N
    NODE_CLASS_MAPPINGS.update(ACE)
    NODE_DISPLAY_NAME_MAPPINGS.update(ACE_N)
except Exception as e:
    print(f"#### Internode Error (Generative Audio): {e}")

# ==============================================================================
# 5. AUDIO DSP & MIXING
# ==============================================================================
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
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSidechain"] = "Audio Sidechain/Ducker (DSP) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStemSplitter"] = "Audio Stem Splitter (Demucs) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioMixer"] = "Audio Mixer 4-Ch + EQ (DSP) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioMixer8"] = "Audio Mixer 8-Ch + EQ (DSP) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioLoader"] = "Audio Loader (IO) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVideoLoader"] = "Video Loader (IO) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeImageLoader"] = "Image Loader (IO) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioSaver"] = "Audio Saver (IO) (Internode)"
except Exception as e:
    print(f"#### Internode Error (DSP): {e}")

# ==============================================================================
# 6. VST3 & STUDIO INSTRUMENTS
# ==============================================================================
try:
    from .internode.vst.vst_nodes import (
        InternodeVST3Effect, InternodeVST3Instrument, InternodeMidiLoader,
        InternodeVST3Param, InternodeVST3Info, InternodeVSTLoader
    )
    from .internode.vst.studio_surface import InternodeStudioSurface
    
    # REMOVED: from .internode.vst.studio_nodes import ...

    # Existing VST Mappings
    NODE_CLASS_MAPPINGS["InternodeStudioSurface"] = InternodeStudioSurface
    NODE_CLASS_MAPPINGS["InternodeVST3Effect"] = InternodeVST3Effect
    NODE_CLASS_MAPPINGS["InternodeVST3Instrument"] = InternodeVST3Instrument
    NODE_CLASS_MAPPINGS["InternodeMidiLoader"] = InternodeMidiLoader
    NODE_CLASS_MAPPINGS["InternodeVST3Param"] = InternodeVST3Param
    NODE_CLASS_MAPPINGS["InternodeVST3Info"] = InternodeVST3Info
    NODE_CLASS_MAPPINGS["InternodeVSTLoader"] = InternodeVSTLoader
    
    # REMOVED: NODE_CLASS_MAPPINGS["InternodeDrumMachine"] ...
    # REMOVED: NODE_CLASS_MAPPINGS["InternodeSampler"] ...
    
    # Display Names
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStudioSurface"] = "Internode Studio Surface (UI)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Effect"] = "VST3 Effect Processor (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Instrument"] = "VST3 Instrument (MIDI) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMidiLoader"] = "MIDI Loader (IO) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Param"] = "VST3 Parameter Automation (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVST3Info"] = "VST3 Info & Param List (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVSTLoader"] = "VST3 Loader (Legacy) (Internode)"
    
    # REMOVED: NODE_DISPLAY_NAME_MAPPINGS["InternodeDrumMachine"] ...
    # REMOVED: NODE_DISPLAY_NAME_MAPPINGS["InternodeSampler"] ...

except Exception as e:
    print(f"#### Internode Error (Studio/VST): {e}")

# ==============================================================================
# 7. AUDIO ANALYSIS
# ==============================================================================
try:
    from .internode.analysis.analysis_nodes import (
        InternodeAudioAnalyzer, InternodeAudioToKeyframes,
        InternodeSpectrogram, InternodeImageToAudio
    )
    NODE_CLASS_MAPPINGS["InternodeAudioAnalyzer"] = InternodeAudioAnalyzer
    NODE_CLASS_MAPPINGS["InternodeAudioToKeyframes"] = InternodeAudioToKeyframes
    NODE_CLASS_MAPPINGS["InternodeSpectrogram"] = InternodeSpectrogram
    NODE_CLASS_MAPPINGS["InternodeImageToAudio"] = InternodeImageToAudio
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioAnalyzer"] = "Audio Analyzer (Curves) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioToKeyframes"] = "Audio to Keyframes (React) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSpectrogram"] = "Audio to Spectrogram (Image) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeImageToAudio"] = "Spectrogram to Audio (Reconstruct) (Internode)"
except Exception as e:
    print(f"#### Internode Error (Analysis): {e}")

# ==============================================================================
# 8. VIDEO FX & POST-PRODUCTION
# ==============================================================================
try:
    from .internode.video_fx.universal_player import InternodeUniversalPlayer
    from .internode.video_fx.ab_comparator import InternodeABComparator
    from .internode.video_fx.post_production_nodes import (
        InternodeColorGrade, InternodeFilmGrain, InternodeGlitch, InternodeSpeedRamp
    )
    from .internode.video_fx.video_smart_nodes import (
        InternodeOpticalFlowInterpolator, InternodeMotionGlitch, InternodeBatchStyleTransfer
    )
    
    NODE_CLASS_MAPPINGS["InternodeUniversalPlayer"] = InternodeUniversalPlayer
    NODE_CLASS_MAPPINGS["InternodeABComparator"] = InternodeABComparator
    NODE_CLASS_MAPPINGS["InternodeColorGrade"] = InternodeColorGrade
    NODE_CLASS_MAPPINGS["InternodeFilmGrain"] = InternodeFilmGrain
    NODE_CLASS_MAPPINGS["InternodeGlitch"] = InternodeGlitch
    NODE_CLASS_MAPPINGS["InternodeSpeedRamp"] = InternodeSpeedRamp
    NODE_CLASS_MAPPINGS["InternodeOpticalFlowInterpolator"] = InternodeOpticalFlowInterpolator
    NODE_CLASS_MAPPINGS["InternodeMotionGlitch"] = InternodeMotionGlitch
    NODE_CLASS_MAPPINGS["InternodeBatchStyleTransfer"] = InternodeBatchStyleTransfer
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeUniversalPlayer"] = "Universal Media Player (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeABComparator"] = "A/B Comparator (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeColorGrade"] = "Color Grade 3-Way (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeFilmGrain"] = "Film Grain / Overlay (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeGlitch"] = "Datamosh / Glitch (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSpeedRamp"] = "Frame Speed Ramp (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeOpticalFlowInterpolator"] = "Video Frame Interpolator (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMotionGlitch"] = "Motion Vector Glitch (VideoFX) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeBatchStyleTransfer"] = "Batch Style Transfer (VideoFX) (Internode)"
except Exception as e:
    print(f"#### Internode Error (VideoFX): {e}")

# ==============================================================================
# 9. IMAGE FX
# ==============================================================================
try:
    from .internode.image_fx import NODE_CLASS_MAPPINGS as IMG, NODE_DISPLAY_NAME_MAPPINGS as IMG_N
    NODE_CLASS_MAPPINGS.update(IMG)
    NODE_DISPLAY_NAME_MAPPINGS.update(IMG_N)
except Exception as e:
    print(f"#### Internode Error (ImageFX): {e}")

# ==============================================================================
# 10. CONTROL & LOGIC
# ==============================================================================
try:
    from .internode.control.control_nodes import NODE_CLASS_MAPPINGS as CONTROL, NODE_DISPLAY_NAME_MAPPINGS as CONTROL_N
    NODE_CLASS_MAPPINGS.update(CONTROL)
    NODE_DISPLAY_NAME_MAPPINGS.update(CONTROL_N)
except Exception as e:
    print(f"#### Internode Error (Control): {e}")

# ==============================================================================
# 11. UTILITIES
# ==============================================================================
try:
    from .internode.utils.markdown_node import InternodeMarkdownNote
    from .internode.utils.sticky_note import InternodeStickyNote
    from .internode.utils.asset_browser import InternodeAssetBrowser
    from .internode.utils.metadata_inspector import InternodeMetadataInspector
    
    NODE_CLASS_MAPPINGS["InternodeMarkdownNote"] = InternodeMarkdownNote
    NODE_CLASS_MAPPINGS["InternodeStickyNote"] = InternodeStickyNote
    NODE_CLASS_MAPPINGS["InternodeAssetBrowser"] = InternodeAssetBrowser
    NODE_CLASS_MAPPINGS["InternodeMetadataInspector"] = InternodeMetadataInspector
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMarkdownNote"] = "Markdown Note (Utils) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeStickyNote"] = "Sticky Note (Utils) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAssetBrowser"] = "Asset Browser (Utils) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMetadataInspector"] = "Metadata Inspector (Utils) (Internode)"
except Exception as e:
    print(f"#### Internode Error (Utils): {e}")

# ==============================================================================
# 12. AUDIO INTELLIGENCE & GENERATION (NEW)
# ==============================================================================
try:
    from .internode.llm.audio_llm_nodes import (
        InternodeMusicPromptGen, InternodeMusicStructureGen, 
        InternodeMusicCritic, InternodeVocalScriptGen
    )
    from .internode.generative.audio_gen_nodes import (
        InternodeSimpleSoundGen, InternodeAmbienceGen, InternodeAudioStyleTransferDSP
    )

    NODE_CLASS_MAPPINGS["InternodeMusicPromptGen"] = InternodeMusicPromptGen
    NODE_CLASS_MAPPINGS["InternodeMusicStructureGen"] = InternodeMusicStructureGen
    NODE_CLASS_MAPPINGS["InternodeMusicCritic"] = InternodeMusicCritic
    NODE_CLASS_MAPPINGS["InternodeVocalScriptGen"] = InternodeVocalScriptGen
    
    NODE_CLASS_MAPPINGS["InternodeSimpleSoundGen"] = InternodeSimpleSoundGen
    NODE_CLASS_MAPPINGS["InternodeAmbienceGen"] = InternodeAmbienceGen
    NODE_CLASS_MAPPINGS["InternodeAudioStyleTransferDSP"] = InternodeAudioStyleTransferDSP

    NODE_DISPLAY_NAME_MAPPINGS["InternodeMusicPromptGen"] = "Music Prompt Generator (LLM) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMusicStructureGen"] = "Music Structure Planner (LLM) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeMusicCritic"] = "Music Critic (LLM) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeVocalScriptGen"] = "Vocal Script/Lyrics (LLM) (Internode)"
    
    NODE_DISPLAY_NAME_MAPPINGS["InternodeSimpleSoundGen"] = "SFX Generator (Synth) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAmbienceGen"] = "Ambience Generator (DSP) (Internode)"
    NODE_DISPLAY_NAME_MAPPINGS["InternodeAudioStyleTransferDSP"] = "Audio Style Match (DSP) (Internode)"

except Exception as e:
    print(f"#### Internode Error (Audio Gen/LLM): {e}")

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]