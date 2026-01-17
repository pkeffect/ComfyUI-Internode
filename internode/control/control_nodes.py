import math
import numpy as np
import re

class InternodeLFO:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "waveform": (["Sine", "Square", "Triangle", "Sawtooth", "Random"],),
                "period_frames": ("INT", {"default": 60, "min": 1, "max": 9999}),
                "amplitude": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 100.0, "step": 0.01}),
                "offset": ("FLOAT", {"default": 0.5, "min": -100.0, "max": 100.0, "step": 0.01}),
                "phase_shift": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "0.0-1.0 (Percentage of period)"}),
                "total_frames": ("INT", {"default": 120, "min": 1, "max": 9999}),
            }
        }

    RETURN_TYPES = ("FLOAT_LIST", "FLOAT")
    RETURN_NAMES = ("float_curve", "last_value")
    FUNCTION = "generate"
    CATEGORY = "Internode/Control"

    def generate(self, waveform, period_frames, amplitude, offset, phase_shift, total_frames):
        values = []
        phase_offset_frames = int(phase_shift * period_frames)

        for i in range(total_frames):
            t = (i + phase_offset_frames) % period_frames
            x = t / float(period_frames) # 0.0 to 1.0 within cycle
            
            y = 0.0
            
            if waveform == "Sine":
                y = math.sin(x * 2 * math.pi)
            
            elif waveform == "Square":
                y = 1.0 if x < 0.5 else -1.0
            
            elif waveform == "Triangle":
                # 4 * abs(x - 0.5) - 1  (approx)
                if x < 0.25: y = 4 * x
                elif x < 0.75: y = 2 - 4 * x
                else: y = 4 * x - 4
            
            elif waveform == "Sawtooth":
                y = 2 * (x - 0.5) # -1 to 1

            elif waveform == "Random":
                # Sample-and-hold random per period
                # We need deterministic random based on the cycle index
                cycle_idx = (i + phase_offset_frames) // period_frames
                np.random.seed(cycle_idx)
                y = np.random.uniform(-1.0, 1.0)

            # Apply Amp and Offset
            val = offset + (y * amplitude)
            values.append(val)

        return (values, values[-1])

class InternodeADSR:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "attack_frames": ("INT", {"default": 10, "min": 0}),
                "decay_frames": ("INT", {"default": 10, "min": 0}),
                "sustain_level": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0}),
                "release_frames": ("INT", {"default": 20, "min": 0}),
                "total_frames": ("INT", {"default": 120, "min": 1}),
                "trigger_start": ("INT", {"default": 0, "min": 0}),
                "hold_duration": ("INT", {"default": 30, "min": 0, "tooltip": "How long the note is 'held' before release starts."}),
            }
        }

    RETURN_TYPES = ("FLOAT_LIST",)
    RETURN_NAMES = ("envelope",)
    FUNCTION = "generate_env"
    CATEGORY = "Internode/Control"

    def generate_env(self, attack_frames, decay_frames, sustain_level, release_frames, total_frames, trigger_start, hold_duration):
        values = []
        
        # Timeline:
        # T0 = trigger_start
        # T1 = T0 + Attack (Peak 1.0)
        # T2 = T1 + Decay (Sustain Level)
        # T3 = T0 + Hold (Key release point)
        # T4 = T3 + Release (Zero)
        
        # Ensure logical hold time
        if hold_duration < (attack_frames + decay_frames):
             # If trigger released before decay finishes, logic gets complex. 
             # Simplify: Force hold to be at least attack+decay for standard ADSR behavior in this simple node
             pass 

        t_start = trigger_start
        t_peak = t_start + attack_frames
        t_sustain_start = t_peak + decay_frames
        t_release_start = t_start + hold_duration
        t_end = t_release_start + release_frames

        for i in range(total_frames):
            val = 0.0
            
            if i < t_start:
                val = 0.0
            
            elif i < t_peak:
                # Attack Phase
                if attack_frames > 0:
                    val = (i - t_start) / attack_frames
                else:
                    val = 1.0
            
            elif i < t_sustain_start:
                # Decay Phase
                # Map range [0, decay] to [1.0, sustain]
                progress = (i - t_peak) / decay_frames if decay_frames > 0 else 1.0
                val = 1.0 - (progress * (1.0 - sustain_level))
            
            elif i < t_release_start:
                # Sustain Phase
                val = sustain_level
                
                # Handling case where release starts during attack/decay (early release)
                # For simplicity in this node, 'Hold' overrides A/D phases? 
                # No, let's strictly follow phases based on time. 
                # If t_release_start < t_sustain_start, we should interpolate from CURRENT val to 0.
                # But to keep code robust:
                if i >= t_release_start: pass # Should be caught by next block
            
            elif i < t_end:
                # Release Phase
                # Determine value at moment of release
                start_release_val = sustain_level
                # If we released early (during A or D), this simple logic might snap.
                # Advanced ADSR requires state memory. 
                # Analytic ADSR:
                progress = (i - t_release_start) / release_frames
                val = start_release_val * (1.0 - progress)
            
            else:
                val = 0.0
                
            values.append(max(0.0, min(1.0, val)))

        return (values,)

class InternodeParamRemap:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "value": ("FLOAT", {"default": 0.5, "forceInput": False}), 
                "in_min": ("FLOAT", {"default": 0.0}),
                "in_max": ("FLOAT", {"default": 1.0}),
                "out_min": ("FLOAT", {"default": 0.0}),
                "out_max": ("FLOAT", {"default": 10.0}),
                "curve": (["Linear", "Ease In (Square)", "Ease Out (InvSquare)", "Logarithmic"],),
                "clamp": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                 "value_list": ("FLOAT_LIST",),
            }
        }

    RETURN_TYPES = ("FLOAT", "FLOAT_LIST")
    FUNCTION = "remap"
    CATEGORY = "Internode/Control"

    def remap(self, value, in_min, in_max, out_min, out_max, curve, clamp, value_list=None):
        
        def process_one(v):
            # Normalize to 0-1
            if in_max == in_min: t = 0.0
            else: t = (v - in_min) / (in_max - in_min)
            
            if clamp: t = max(0.0, min(1.0, t))
            
            # Apply Curve
            if curve == "Ease In (Square)":
                t = t * t
            elif curve == "Ease Out (InvSquare)":
                t = 1.0 - (1.0 - t) * (1.0 - t)
            elif curve == "Logarithmic":
                # Fake log mapping for 0-1 range
                if t <= 0: t = 0
                else: t = math.log(t * 9.0 + 1.0) / math.log(10.0) # map 0-1 log style

            # Scale to output
            return out_min + t * (out_max - out_min)

        # Handle Single Value
        out_val = process_one(value)
        
        # Handle List
        out_list = []
        if value_list:
            out_list = [process_one(x) for x in value_list]
        else:
            # If no list input, return list containing single value
            out_list = [out_val]

        return (out_val, out_list)

class InternodeStringSequencer:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "schedule": ("STRING", {"multiline": True, "default": "0: A cinematic shot of a cat\n30: A cinematic shot of a dog", "dynamicPrompts": False}),
                "total_frames": ("INT", {"default": 120}),
                "current_frame": ("INT", {"default": 0}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING_LIST")
    RETURN_NAMES = ("current_string", "string_list")
    FUNCTION = "sequence"
    CATEGORY = "Internode/Control"

    def sequence(self, schedule, total_frames, current_frame):
        # Parse schedule
        # Format: "FRAME: TEXT"
        keyframes = {}
        
        for line in schedule.splitlines():
            line = line.strip()
            if not line or ":" not in line: continue
            
            parts = line.split(":", 1)
            try:
                frame_idx = int(parts[0].strip())
                text_content = parts[1].strip()
                keyframes[frame_idx] = text_content
            except ValueError:
                continue
                
        # Sort keys
        sorted_frames = sorted(keyframes.keys())
        if not sorted_frames:
            return ("", [""] * total_frames)
            
        # Generate list
        output_list = []
        current_text = keyframes[sorted_frames[0]] # Default to first defined
        
        # Fill from 0 to end
        # Note: if first keyframe is at 10, 0-9 will be empty or repeat first found? 
        # Standard behavior: hold previous value.
        
        idx = 0
        next_kf_idx = 0
        
        for f in range(total_frames):
            # Check if we hit a new keyframe
            if f in keyframes:
                current_text = keyframes[f]
            # Handle case where first keyframe > 0.
            # If f < first keyframe, we can either look ahead or output empty.
            # Let's look ahead to first keyframe for "pre-roll"
            elif f < sorted_frames[0]:
                current_text = keyframes[sorted_frames[0]]
                
            output_list.append(current_text)

        # Get specific frame
        frame_clamped = max(0, min(total_frames - 1, current_frame))
        out_current = output_list[frame_clamped]
        
        return (out_current, output_list)

NODE_CLASS_MAPPINGS = {
    "InternodeLFO": InternodeLFO,
    "InternodeADSR": InternodeADSR,
    "InternodeParamRemap": InternodeParamRemap,
    "InternodeStringSequencer": InternodeStringSequencer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "InternodeLFO": "LFO Generator (Internode)",
    "InternodeADSR": "ADSR Envelope (Internode)",
    "InternodeParamRemap": "Parameter Remapper (Internode)",
    "InternodeStringSequencer": "String Sequencer (Internode)"
}