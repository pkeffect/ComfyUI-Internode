# ComfyUI-Internode

**Version 3.0.0**  
A comprehensive "Kitchen Sink" suite for **ComfyUI** focusing on Audio DSP, Music Generation (ACE-Step), OpenWebUI Agents, and Workflow Utilities.

This node pack aims to bring **DAW-level Audio Processing** and **Conversational Agent** capabilities directly into the ComfyUI graph.

## 🚀 Key Updates (v3.0.0)

*   **⚡ GPU-Accelerated DSP:** The Audio Mixer now uses vectorized convolution for Delays and Torchaudio Biquad filters for EQ, eliminating UI freezes during playback.
*   **🤖 Conversational Agents:** The `OpenWebUI` node now supports a `History` input/output loop, allowing for multi-turn conversations and "Agentic" workflows.
*   **🛡️ Safety First:** Video Loaders now feature a "Frame Cap" (default 150 frames) to prevent immediate VRAM OOM crashes when loading large files.
*   **🎛️ Mixer Automation:** Mixer knobs and faders now visually detect when they are converted to inputs, locking the UI and displaying an "Automated" status.
*   **🚀 ACE-Step Preview:** Added a "Preview Mode" to the Music Generator for rapid 10-second iteration.

---

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    cd ComfyUI/custom_nodes/
    git clone https://github.com/pkeffect/ComfyUI-Internode.git
    ```

2.  **Install Dependencies:**
    ComfyUI should automatically install the core requirements. If not, run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **System Requirements:**
    *   **FFmpeg:** Required for loading MP3/MP4 files (add to your system PATH).
    *   **OpenWebUI:** (Optional) Required only if using the LLM/Agent nodes.
    *   **Demucs:** (Optional) The Stem Splitter will download models on first run.

---

## 🎚️ Node Breakdown & Usage Guide

### 1. Audio Mixing & DSP
**Nodes:** `InternodeAudioMixer`, `InternodeAudioMixer8`

A fully functional mixing console inside ComfyUI. Unlike standard "Save Audio" nodes, this allows you to process signals *before* saving.

*   **Features:**
    *   **3-Band EQ:** Torchaudio-based Low/Mid/High isolation.
    *   **Dynamics:** Noise Gate (remove background hiss) and Compressor (even out volume).
    *   **Time FX:** Vectorized Delay/Echo with Feedback and Mix controls.
    *   **Master Bus:** Drive (Saturation), LowCut/HiCut filters, and Ceiling limiter.
*   **Usage Scenario:**
    *   **Podcasting:** Connect a TTS node to Track 1 (Voice) and a generated music track to Track 2. Use the Mixer to balance levels, EQ the voice for clarity, and add a slight compression to "glue" the mix.
    *   **Automation:** Right-click `vol_1` -> *Convert to Input*. Connect an LFO node to fade music in and out automatically.

### 2. Audio Tools
**Nodes:** `InternodeSidechain`, `InternodeStemSplitter`, `InternodeAudioAnalyzer`

*   **InternodeSidechain:**
    *   **What it does:** Lowers the volume of input A (Music) whenever input B (Voice) exceeds a threshold.
    *   **Usage:** Essential for "Ducking". Keeps background music loud during silence but quiet when a character is speaking.
*   **InternodeStemSplitter:**
    *   **What it does:** Uses **Demucs** to split a song into 4 tracks: Drums, Bass, Vocals, Other.
    *   **Usage:** Extract vocals from a song to use with RVC (Voice Conversion) or extract Drums to drive an AnimateDiff video.
*   **InternodeAudioAnalyzer:**
    *   **What it does:** GPU-accelerated spectral analysis. Returns 4 float curves: Bass, Mid, High, Volume.
    *   **Usage:** **Audio-Reactive Video.** Connect the `bass_curve` output to the `scale` or `noise` input of a KSampler/AnimateDiff node to make the video "pulse" to the kick drum.

### 3. ACE-Step Music Generation
**Nodes:** `InternodeAceStepLoader`, `InternodeAceStepGenerator`

A wrapper for the ACE-Step text-to-music model.

*   **InternodeAceStepGenerator:**
    *   **Inputs:** Prompt, Lyrics, Duration, Steps, Seeds.
    *   **New Feature:** `preview_mode` (Boolean). When enabled, ignores duration/steps and generates a 10s clip at 20 steps. Great for testing prompts quickly.
    *   **Usage:** Generate unique, royalty-free background music for your AI videos directly within the workflow.

### 4. OpenWebUI (LLM Agents)
**Nodes:** `Internode_OpenWebUINode`, `Internode_OpenWebUIServerConfig`

Connects ComfyUI to a local or remote **OpenWebUI** instance (Ollama, vLLM, etc.).

*   **Internode_OpenWebUINode:**
    *   **Inputs:** `prompt`, `image` (Vision), `history` (Context Loop).
    *   **Outputs:** `text` (Response), `history` (Updated Context).
    *   **Usage:**
        *   **Vision Captioning:** Send a generated image to a Vision model (LLaVA) to get a detailed critique.
        *   **Prompt Refinement:** Send a simple prompt ("A cat") to Llama 3 to get a detailed Stable Diffusion prompt.
        *   **Agent Loops:** Connect `history` output back to `history` input (using a feedback/loop node) to have the LLM "remember" the conversation over multiple generation steps.

### 5. Loaders & Utilities
**Nodes:** `InternodeVideoLoader`, `InternodeMarkdownNote`, `InternodeAudioSaver`

*   **InternodeVideoLoader:**
    *   **Safety:** Includes `frame_load_cap` to prevent crashing 8GB VRAM cards when loading 4K video.
    *   **Usage:** Loading source material for Vid2Vid workflows.
*   **InternodeMarkdownNote:**
    *   **Features:** A collapsible, rich-text editor on the canvas. Supports code blocks and tables.
    *   **Usage:** Write instructions for your workflow, document parameters, or leave to-do lists for yourself.
*   **InternodeAudioSaver:**
    *   **Features:** Supports WAV (16/24/32-float), FLAC, MP3, and OGG.
    *   **Usage:** The final step to save your mixed audio to disk.

---

## ⚠️ Common Issues & Troubleshooting

1.  **"Pedalboard/Demucs Not Found":**
    *   These libraries have complex system dependencies. If they fail to install, the specific nodes (VST Loader / Stem Splitter) will be disabled, but the rest of the suite will function.
    *   **Fix:** Ensure you are running a standard Python environment. On Linux/Docker, you may need `sudo apt-get install libsndfile1`.

2.  **Mixer UI Glitch:**
    *   If the Mixer looks broken, ensure you are on the latest version (`git pull`). v3.0.0+ fixes layout issues on HD screens.

3.  **Video Loader OOM:**
    *   If ComfyUI crashes loading a video, lower the `frame_load_cap` in the Video Loader node (try 50 or 100).

## License

MIT License.
Parts of the code (Demucs wrapper) utilize the Demucs project (MIT).
Audio DSP logic utilizes TorchAudio (BSD).