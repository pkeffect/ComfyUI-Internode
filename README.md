# ComfyUI-Internode

![Internode ComfyUI Custom Nodes](./images/screenshot.png)

![Version](https://img.shields.io/badge/Version-3.0.7-green?style=for-the-badge) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20MacOS-blue?style=for-the-badge) ![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)

**ComfyUI-Internode** is a comprehensive, professional-grade Audio & Multimodal Workstation designed specifically for the ComfyUI ecosystem. It fundamentally transforms ComfyUI from an image-generation tool into a full-fledged **Generative Digital Audio Workstation (DAW)**.

While standard audio nodes in ComfyUI typically offer simple playback or basic saving capabilities, Internode provides a complete signal processing pipeline. It integrates high-fidelity DSP mixing, VST3 plugin hosting, native AI music generation (ACE-Step), spectral editing, and advanced LLM orchestration.

## 🌟 Key Features at a Glance

*   **Integrated DAW Mixer:** 4 and 8-channel mixing consoles with per-track EQ, Compression, Gating, and Sends.
*   **Dual-Engine Architecture:** Real-time Web Audio API previews in the browser; Bit-perfect PyTorch rendering in the backend.
*   **VST3 Host:** Run industry-standard instruments (Serum, Kontakt) and effects (FabFilter, Valhalla) directly inside your node graph.
*   **AI Music Generation:** Native implementation of **ACE-Step** audio diffusion with LoRA and Lyric support.
*   **Audio Reactivity:** Drive video generation (AnimateDiff) with precise frequency analysis and beat detection.
*   **Spectral Editing:** Convert audio to images for "Audio Inpainting" using Stable Diffusion, then convert back to audio.
*   **Multimodal LLM:** Give eyes and ears to local LLMs (Ollama/LocalAI) for complex analysis and prompt engineering.

---

## 📋 Table of Contents

1.  [📥 Installation & Setup](#-installation--setup)
    *   [Cloning the Repository](#1-cloning-the-repository)
    *   [Dependency Management](#2-dependency-management)
    *   [System Prerequisites (FFmpeg & VSTs)](#3-system-prerequisites)
2.  [🏗️ System Architecture](#-system-architecture)
    *   [The Dual-Engine Concept](#the-dual-engine-concept)
    *   [Data Flow](#data-flow)
3.  [🎛️ Section 1: The DSP Mixing Engine](#-section-1-the-dsp-mixing-engine)
    *   [The Channel Strip](#the-channel-strip)
    *   [The Master Bus](#the-master-bus)
    *   [Media Loaders & Savers](#media-loaders--savers)
4.  [🔌 Section 2: VST3 Integration (The Studio)](#-section-2-vst3-integration-the-studio)
    *   [VST Instruments (MIDI)](#vst-instruments-midi)
    *   [VST Effects](#vst-effects)
    *   [Parameter Automation](#parameter-automation)
5.  [🎼 Section 3: AI Music Generation (ACE-Step)](#-section-3-ai-music-generation-ace-step)
6.  [📊 Section 4: Audio Reactivity & Video Sync](#-section-4-audio-reactivity--video-sync)
7.  [🌈 Section 5: Spectral Manipulation (Audio Inpainting)](#-section-5-spectral-manipulation-audio-inpainting)
8.  [🤖 Section 6: OpenWebUI (LLM Integration)](#-section-6-openwebui-llm-integration)
9.  [🛠️ Section 7: Utilities & Audio Tools](#-section-7-utilities--audio-tools)
10. [📚 Workflow Scenarios](#-workflow-scenarios)
11. [⚠️ Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 📥 Installation & Setup

### 1. Cloning the Repository
Navigate to your ComfyUI custom nodes directory via your terminal or command prompt:

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/pkeffect/ComfyUI-Internode.git
```

### 2. Dependency Management
Internode relies on specialized audio processing libraries (`pedalboard`, `torchaudio`, `mido`, `diffusers`, `scipy`) that are generally not included in a standard ComfyUI installation.

**⚠️ IMPORTANT:** Do not just run `pip install`. ComfyUI (especially on Windows) often uses an embedded Python environment. You must install dependencies into *that specific environment*. We provide a script to handle this automatically.

#### **Option A: Windows (Standalone / Portable ComfyUI)**
If you downloaded the official `.zip` release of ComfyUI:
1.  Open `cmd` or PowerShell.
2.  Navigate to the Internode folder:
    ```cmd
    cd ComfyUI\custom_nodes\ComfyUI-Internode
    ```
3.  Run the installer using the embedded python executable:
    ```cmd
    ..\..\python_embeded\python.exe install.py
    ```

#### **Option B: Standard Python (Linux / Mac / venv)**
If you installed ComfyUI manually into a virtual environment (venv) or Conda environment:
1.  Activate your environment.
2.  Navigate to the folder:
    ```bash
    cd ComfyUI/custom_nodes/ComfyUI-Internode
    ```
3.  Run the installer:
    ```bash
    python install.py
    ```

### 3. System Prerequisites

#### **FFmpeg (Crucial)**
Internode uses `pydub` and `torchaudio` for media handling. These libraries rely on FFmpeg to decode compressed audio formats (MP3, AAC, OGG, FLAC) and to extract audio streams from Video files (MP4, MKV, MOV).
*   **Without FFmpeg:** You will **only** be able to load uncompressed `.wav` files. Loading an MP3 will result in a generic error or silence.

**How to Install FFmpeg:**
*   **Windows:**
    1.  Download the "gyan.dev" full build from [ffmpeg.org](https://ffmpeg.org/download.html).
    2.  Extract the ZIP file.
    3.  Copy the path to the `bin` folder (e.g., `C:\ffmpeg\bin`).
    4.  Search Windows for "Edit the system environment variables" -> Environment Variables.
    5.  Edit the `Path` variable and add the path to the `bin` folder.
    6.  Restart ComfyUI.
*   **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```
*   **MacOS:**
    ```bash
    brew install ffmpeg
    ```

#### **VST3 Plugins (Optional)**
To utilize the VST Host capabilities, you must have **64-bit VST3** plugins installed on your system. Internode automatically scans the standard system paths.
*   **Windows:** `C:\Program Files\Common Files\VST3`
*   **MacOS:** `/Library/Audio/Plug-Ins/VST3`
*   **Linux:** `/usr/lib/vst3` or `~/.vst3`

> **Note:** VST2 (`.dll`) plugins are **not supported**. 32-bit plugins are **not supported**.

---

## 🏗️ System Architecture

### The Dual-Engine Concept
One of the biggest challenges in Node-based audio is the delay between changing a parameter and hearing the result. Internode solves this with a split architecture:

1.  **The Frontend (Interactive Preview):**
    *   The custom UI widgets (Mixer, Knobs) are written in Javascript.
    *   They utilize the browser's native **Web Audio API**.
    *   When you drag a slider, the browser applies a digital filter *locally* to the audio preview. This provides **zero-latency feedback**. You hear the EQ change instantly.

2.  **The Backend (High-Fidelity Render):**
    *   When you press "Queue Prompt", the Python backend takes over.
    *   It uses **PyTorch** and **Torchaudio** to perform mathematical operations on the audio tensors.
    *   It uses **Pedalboard** to host VSTs.
    *   This ensures the final output is studio-quality, sample-accurate, and rendered offline (allowing for processing chains that might be too heavy for real-time playback).

> **Disclaimer:** Because the Web Audio API (Chrome/Firefox) and PyTorch are different audio engines, there may be extremely subtle differences in the sound (specifically filter Q-curves or compressor attack times) between what you hear in the preview and the final saved file. Always trust the final render for critical mastering work.

---

## 🎛️ Section 1: The DSP Mixing Engine

The `InternodeAudioMixer` nodes act as the central hub of your audio workflow.

### The Channel Strip
Each input track (1 through 4 or 8) passes through a complete channel strip signal chain.

*   **`vol_x` (Volume Fader):**
    *   Controls the level of the channel.
    *   Range: `0.0` (Silent) to `1.5` (+50% boost).
    *   *Default:* `0.75` (approx -3dB headroom).
*   **`pan_x` (Panorama):**
    *   Places the sound in the stereo field.
    *   Range: `-1.0` (Hard Left) to `1.0` (Hard Right). `0.0` is Center.
*   **`mute_x` / `solo_x`:**
    *   **Mute:** Silences the track.
    *   **Solo:** Silences all *other* tracks. (Useful for critical listening).
*   **`gate_x` (Noise Gate):**
    *   Automatically mutes the channel when the volume falls below this threshold.
    *   *Use Case:* Cleaning up background hiss from TTS (Text-to-Speech) generations or microphone recordings.
*   **`comp_x` (Compressor):**
    *   Reduces the dynamic range (the difference between the loudest and quietest parts).
    *   Higher values make the track sound "tighter," "punchier," and consistent in volume.
*   **3-Band EQ (Equalizer):**
    *   **`eq_low_x`**: Low Shelf Filter (~250Hz). Boosts or cuts bass/kick frequencies.
    *   **`eq_mid_x`**: Peaking Filter (~1000Hz). Affects vocals, snare presence, and intelligibility.
    *   **`eq_high_x`**: High Shelf Filter (~4000Hz). Affects "air," hi-hats, and sibilance.
    *   *Algorithm:* Uses Serial Biquad Filters for phase-coherent processing.
*   **Delay Send:**
    *   **`d_time_x`**: Time between echoes (in seconds).
    *   **`d_fb_x` (Feedback)**: How many times the echo repeats before fading out.
    *   **`d_mix_x`**: The Dry/Wet blend. `0.0` is no delay, `1.0` is pure echo.
    *   **`d_echo_x`**: Internal buffer size for the echo kernel (optimization parameter).

### The Master Bus
After all channels are summed together, they pass through the Master Bus for final polishing.

*   **`master_drive` (Saturation):**
    *   Adds tube-like harmonic distortion.
    *   *Use Case:* "Gluing" a mix together or making a clean digital synth sound gritty and analog.
*   **`master_locut` (High-Pass Filter):**
    *   Cuts frequencies *below* this value (e.g., 20Hz).
    *   *Use Case:* Removing inaudible sub-bass rumble that eats up headroom.
*   **`master_hicut` (Low-Pass Filter):**
    *   Cuts frequencies *above* this value (e.g., 20kHz).
    *   *Use Case:* Removing digital aliasing or ultrasonic noise.
*   **`master_width` (Stereo Imager):**
    *   `0.0`: Forces the mix to Mono (checks phase compatibility).
    *   `1.0`: Normal Stereo.
    *   `> 1.0`: Widens the stereo image by boosting the Side signal relative to the Mid signal.
*   **`master_ceil` (Limiter Ceiling):**
    *   A brickwall limiter that prevents the audio from exceeding this level.
    *   *Crucial:* Prevents digital clipping (nasty distortion) when summing multiple loud tracks.

### Outputs
The Mixer provides two audio outputs for flexible routing:
1.  **`master_output`**: The final production-ready mix. Contains all EQ, Compression, and Master Bus effects. Connect this to `Audio Saver`.
2.  **`pre_master_output`**: The raw sum of all channels *before* the Master Bus effects are applied.
    *   *Use Case:* Connect this to a `InternodeVST3Effect` node loaded with iZotope Ozone or a dedicated mastering plugin if you prefer third-party mastering over the built-in Master Bus.

### Media Loaders & Savers

#### **`InternodeAudioLoader`**
*   **`audio_file`**: Drag and drop support.
*   **`normalize`**: If enabled, boosts the audio peak to -0.1dB.
*   **`mono_to_stereo`**: If the input file is Mono (1 channel), it duplicates it to Stereo (2 channels) to ensure compatibility with VSTs and the Mixer.

#### **`InternodeVideoLoader`**
Designed for heavy video files.
*   **`load_audio`**: Toggle to extract the audio track.
*   **`frame_load_cap`**: **CRITICAL PARAMETER.** Loading video frames into uncompressed tensors consumes massive RAM (approx 20MB per frame at 1080p).
    *   *Default:* 150 frames.
    *   *Usage:* Increase cautiously based on your system RAM.
*   **`resize_mode`**: Downscales video on load (e.g., to 512x512). Use this if you are using the video frames for ControlNet or AnimateDiff, as full 4K resolution is usually unnecessary for conditioning.

#### **`InternodeAudioSaver`**
*   **`filename_prefix`**: Subfolder/Filename pattern.
*   **`format`**:
    *   **WAV (16-bit):** Standard CD quality.
    *   **WAV (24-bit):** Studio standard.
    *   **WAV (32-bit Float):** High dynamic range (impossible to clip internally).
    *   **FLAC:** Lossless compression.
    *   **MP3/AAC/OGG:** Compressed formats for web delivery.

---

## 🔌 Section 2: VST3 Integration (The Studio)

This section turns ComfyUI into a plugin host.

### VST Instruments (MIDI)
**Node:** `InternodeVST3Instrument`

Unlike effect plugins that process audio, Instruments *generate* audio from MIDI data.

*   **Inputs:**
    *   **`midi_data`**: Requires a connection from `InternodeMidiLoader`.
    *   **`vst_path`**: Absolute path to a valid `.vst3` instrument (e.g., Serum, Vital, Kontakt, Omnisphere).
    *   **`sample_rate`**: The output quality.
    *   **`duration_padding`**: Adds seconds of silence after the last MIDI note ends. This captures the decay of reverb or delay tails that would otherwise be cut off.

### VST Effects
**Node:** `InternodeVST3Effect`

Processes an incoming audio stream.

*   **Inputs:**
    *   **`audio`**: The waveform to process.
    *   **`vst_path`**: Absolute path to a `.vst3` effect (e.g., FabFilter Pro-Q, Valhalla Reverb, distortion, chorus).
    *   **`dry_wet`**: A global mix knob for the plugin.
        *   `0.0`: Bypassed (Original signal).
        *   `0.5`: 50% Original / 50% Effect.
        *   `1.0`: 100% Wet (Effect only).

### Parameter Automation
**Node:** `InternodeVST3Param`

This is where the magic happens. You can control VST knobs using ComfyUI logic (Floats, LFOs, Audio Reactive Curves).

**Step-by-Step Automation Guide:**
1.  **Identify the Parameter:** Create an `InternodeVST3Info` node. Paste your VST path into it and preview the output string. It will list every available parameter name (e.g., *"Filter Cutoff"*, *"Resonance"*, *"Mix"*).
2.  **Configure Automation:** Create an `InternodeVST3Param` node.
    *   **`param_name`**: Paste the *exact* name found in step 1.
    *   **`value`**: Connect a Float node (or a batch of Floats/Curve) here.
3.  **Connect:** Wire the `VST3Param` node into the `param_1`, `param_2`, etc., slots on the Instrument or Effect node.

**Example:** Using the "Kick Drum" audio curve to modulate the "Threshold" of a Distortion plugin on a Bass track.

---

## 🎼 Section 3: AI Music Generation (ACE-Step)

**Node:** `InternodeAceStepGenerator`

This node runs the **ACE-Step** latent diffusion model locally on your GPU to generate music.

*   **`prompt`**: Describes the genre, mood, instrumentation, and tempo.
    *   *Effective Prompting:* "Techno, 140 BPM, Dark, Industrial, Aggressive Bass, SynthesizerArp"
*   **`lyrics`**: (Experimental) Input text for the model to attempt to sing/rap. Adherence varies by seed.
*   **`preview_mode` (Toggle)**:
    *   **ON (True):** Generates 10 seconds of audio at only 20 inference steps. This is extremely fast and meant for "prompt surfing" to find a good seed.
    *   **OFF (False):** Generates the full `audio_duration` at the full `infer_step` count. Use this for the final render.
*   **`infer_step`**: The number of denoising steps.
    *   *Draft:* 20-30.
    *   *Standard:* 50.
    *   *High Quality:* 100+.
*   **`guidance_scale`**: The CFG (Classifier Free Guidance) scale. Controls how strictly the model adheres to your prompt versus creative freedom.
    *   *Range:* 5.0 to 15.0 is usually the sweet spot.
*   **`lora_name_or_path`**: Loads a `.safetensors` LoRA model to shift the style (e.g., "Chinese Rap LoRA", "Anime Voice LoRA").

---

## 📊 Section 4: Audio Reactivity & Video Sync

These nodes are essential for AI Music Video creation. They translate sound into data that video generators (AnimateDiff, ControlNet) can understand.

### **`InternodeAudioToKeyframes`**

*   **`fps`**: Set this to match your video project (e.g., 24, 30, 60). It ensures the output curve aligns perfectly frame-by-frame.
*   **`mode`**:
    *   **RMS (Volume):** Measures total energy. Good for global intensity, camera zoom, or noise strength.
    *   **Low (Bass/Kick):** (20Hz - 250Hz). Good for syncing motion to the beat/kick drum.
    *   **Mid (Vocals):** (250Hz - 4kHz). Good for reacting to lyrics or snare drums.
    *   **High (Hats):** (4kHz+). Good for reacting to cymbals/shakers (jittery motion).
    *   **Beat (Trigger):** A transient detector. It outputs a binary `1.0` (Hit) or `0.0` (No Hit). Excellent for hard cuts or triggering scene changes.
*   **`smoothing`**: Applies an Exponential Moving Average to smooth out jittery values. Higher values = slower, smoother curves.
*   **`amp_scale`**: Multiplies the result. If your curve is too subtle, turn this up.
*   **`y_offset`**: Adds a base value. E.g., if you are controlling "Motion Scale" and want a minimum movement of 0.5, set this to 0.5.

**Outputs:**
1.  **`float_curve`**: A raw list/batch of floats. Connect this to "Batch Float" nodes.
2.  **`schedule_str`**: A formatted text string compatible with **ComfyUI-Advanced-ControlNet** (Value Scheduling).
    *   *Format:* `0:(0.1), 1:(0.5), 2:(0.3)...`
3.  **`curve_image`**: A generated graph image. Preview this to visually verify that your beats are syncing before you spend hours rendering video.

---

## 🌈 Section 5: Spectral Manipulation (Audio Inpainting)

This workflow allows you to edit audio using Image Editing techniques.

### The Concept
1.  **Audio -> Image:** We convert the audio into a Spectrogram. Time is on the X-axis, Frequency (Pitch) is on the Y-axis, and Color is Loudness.
2.  **Image Processing:** You can now use **ComfyUI Inpainting nodes** (MaskEditor + KSampler). You visually identify an unwanted sound (like a siren, which looks like a bright wavy line) and mask it out.
3.  **Image -> Audio:** We convert the modified image back into sound.

### Nodes
*   **`InternodeSpectrogram`**:
    *   **`n_fft`**: The FFT window size.
        *   *Higher (2048+):* Better frequency detail (you can see individual notes), but blurry timing.
        *   *Lower (512):* Better timing (sharp drum hits), but blurry frequency.
    *   **`hop_length`**: How often we sample the window. Controls the width of the resulting image.
*   **`InternodeImageToAudio`**:
    *   Uses the **Griffin-Lim** algorithm to estimate phase information (since standard images don't contain phase data).
    *   **`n_iter`**: The number of reconstruction passes. Higher (64+) results in less robotic/metallic artifacts but takes longer to process.
    *   **`amp_scale`**: Boosts the signal volume during reconstruction to recover dynamic range.

---

## 🤖 Section 6: OpenWebUI (LLM Integration)

This node allows you to connect ComfyUI to a running instance of **OpenWebUI** (which can front-end Ollama, LocalAI, vLLM, or OpenAI).

### **`Internode_OpenWebUINode`**

*   **Context Aware (Memory):** Unlike standard prompt nodes, this node accepts a `history` input. By creating a feedback loop (passing the output history back into the input), the LLM can remember previous instructions, allowing for multi-turn iterative refinement of prompts.
*   **Multimodal Vision:** If you connect an `IMAGE` to this node, it automatically converts it to a Base64 string and sends it to the API.
    *   *Scenario:* Connect a "Preview Image" from a generation to this node. Ask the LLM: *"What is wrong with this image?"*. The LLM (using LLaVA or similar) can critique the generation.

### **`OpenWebUI Server Config`**
*   **`host`**: The URL of your API (e.g., `http://localhost:11434` for Ollama).
*   **`api_key`**: Required if you are connecting to a remote server or OpenAI. Leave blank for local Ollama.

---

## 🛠️ Section 7: Utilities & Audio Tools

### **`InternodeMarkdownNote`**
A persistent text editor for documenting your complex workflows.
*   **Persistence:** Text entered here is saved inside the workflow `.json` metadata. It survives page reloads.
*   **Security:** Includes a sanitizer that strips malicious Javascript vectors (`<script>`, `onclick`) to ensure shared workflows are safe to open.

### **`InternodeSidechain` (The Ducker)**
A mixing utility essential for voiceovers. It lowers the volume of the `music` input whenever signal is detected on the `voice` input.
*   **`threshold`**: Sensitivity. Lower values trigger ducking more easily.
*   **`ratio`**: Compression strength. `4.0` means the music is reduced by a factor of 4.
*   **`attack`**: How quickly the music fades out when the voice starts. (Fast = 10ms).
*   **`release`**: How slowly the music fades back in after the voice stops. (Slow = 500ms).

### **`InternodeStemSplitter`**
Uses the **Demucs** Hybrid Transformer model to un-mix a song.
*   Takes a full song as input.
*   Outputs 4 separate audio streams: **Drums**, **Bass**, **Vocals**, **Other** (Melody).
*   *Note:* This requires significant VRAM/RAM.

---

## ⚠️ Troubleshooting & FAQ

### 🔴 Problem: My nodes are red and say "Missing Dependencies"
**Solution:** You missed the installation step.
1.  Close ComfyUI.
2.  Open a terminal in `ComfyUI/custom_nodes/ComfyUI-Internode`.
3.  Run `python install.py` (or `..\..\python_embeded\python.exe install.py` on standalone Windows).
4.  Restart ComfyUI.

### 🔴 Problem: I can only load WAV files. MP3/Video fails.
**Solution:** FFmpeg is missing from your system.
1.  Download FFmpeg.
2.  Add it to your System PATH environment variable.
3.  Restart ComfyUI (and potentially your PC to flush path cache).

### 🟠 Problem: The Mixer UI sounds slightly different from the `Audio Saver` file.
**Reason:** The UI uses the browser's lightweight **Web Audio API** for real-time previewing. The `Audio Saver` output uses **PyTorch/Torchaudio** for high-precision offline rendering.
**Solution:** This is expected behavior. The backend render is the "truth." Trust the saved file for critical dynamic range work.

### 🟠 Problem: VST Plugins aren't loading.
**Checklist:**
1.  Is the file extension `.vst3`? (We do not support `.dll` VST2).
2.  Is the plugin **64-bit**? (32-bit plugins will fail silently or crash).
3.  Is the path absolute? (e.g., `C:\Program Files\...`).
4.  Did you copy the path as a string? Ensure there are no surrounding quotes `"` in the text widget.

### 🟠 Problem: "Audio To Keyframes" graph is flat.
**Solution:**
1.  Check `amp_scale`. Your audio might be too quiet. Increase to 2.0 or 5.0.
2.  Check the `mode`. If you selected "High (Hats)" but your audio is a bass guitar, there is no data in that frequency band.

---

**ComfyUI-Internode**
*Built for the Audio AI Revolution.*
