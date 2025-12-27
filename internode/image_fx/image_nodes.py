# ComfyUI/custom_nodes/ComfyUI-Internode/internode/image_fx/image_nodes.py
# VERSION: 3.3.0

import torch
import numpy as np
import cv2
from PIL import Image

# For Depth Map
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class InternodeAspectRatioSmart:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "aspect_ratio": (["1:1", "16:9", "9:16", "4:3", "3:4", "21:9"],),
                "fit_mode": (["Crop Center", "Pad (Letterbox)"],),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "process"
    CATEGORY = "Internode/Image FX"

    def process(self, image, aspect_ratio, fit_mode):
        batch, h, w, c = image.shape
        
        # Parse AR
        ar_map = {"1:1": 1.0, "16:9": 1.777, "9:16": 0.5625, "4:3": 1.333, "3:4": 0.75, "21:9": 2.333}
        target_ar = ar_map.get(aspect_ratio, 1.0)
        current_ar = w / h
        
        out_images = []
        out_masks = []

        for i in range(batch):
            img_np = image[i].cpu().numpy()
            
            if fit_mode == "Crop Center":
                if current_ar > target_ar:
                    # Too wide, crop width
                    new_w = int(h * target_ar)
                    start_x = (w - new_w) // 2
                    crop = img_np[:, start_x:start_x+new_w, :]
                else:
                    # Too tall, crop height
                    new_h = int(w / target_ar)
                    start_y = (h - new_h) // 2
                    crop = img_np[start_y:start_y+new_h, :, :]
                
                # Create mask (full ones)
                out_images.append(torch.from_numpy(crop))
                out_masks.append(torch.ones((crop.shape[0], crop.shape[1]), dtype=torch.float32))

            else: # Pad
                if current_ar > target_ar:
                    # Too wide, pad height
                    new_h = int(w / target_ar)
                    pad_top = (new_h - h) // 2
                    pad_bottom = new_h - h - pad_top
                    
                    # Pad image with black
                    padded = np.pad(img_np, ((pad_top, pad_bottom), (0,0), (0,0)), mode='constant')
                    
                    # Create Mask (0 for padded area, 1 for original)
                    mask = np.zeros((new_h, w), dtype=np.float32)
                    mask[pad_top:pad_top+h, :] = 1.0
                else:
                    # Too tall, pad width
                    new_w = int(h * target_ar)
                    pad_left = (new_w - w) // 2
                    pad_right = new_w - w - pad_left
                    
                    padded = np.pad(img_np, ((0,0), (pad_left, pad_right), (0,0)), mode='constant')
                    
                    mask = np.zeros((h, new_w), dtype=np.float32)
                    mask[:, pad_left:pad_left+w] = 1.0

                out_images.append(torch.from_numpy(padded))
                out_masks.append(torch.from_numpy(mask))

        return (torch.stack(out_images), torch.stack(out_masks))

class InternodeDetailEnhancer:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0}),
                "radius": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 10.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "enhance"
    CATEGORY = "Internode/Image FX"

    def enhance(self, image, strength, radius):
        # Unsharp Mask technique (Signal Processing for Images)
        t = image.clone()
        
        # Blur the image (Low Pass)
        # We use a simple box blur approximation via AveragePooling or Gaussian if avail.
        # Let's use torch Gaussian blur if possible, or manual kernel.
        # Simpler: Permute to [B, C, H, W] for torch transforms
        
        t_perm = t.permute(0, 3, 1, 2)
        
        # Gaussian Kernel approx
        kernel_size = int(radius * 2) + 1
        if kernel_size % 2 == 0: kernel_size += 1
        
        import torchvision.transforms.functional as F
        blurred = F.gaussian_blur(t_perm, kernel_size, sigma=[radius, radius])
        
        # High Pass = Original - Low Pass
        high_pass = t_perm - blurred
        
        # Add High Pass back to original
        sharpened = t_perm + (high_pass * strength)
        
        return (torch.clamp(sharpened.permute(0, 2, 3, 1), 0.0, 1.0),)

class InternodeDepthMapHF:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "model_name": (["depth-anything/Depth-Anything-V2-Small-hf", "Intel/dpt-large"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "estimate"
    CATEGORY = "Internode/Image FX"

    def estimate(self, image, model_name):
        if not TRANSFORMERS_AVAILABLE:
            print("#### Internode Error: 'transformers' library not found.")
            return (image,)

        # Load Pipeline (Cached by HF)
        # Note: This might download 100-500MB on first run.
        depth_pipe = pipeline("depth-estimation", model=model_name)
        
        out_batch = []
        for i in range(image.shape[0]):
            pil_img = Image.fromarray(np.clip(255. * image[i].cpu().numpy(), 0, 255).astype(np.uint8))
            
            # Inference
            result = depth_pipe(pil_img)
            depth_tensor = result["depth"]
            
            # Convert back to Tensor
            depth_np = np.array(depth_tensor).astype(np.float32) / 255.0
            depth_np = depth_np[:, :, None] # Add Channel dim
            
            # Expand to 3 channels for compatibility
            depth_np = np.repeat(depth_np, 3, axis=2)
            
            out_batch.append(torch.from_numpy(depth_np))
            
        return (torch.stack(out_batch),)

class InternodeColorMatch:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_image": ("IMAGE",),
                "reference_image": ("IMAGE",),
                "blend": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "match"
    CATEGORY = "Internode/Image FX"

    def match(self, target_image, reference_image, blend):
        # Reinhard Color Transfer (Mean/Std Stats in LAB space)
        # Fast, no neural network required.
        
        t_np = (target_image[0].cpu().numpy() * 255).astype(np.uint8)
        r_np = (reference_image[0].cpu().numpy() * 255).astype(np.uint8)
        
        # Convert to LAB
        t_lab = cv2.cvtColor(t_np, cv2.COLOR_RGB2LAB).astype("float32")
        r_lab = cv2.cvtColor(r_np, cv2.COLOR_RGB2LAB).astype("float32")
        
        # Compute Stats
        t_mean, t_std = cv2.meanStdDev(t_lab)
        r_mean, r_std = cv2.meanStdDev(r_lab)
        
        t_mean = t_mean.flatten()
        t_std = t_std.flatten()
        r_mean = r_mean.flatten()
        r_std = r_std.flatten()
        
        # Apply Transform
        # Output = (Input - InMean) * (RefStd / InStd) + RefMean
        res_lab = t_lab.copy()
        for k in range(3):
            res_lab[:,:,k] = (t_lab[:,:,k] - t_mean[k]) * (r_std[k] / (t_std[k] + 1e-5)) + r_mean[k]
            
        res_lab = np.clip(res_lab, 0, 255).astype("uint8")
        res_rgb = cv2.cvtColor(res_lab, cv2.COLOR_LAB2RGB)
        
        # Blend
        final_np = (res_rgb.astype("float32") / 255.0) * blend + target_image[0].cpu().numpy() * (1.0 - blend)
        
        return (torch.from_numpy(final_np).unsqueeze(0),)