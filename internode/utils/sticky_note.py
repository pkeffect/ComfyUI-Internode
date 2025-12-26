# ComfyUI/custom_nodes/ComfyUI-Internode/sticky_note.py
# VERSION: 3.0.8

class InternodeStickyNote:
    """
    A visual 'Post-it' style note with customizable colors.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "### Sticky Note\n- Reminder 1\n- Reminder 2"}),
                "note_color": (["Yellow", "Green", "Pink", "Orange", "Blue", "White"], {"default": "Yellow"}),
                "text_color": (["Black", "Gray", "White", "Red", "Blue"], {"default": "Black"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "do_nothing"
    CATEGORY = "Internode/Utilities"

    def do_nothing(self, text, note_color, text_color):
        return (text,)