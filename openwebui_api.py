# ComfyUI/custom_nodes/ComfyUI-Internode/openwebui_api.py
# VERSION: 3.0.0

import requests
import base64
import json
from io import BytesIO

class OpenWebUIAPI:
    def __init__(self, host, api_key):
        self.host = host.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.chat_endpoint = f"{self.host}/api/chat/completions"
        self.tags_endpoint = f"{self.host}/api/models"

    def get_models(self):
        try:
            response = requests.get(self.tags_endpoint, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            return sorted(models)
        except Exception as e:
            raise e

    def _prepare_content(self, prompt, images=None, audio=None, video=None):
        """Constructs the OpenAI-compatible multimodal content list."""
        content = [{"type": "text", "text": prompt}]

        # 1. Images
        if images:
            for img in images:
                # Expecting images to be pre-converted to base64 strings or handled here
                # Assuming img is a PIL Image
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                })

        # 2. Audio (Base64 WAV)
        if audio:
            # Open WebUI / OpenAI backends often treat files via specific attachments or data URIs
            # using 'image_url' type as a generic 'file_url' container in some adapters,
            # or strictly expecting text if the model is just an LLM.
            # However, for a Multimodal node, we format as data URI.
            content.append({
                "type": "image_url", # Generic carrier for many local LLM servers
                "image_url": {"url": f"data:audio/wav;base64,{audio}"}
            })

        # 3. Video (Base64 MP4 or Frames)
        # If passed as a single encoded string (video file)
        if video and isinstance(video, str): 
             content.append({
                "type": "image_url",
                "image_url": {"url": f"data:video/mp4;base64,{video}"}
            })
        # If passed as list of images (frames), they are handled in the images loop if passed there.
        
        return content

    def chat_completions(self, model, prompt, images=None, audio=None, video=None, max_retries=3):
        # Prepare Multimodal Content
        # Note: 'images' expected as list of PIL objects
        # 'audio' expected as base64 string
        # 'video' expected as base64 string (if file)
        
        message_content = self._prepare_content(prompt, images, audio, video)

        data = {
            "model": model,
            "messages": [{"role": "user", "content": message_content}],
            "stream": False,
        }
        
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = requests.post(self.chat_endpoint, headers=self.headers, json=data, timeout=120)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except requests.exceptions.Timeout as e:
                last_exception = e
                print(f"#### Internode Timeout (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"#### Internode API Error: {e}")
                if 'response' in locals() and response is not None:
                    print(f"#### Response: {response.text}")
                raise e
        
        raise last_exception

    # Legacy wrappers for backward compatibility if needed
    def generate(self, model, prompt, max_retries=3):
        return self.chat_completions(model, prompt, max_retries=max_retries)

    def vision(self, model, prompt, image, max_retries=3):
        return self.chat_completions(model, prompt, images=[image], max_retries=max_retries)