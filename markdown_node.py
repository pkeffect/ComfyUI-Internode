# ComfyUI/custom_nodes/comfyui-internode-nodes/markdown_node.py
# VERSION: 1.3.0

class InternodeMarkdownNote:
    """
    A note node that displays text as Markdown in the UI.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "# My Note\n\nStart typing here..."}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "do_nothing"
    CATEGORY = "Internode/Utils"

    def do_nothing(self, text):
        return (text,)