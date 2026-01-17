# ComfyUI/custom_nodes/ComfyUI-Internode/internode/video_fx/video_smart_nodes.py
# VERSION: 3.4.0

import torch
import numpy as np
import cv2

class InternodeOpticalFlowInterpolator:
    """
    A lightweight 'AI' interpolator using Dense Optical Flow (Farneback algorithm).
    OPTIMIZED: Includes downscaling parameter to reduce CPU load significantly.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "multiplier": ("INT", {"default": 2, "min": 2, "max": 4}),
                "flow_scale": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 1.0, "step": 0.1, "tooltip": "Downscale factor for flow calculation. 0.5 = 4x faster."}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "interpolate"
    CATEGORY = "Internode/VideoFX"

    def interpolate(self, images, multiplier, flow_scale=0.5):
        batch, h, w, c = images.shape
        out_list = []
        
        images_np = (images.cpu().numpy() * 255).astype(np.uint8)
        
        # Optimization: Calculate flow on smaller image
        flow_h, flow_w = int(h * flow_scale), int(w * flow_scale)
        
        prev_gray = cv2.cvtColor(images_np[0], cv2.COLOR_RGB2GRAY)
        prev_small = cv2.resize(prev_gray, (flow_w, flow_h), interpolation=cv2.INTER_LINEAR)
        
        for i in range(batch - 1):
            frame1 = images_np[i]
            frame2 = images_np[i+1]
            out_list.append(frame1) # Add original
            
            next_gray = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
            next_small = cv2.resize(next_gray, (flow_w, flow_h), interpolation=cv2.INTER_LINEAR)
            
            # Calculate Flow on Proxy
            flow_small = cv2.calcOpticalFlowFarneback(prev_small, next_small, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            
            # Upscale Flow
            if flow_scale != 1.0:
                # Resize flow field to full res
                flow = cv2.resize(flow_small, (w, h), interpolation=cv2.INTER_LINEAR)
                # Adjust flow magnitude
                flow *= (1.0 / flow_scale)
            else:
                flow = flow_small
            
            # Generate intermediate frames
            for j in range(1, multiplier):
                alpha = j / multiplier
                
                # Flow maps
                flow_map = -flow * alpha
                h_map, w_map = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
                
                map_x = (w_map + flow_map[..., 0]).astype(np.float32)
                map_y = (h_map + flow_map[..., 1]).astype(np.float32)
                
                # Warp frame 1 forward
                warped = cv2.remap(frame1, map_x, map_y, cv2.INTER_LINEAR)
                
                # Simple blend with frame 2 to hide artifacts
                interpolated = cv2.addWeighted(warped, 1.0 - alpha, frame2, alpha, 0)
                
                out_list.append(interpolated)
            
            prev_small = next_small
            
        out_list.append(images_np[-1]) # Add last
        
        # Convert back
        out_tensor = torch.from_numpy(np.array(out_list)).float() / 255.0
        return (out_tensor,)

class InternodeMotionGlitch:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "intensity": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0}),
                "threshold": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 20.0, "tooltip": "Only glitch if motion exceeds this"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "glitch"
    CATEGORY = "Internode/VideoFX"

    def glitch(self, images, intensity, threshold):
        batch, h, w, c = images.shape
        images_np = (images.cpu().numpy() * 255).astype(np.uint8)
        out_list = [images_np[0]]
        
        prev_gray = cv2.cvtColor(images_np[0], cv2.COLOR_RGB2GRAY)
        
        # Optimization: Glitch doesn't need high precision flow
        # Force low res flow for speed
        glitch_scale = 0.25
        sh, sw = int(h * glitch_scale), int(w * glitch_scale)
        prev_small = cv2.resize(prev_gray, (sw, sh))

        for i in range(1, batch):
            curr = images_np[i]
            curr_gray = cv2.cvtColor(curr, cv2.COLOR_RGB2GRAY)
            curr_small = cv2.resize(curr_gray, (sw, sh))
            
            flow_small = cv2.calcOpticalFlowFarneback(prev_small, curr_small, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            
            # Upscale just for mask generation
            flow = cv2.resize(flow_small, (w, h), interpolation=cv2.INTER_NEAREST) * (1/glitch_scale)
            
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            # Create mask where motion is high
            mask = mag > threshold
            
            # Apply glitch displacement on High Motion areas
            if np.any(mask):
                # Amplify flow vector
                dx = (flow[..., 0] * intensity).astype(np.int32)
                dy = (flow[..., 1] * intensity).astype(np.int32)
                
                h_map, w_map = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
                
                # Add noise/jitter to maps based on flow intensity
                map_x = (w_map + dx * mask).astype(np.float32)
                map_y = (h_map + dy * mask).astype(np.float32)
                
                glitched = cv2.remap(curr, map_x, map_y, cv2.INTER_NEAREST)
                out_list.append(glitched)
            else:
                out_list.append(curr)
                
            prev_small = curr_small
            
        out_tensor = torch.from_numpy(np.array(out_list)).float() / 255.0
        return (out_tensor,)

class InternodeBatchStyleTransfer:
    """
    Applies the color statistics of a Reference Style Image to every frame 
    of a target video sequence.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_video": ("IMAGE",),
                "reference_style": ("IMAGE",),
                "blend": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "transfer_batch"
    CATEGORY = "Internode/VideoFX"

    def transfer_batch(self, target_video, reference_style, blend):
        # We reuse the logic from image_nodes but apply loop
        # Reference is usually single frame
        ref_np = (reference_style[0].cpu().numpy() * 255).astype(np.uint8)
        r_lab = cv2.cvtColor(ref_np, cv2.COLOR_RGB2LAB).astype("float32")
        r_mean, r_std = cv2.meanStdDev(r_lab)
        
        out_list = []
        batch = target_video.shape[0]
        
        for i in range(batch):
            t_np = (target_video[i].cpu().numpy() * 255).astype(np.uint8)
            t_lab = cv2.cvtColor(t_np, cv2.COLOR_RGB2LAB).astype("float32")
            
            t_mean, t_std = cv2.meanStdDev(t_lab)
            
            res_lab = t_lab.copy()
            for k in range(3):
                res_lab[:,:,k] = (t_lab[:,:,k] - t_mean[k]) * (r_std[k] / (t_std[k] + 1e-5)) + r_mean[k]
                
            res_lab = np.clip(res_lab, 0, 255).astype("uint8")
            res_rgb = cv2.cvtColor(res_lab, cv2.COLOR_LAB2RGB)
            
            final = (res_rgb.astype("float32") / 255.0) * blend + target_video[i].cpu().numpy() * (1.0 - blend)
            out_list.append(final)
            
        return (torch.from_numpy(np.array(out_list)),)