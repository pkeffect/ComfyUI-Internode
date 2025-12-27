# ComfyUI/custom_nodes/ComfyUI-Internode/internode/image_fx/__init__.py
from .image_nodes import InternodeAspectRatioSmart, InternodeDetailEnhancer, InternodeDepthMapHF, InternodeColorMatch

NODE_CLASS_MAPPINGS = {
    "InternodeAspectRatioSmart": InternodeAspectRatioSmart,
    "InternodeDetailEnhancer": InternodeDetailEnhancer,
    "InternodeDepthMapHF": InternodeDepthMapHF,
    "InternodeColorMatch": InternodeColorMatch
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "InternodeAspectRatioSmart": "Smart Aspect Ratio & Crop (Internode)",
    "InternodeDetailEnhancer": "Image Detail Enhancer (Internode)",
    "InternodeDepthMapHF": "Depth Map Generator (HF) (Internode)",
    "InternodeColorMatch": "Color Match / Style Transfer (Internode)"
}