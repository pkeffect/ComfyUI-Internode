# ComfyUI-Internode

![Internode ComfyUI Custom Nodes](./images/screenshot.png)

**Version:** 3.0.2  
**Author:** pkeffect

A professional audio/multimodal suite for ComfyUI. Internode bridges the gap between Digital Audio Workstations (DAW) and Generative AI, providing high-fidelity DSP mixing, VST3 hosting, ACE-Step music generation, and advanced LLM integration via OpenWebUI.

---

## 📦 Installation

1.  **Clone the repository** into your `ComfyUI/custom_nodes/` folder:
    ```bash
    cd ComfyUI/custom_nodes/
    git clone https://github.com/pkeffect/ComfyUI-Internode.git
    ```

2.  **Install Dependencies**:
    *   **Windows/Linux/Mac**: Run the included install script.
        ```bash
        cd ComfyUI-Internode
        ..\..\python_embeded\python.exe install.py  # Standalone Windows
        # OR
        python install.py                           # Standard Python env
        ```

3.  **System Requirements**:
    *   **FFmpeg**: Required for loading MP3, FLAC, OGG, and video files. Ensure `ffmpeg` is in your system PATH.
    *   **VST3 Support**: To use the VST loader, you must have VST3 plugins installed in standard system locations (e.g., `C:\Program Files\Common Files\VST3`).

---

## 🎛️ Audio Mixer (DSP)

A fully functional 4-channel or 8-channel mixer with a custom UI.

*   **Dual Engine Architecture**:
    *   **UI (Frontend)**: Uses Web Audio API for fast, real-time previewing inside the browser.
    *   **Render (Backend)**: Uses PyTorch/Torchaudio for bit-perfect, GPU-accelerated rendering.
    *   *Note: Minor dynamic differences may exist between the browser preview and the final node output.*
*   **Channel Strip Features**:
    *   **3-Band EQ**: Professional Shelving (Low/High) and Peaking (Mid) filters.
    *   **Dynamics**: One-knob Gate and Compressor per channel.
    *   **Delay**: Send-based delay with Time, Feedback, and Stereo Echo controls.
    *   **Pan/Vol**: Standard stereo panning and faders.
*   **Master Bus**:
    *   **Master FX**: Drive (Saturation), Low-Cut/High-Cut filters, Ceiling (Limiter).
    *   **Stereo Width**: M/S processing to widen or narrow the mix.
*   **Outputs**:
    *   `master_output`: The final mix with all Master FX applied.
    *   `pre_master_output`: The sum of all channels *before* the Master FX chain (useful for external mastering).

---

## 🎹 ACE-Step (AI Music Generation)

Native implementation of the ACE-Step diffusion model for high-quality audio generation.

*   **Nodes**:
    *   `ACE-Step Loader`: Loads the model with caching support to prevent reloading on every run.
    *   `ACE-Step Generator`: The main generation node.
*   **Features**:
    *   **Preview Mode**: Toggle to limit generation to 10s @ 20 steps for rapid prompt testing.
    *   **LoRA Support**: Dynamically load/unload LoRAs (e.g., Chinese Rap LoRA).
    *   **Lyrics & Guidance**: Full support for lyrical prompting and CFG scales.

---

## 🔌 VST3 Host (Audio FX)

Apply your favorite third-party VST3 plugins to audio tensors within ComfyUI.

*   **Node**: `InternodeVSTLoader`
*   **Inputs**:
    *   `audio`: The audio stream to process.
    *   `vst_path`: Absolute path to the `.vst3` file (e.g., `C:\Program Files\Common Files\VST3\FabFilter Pro-Q 3.vst3`).
    *   `dry_wet`: Blend control (0.0 = Dry, 1.0 = Wet).
*   **Performance Warning**: This node processes audio on the **CPU** (using `pedalboard`). It will transfer data from GPU -> CPU -> VST -> GPU, which may impact performance during batch processing.

---

## 🤖 OpenWebUI (LLM Integration)

A unified interface for connecting to local or remote OpenWebUI instances (e.g., Ollama, LocalAI).

*   **Features**:
    *   **Context Aware**: Correctly parses and appends conversation history, allowing for multi-turn chatbots.
    *   **Multimodal**: Supports Image, Video, and Audio inputs (sent as Base64 data URIs).
    *   **Model Caching**: Caches the list of available models from the API to prevent excessive network calls.
*   **Nodes**:
    *   `OpenWebUI Server Config`: Set your Host URL and API Key.
    *   `OpenWebUI Unified`: The main chat node. Accepts prompt + history + media.
    *   `OpenWebUI Refresh Models`: Force-refreshes the model list from the server.

---

## 🛠️ Utilities

*   **Markdown Note**: A secure, sanitizing Markdown editor for adding documentation directly into your workflows. Supports code blocks, tables, and basic formatting.
*   **Loaders**:
    *   `Audio Loader`: Supports WAV, MP3, FLAC, etc. (Requires FFmpeg).
    *   `Video Loader`: Extracts frames and audio from video files. Includes frame capping to prevent OOM errors.
    *   `Image Loader`: Supports RGBA/Mask inversion.
*   **Savers**:
    *   `Audio Saver`: Supports exporting to WAV (16/24/32-float), FLAC, MP3, OGG, AAC.

---

## ⚠️ Troubleshooting

**1. "Missing dependencies" error:**
Run `install.py` found in the root of the custom node folder.

**2. Audio files (MP3/AAC) fail to load:**
Internode falls back to standard Python libraries if FFmpeg is not found. Install FFmpeg and add it to your system PATH to enable broad format support.

**3. VSTs not loading:**
*   Ensure the path points to a `.vst3` file, not a `.dll` (VST2 is not supported).
*   Ensure the plugin is 64-bit.
*   Check the console log for specific `pedalboard` errors.

**4. Mixer UI doesn't match the output sound exactly:**
The browser uses Web Audio API for the UI preview, while the node uses PyTorch for the final render. Minor differences in compressor attack/release curves and filter Q-factors are expected. Trust the `Audio Saver` output for critical work.