import torch
import folder_paths
from nodes import PreviewImage

class InternodeImageComparer(PreviewImage):
    """A node that compares two images in the UI."""
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {},
            "optional": {
                "image_a": ("IMAGE",),
                "image_b": ("IMAGE",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "compare_images"
    CATEGORY = "Internode/Image FX"
    DESCRIPTION = "Compares two images with a hover slider."

    def compare_images(self, image_a=None, image_b=None, filename_prefix="internode_compare", prompt=None, extra_pnginfo=None):
        result = {"ui": {"a_images": [], "b_images": []}}
        
        # We reuse PreviewImage's save_images method to handle temp file saving
        # but we need to ensure we don't crash if inputs are missing
        
        if image_a is not None:
            # save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None)
            res_a = self.save_images(image_a, filename_prefix, prompt, extra_pnginfo)
            result["ui"]["a_images"] = res_a["ui"]["images"]
            
        if image_b is not None:
            res_b = self.save_images(image_b, filename_prefix, prompt, extra_pnginfo)
            result["ui"]["b_images"] = res_b["ui"]["images"]

        return result
