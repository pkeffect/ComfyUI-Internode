import torch
import numpy as np
import cv2
import random

class InternodeColorGrade:
    """
    Professional 3-Way Color Corrector (Lift, Gamma, Gain).
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                # Lift (Shadows): Moves black point. Range -1.0 to 1.0. 0 is neutral.
                "lift_r": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
                "lift_g": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
                "lift_b": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
                # Gamma (Midtones): Power function. 1.0 is neutral.
                "gamma_r": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0, "step": 0.01}),
                "gamma_g": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0, "step": 0.01}),
                "gamma_b": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0, "step": 0.01}),
                # Gain (Highlights): Multiplier. 1.0 is neutral.
                "gain_r": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
                "gain_g": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
                "gain_b": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "grade"
    CATEGORY = "Internode/VideoFX"

    def grade(self, image, lift_r, lift_g, lift_b, gamma_r, gamma_g, gamma_b, gain_r, gain_g, gain_b):
        # Image is [Batch, H, W, Channels]
        t = image.clone()
        
        # 1. Lift (Offset)
        # We apply lift such that it affects shadows mainly. 
        # Standard CDL Lift: val = val + lift * (1 - val) ??? No, simple offset is standard: val + lift
        # But commonly in NLEs: Lift offsets black point.
        t[..., 0] += lift_r * 0.5
        t[..., 1] += lift_g * 0.5
        t[..., 2] += lift_b * 0.5
        
        # 2. Gain (Multiply)
        # Anchor point is 0.0.
        t[..., 0] *= gain_r
        t[..., 1] *= gain_g
        t[..., 2] *= gain_b
        
        # 3. Gamma (Power)
        # Avoid negative numbers before power
        t = torch.clamp(t, 0.0001, 10.0)
        
        # Gamma correction is usually 1/gamma
        t[..., 0] = torch.pow(t[..., 0], 1.0 / gamma_r)
        t[..., 1] = torch.pow(t[..., 1], 1.0 / gamma_g)
        t[..., 2] = torch.pow(t[..., 2], 1.0 / gamma_b)
        
        # Clamp final
        t = torch.clamp(t, 0.0, 1.0)
        
        return (t,)

class InternodeFilmGrain:
    """
    Composites generated film grain onto the image.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "intensity": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "size": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.1}),
                "saturation": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "0=Monochrome noise, 1=Color noise"}),
                "blend_mode": (["Overlay", "SoftLight", "Add", "Screen"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_grain"
    CATEGORY = "Internode/VideoFX"

    def apply_grain(self, image, intensity, size, saturation, blend_mode):
        batch, h, w, c = image.shape
        
        # Generate Noise
        # For efficiency, we generate a smaller noise patch and resize if size > 1.0
        # If size < 1.0, we generate larger and crop? No, usually grain size means "scale".
        
        target_h = int(h / size)
        target_w = int(w / size)
        
        # Random normal distribution centered at 0.5 for overlay logic? 
        # Or standard gaussian centered at 0.
        
        noise = torch.randn((batch, target_h, target_w, c if saturation > 0 else 1), device=image.device)
        
        # Resize if needed
        if size != 1.0:
            # Permute to [Batch, Channels, H, W] for interpolation
            noise = noise.permute(0, 3, 1, 2)
            noise = torch.nn.functional.interpolate(noise, size=(h, w), mode="bilinear")
            noise = noise.permute(0, 2, 3, 1)
        
        # Duplicate channels if monochrome
        if saturation == 0 and c > 1:
            noise = noise.expand(-1, -1, -1, c)

        # Scale intensity
        noise = noise * intensity

        # Compositing
        result = image.clone()
        
        if blend_mode == "Add":
             result = result + noise
             
        elif blend_mode == "Screen":
             # 1 - (1-a)(1-b)
             # Normalize noise to 0-1 (it's currently centered around 0 with varying range)
             n_norm = (noise + 1.0) * 0.5 # shift approx
             result = 1.0 - (1.0 - result) * (1.0 - n_norm)
             
        elif blend_mode == "Overlay":
            # Overlay formula: 
            # if base < 0.5: 2 * base * blend
            # if base > 0.5: 1 - 2 * (1-base) * (1-blend)
            
            # Since our noise is centered at 0, let's treat it as an offset for a simple "Grain" effect 
            # rather than strict Photoshop overlay which expects 0.5 gray.
            # "Film Grain" usually is just Luma variance.
            # Let's use a simplified Overlay:
            
            # Shift noise to be centered at 0.5 for math
            n_overlay = torch.clamp(noise + 0.5, 0.0, 1.0)
            
            mask = (result < 0.5).float()
            result = (2 * result * n_overlay * mask) + ((1 - 2 * (1 - result) * (1 - n_overlay)) * (1 - mask))

        elif blend_mode == "SoftLight":
             n_sl = torch.clamp(noise + 0.5, 0.0, 1.0)
             # W3C Softlight
             # if Cs <= 0.5: B(x) = Cb - (1-2Cs)Cb(1-Cb)
             # if Cs > 0.5:  B(x) = Cb + (2Cs-1)(D(Cb) - Cb)
             # Simplify: Just add noise based on luminance
             result = result + (noise * (1.0 - torch.abs(2 * result - 1.0))) # Adds mostly in midtones

        return (torch.clamp(result, 0.0, 1.0),)

class InternodeGlitch:
    """
    Simulated Datamosh/Glitch effect.
    Moves blocks of pixels based on a trigger.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "trigger": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 1.0}),
                "block_size": ("INT", {"default": 32, "min": 8, "max": 256}),
                "glitch_amount": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 2.0}),
            },
            "optional": {
                "motion_vectors": ("IMAGE",), # Future proofing
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "glitch"
    CATEGORY = "Internode/VideoFX"

    def glitch(self, image, trigger, block_size, glitch_amount, motion_vectors=None):
        if trigger < 0.5:
            return (image,)
            
        # If triggered, we shuffle blocks or displace channels
        batch, h, w, c = image.shape
        out = image.clone()
        
        # Simple Channel Shift (RGB Split)
        # Shift R channel left, B channel right
        shift_x = int(random.randint(-10, 10) * glitch_amount)
        shift_y = int(random.randint(-5, 5) * glitch_amount)
        
        # Roll tensors
        out[..., 0] = torch.roll(out[..., 0], shifts=(shift_y, shift_x), dims=(1, 2))
        out[..., 2] = torch.roll(out[..., 2], shifts=(-shift_y, -shift_x), dims=(1, 2))
        
        # Block sorting / shuffling simulation
        # We select random rows and roll them heavily
        num_glitch_rows = int(h * 0.1 * glitch_amount)
        for _ in range(num_glitch_rows):
            row_idx = random.randint(0, h-1)
            row_shift = random.randint(-50, 50)
            out[:, row_idx, :, :] = torch.roll(out[:, row_idx, :, :], shifts=row_shift, dims=1)

        return (out,)

class InternodeSpeedRamp:
    """
    Variable Speed Playback (Time Remapping).
    Takes an input video and a float curve (0.0 to 1.0) representing 'Speed'.
    Resamples the video to create slow-mo or fast-forward effects using frame blending.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "speed_curve": ("FLOAT_LIST",), # List of floats, 1.0 = normal speed
                "target_fps": ("INT", {"default": 24}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "remap_time"
    CATEGORY = "Internode/VideoFX"

    def remap_time(self, images, speed_curve, target_fps):
        # speed_curve: list of multipliers for every output frame? 
        # Or list of multipliers for input frames?
        # Let's assume speed_curve represents the playback speed AT THAT MOMENT in the output sequence.
        # We integrate speed to find the source frame index.
        
        batch_count = images.shape[0]
        out_images = []
        
        source_cursor = 0.0
        
        # If speed_curve is shorter than needed, we loop or clamp? 
        # We generate frames until we run out of source video.
        
        # Or, usually, you want to render N frames.
        # Let's iterate through the speed_curve (assuming it defines the timeline length)
        # If speed_curve is [1.0, 0.5, 0.1], we output 3 frames.
        # Frame 1: Source 0.0
        # Frame 2: Source 0.0 + 1.0 = 1.0
        # Frame 3: Source 1.0 + 0.5 = 1.5
        
        # Correct logic:
        # T(n) = T(n-1) + Speed(n)
        
        for speed in speed_curve:
            # Current Frame Index to sample from
            idx = source_cursor
            
            # Bounds check
            if idx >= batch_count - 1:
                # Hold last frame
                out_images.append(images[-1])
            else:
                # Linear Interpolation (Frame Blending)
                idx_floor = int(np.floor(idx))
                idx_ceil = min(idx_floor + 1, batch_count - 1)
                alpha = idx - idx_floor
                
                frame_a = images[idx_floor]
                frame_b = images[idx_ceil]
                
                blended = (frame_a * (1.0 - alpha)) + (frame_b * alpha)
                out_images.append(blended)
            
            # Advance cursor
            source_cursor += speed
            
            if source_cursor >= batch_count:
                break # End of source video
                
        if not out_images:
            return (images,)
            
        return (torch.stack(out_images),)