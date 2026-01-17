# ComfyUI/custom_nodes/ComfyUI-Internode/internode/vst/studio_surface.py
# VERSION: 3.1.0

import os
import mido
from mido import Message, MidiFile, MidiTrack

class InternodeStudioSurface:
    """
    The backend for the Visual Studio Surface.
    Captures the UI state (Knobs, active notes) and generates MIDI.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ui_state": ("STRING", {"default": "{}", "multiline": False}),
            }
        }

    RETURN_TYPES = ("MIDI_DATA", "MIDI_DATA")
    RETURN_NAMES = ("midi_top", "midi_bot")
    FUNCTION = "generate_midi"
    CATEGORY = "Internode/VST3"

    def generate_midi(self, ui_state):
        # 1. Initialize MIDI Files
        mid_top = MidiFile()
        track_top = MidiTrack()
        mid_top.tracks.append(track_top)
        
        mid_bot = MidiFile()
        track_bot = MidiTrack()
        mid_bot.tracks.append(track_bot)

        # 2. Logic Placeholder
        # Currently, the node acts as a live performance surface. 
        # When "Queue Prompt" is hit, we generate a basic C-Major chord 
        # to ensure the VSTs downstream make sound, until the JS Sequencer is fully linked.
        
        # Example: C Major Chord on Top Deck
        track_top.append(Message('note_on', note=60, velocity=100, time=0))
        track_top.append(Message('note_on', note=64, velocity=100, time=0))
        track_top.append(Message('note_on', note=67, velocity=100, time=0))
        
        track_top.append(Message('note_off', note=60, velocity=100, time=960))
        track_top.append(Message('note_off', note=64, velocity=100, time=0))
        track_top.append(Message('note_off', note=67, velocity=100, time=0))

        # Example: Bass note on Bottom Deck
        track_bot.append(Message('note_on', note=36, velocity=110, time=0))
        track_bot.append(Message('note_off', note=36, velocity=110, time=960))

        return (mid_top, mid_bot)