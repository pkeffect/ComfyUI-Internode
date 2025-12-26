// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_mixer.js
// VERSION: 4.3.1 (Hotfix: Hide Standard Widgets)

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("%c#### Internode: Mixer UI v4.3.1 Loaded (UI Restoration)", "color: orange; font-weight: bold;");

// --- CONSTANTS ---
const DEFAULTS = {
    master_vol: 1.0,
    master_drive: 0.0,
    master_locut: 20.0,
    master_hicut: 20000.0,
    master_ceil: 1.0,
    master_gate: 0.0,
    master_comp: 0.0,
    master_eq: 1.0,
    master_bal: 0.0,
    master_width: 1.0,
    master_mono: false,
    
    vol: 0.75,
    pan: 0.0,
    eq: 1.0,
    gate: 0.0,
    comp: 0.0,
    d_time: 0.35,
    d_fb: 0.4,
    d_mix: 0.0,
    d_echo: 4,
    mute: false,
    solo: false
};

// --- WEB AUDIO ENGINE ---
class MixerAudioEngine {
    constructor(channelCount) {
        this.ctx = null;
        this.channels = [];
        this.master = { 
            gain: null, comp: null, pan: null,
            eqLow: null, eqMid: null, eqHigh: null, 
            loCut: null, hiCut: null, drive: null,
            analyser: null 
        };
        this.isPlaying = false;
        this.channelCount = channelCount;
    }

    init() {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    async loadTrack(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error("Fetch failed");
            const arrayBuffer = await resp.arrayBuffer();
            return await this.ctx.decodeAudioData(arrayBuffer);
        } catch (e) {
            console.warn("Internode Mixer: Could not load track preview.", e);
            return null;
        }
    }

    async loadSources(node) {
        this.init();
        if (this.ctx.state === 'suspended') await this.ctx.resume();

        const promises = [];
        
        // Master Chain Setup
        this.master.loCut = this.ctx.createBiquadFilter(); this.master.loCut.type = "highpass";
        this.master.hiCut = this.ctx.createBiquadFilter(); this.master.hiCut.type = "lowpass";
        this.master.drive = this.ctx.createGain(); 
        
        this.master.comp = this.ctx.createDynamicsCompressor();
        
        this.master.eqLow = this.ctx.createBiquadFilter(); this.master.eqLow.type = "lowshelf";
        this.master.eqMid = this.ctx.createBiquadFilter(); this.master.eqMid.type = "peaking";
        this.master.eqHigh = this.ctx.createBiquadFilter(); this.master.eqHigh.type = "highshelf";
        
        this.master.pan = this.ctx.createStereoPanner();
        this.master.gain = this.ctx.createGain();
        this.master.analyser = this.ctx.createAnalyser(); this.master.analyser.fftSize = 256;
        
        this.master.loCut.connect(this.master.hiCut);
        this.master.hiCut.connect(this.master.comp);
        this.master.comp.connect(this.master.eqLow);
        this.master.eqLow.connect(this.master.eqMid);
        this.master.eqMid.connect(this.master.eqHigh);
        this.master.eqHigh.connect(this.master.pan);
        this.master.pan.connect(this.master.gain);
        this.master.gain.connect(this.master.analyser);
        this.master.analyser.connect(this.ctx.destination);

        // Channels
        for (let i = 1; i <= this.channelCount; i++) {
            const ch = {
                buffer: null, source: null,
                gain: this.ctx.createGain(), pan: this.ctx.createStereoPanner(),
                eqLow: this.ctx.createBiquadFilter(), eqMid: this.ctx.createBiquadFilter(), eqHigh: this.ctx.createBiquadFilter(),
                comp: this.ctx.createDynamicsCompressor(),
                delay: this.ctx.createDelay(2.0), delayFb: this.ctx.createGain(), delayMix: this.ctx.createGain(), delayDry: this.ctx.createGain(),
                analyser: this.ctx.createAnalyser()
            };

            ch.eqLow.type = "lowshelf"; ch.eqLow.frequency.value = 200;
            ch.eqMid.type = "peaking"; ch.eqMid.frequency.value = 1000;
            ch.eqHigh.type = "highshelf"; ch.eqHigh.frequency.value = 4000;
            ch.comp.ratio.value = 1; ch.comp.threshold.value = 0;

            ch.delay.connect(ch.delayFb); ch.delayFb.connect(ch.delay);
            ch.delayDry.connect(ch.eqLow); ch.delay.connect(ch.delayMix); ch.delayMix.connect(ch.eqLow);
            
            ch.eqLow.connect(ch.eqMid); ch.eqMid.connect(ch.eqHigh);
            ch.eqHigh.connect(ch.comp); ch.comp.connect(ch.pan);
            ch.pan.connect(ch.gain); ch.gain.connect(ch.analyser);
            
            ch.analyser.connect(this.master.loCut);

            this.channels[i] = ch;

            const inputSlot = node.inputs ? node.inputs.find(inp => inp.name === `track_${i}`) : null;
            if (inputSlot && inputSlot.link) {
                const linkId = inputSlot.link;
                const link = app.graph.links[linkId];
                if (link) {
                    const originNode = app.graph.getNodeById(link.origin_id);
                    if (originNode && originNode.type === "InternodeAudioLoader") {
                        const fileWidget = originNode.widgets ? originNode.widgets.find(w => w.name === "audio_file") : null;
                        if (fileWidget && fileWidget.value && fileWidget.value !== "none") {
                            const filename = encodeURIComponent(fileWidget.value);
                            const url = api.apiURL(`/view?filename=${encodeURIComponent(fileWidget.value)}&type=input`);
                            promises.push(this.loadTrack(url).then(buf => { ch.buffer = buf; }));
                        }
                    }
                }
            }
        }
        await Promise.all(promises);
    }

    start() {
        if (!this.ctx) return;
        this.channels.forEach((ch, i) => {
            if (ch && ch.buffer) {
                ch.source = this.ctx.createBufferSource();
                ch.source.buffer = ch.buffer;
                ch.source.connect(ch.delayDry); ch.source.connect(ch.delay);
                ch.source.start(0);
            }
        });
        this.isPlaying = true;
    }

    stop() {
        if (!this.ctx) return;
        this.channels.forEach(ch => {
            if (ch && ch.source) {
                try { ch.source.stop(); } catch(e){}
                ch.source.disconnect(); ch.source = null;
            }
        });
        this.isPlaying = false;
    }

    updateParams(node) {
        if (!this.ctx) return;
        const now = this.ctx.currentTime;

        const getVal = (name, def) => {
             const w = node.widgets ? node.widgets.find(x => x.name === name) : null;
             return w ? w.value : def;
        };

        const mVol = getVal("master_vol", DEFAULTS.master_vol);
        const mComp = getVal("master_comp", DEFAULTS.master_comp);
        const mEqH = getVal("master_eq_high", DEFAULTS.master_eq);
        const mEqM = getVal("master_eq_mid", DEFAULTS.master_eq);
        const mEqL = getVal("master_eq_low", DEFAULTS.master_eq);
        const mBal = getVal("master_balance", DEFAULTS.master_bal);
        const mLoCut = getVal("master_locut", DEFAULTS.master_locut);
        const mHiCut = getVal("master_hicut", DEFAULTS.master_hicut);
        
        if(this.master.gain) this.master.gain.gain.setTargetAtTime(mVol, now, 0.05);
        if(this.master.pan) this.master.pan.pan.setTargetAtTime(mBal, now, 0.05);
        
        if(this.master.loCut) this.master.loCut.frequency.setTargetAtTime(mLoCut, now, 0.05);
        if(this.master.hiCut) this.master.hiCut.frequency.setTargetAtTime(mHiCut, now, 0.05);
        
        if(this.master.comp) {
            if(mComp > 0) {
                this.master.comp.threshold.setTargetAtTime(-5 - (mComp * 25), now, 0.1);
                this.master.comp.ratio.setTargetAtTime(1 + (mComp * 4), now, 0.1);
            } else {
                this.master.comp.ratio.setTargetAtTime(1, now, 0.1);
            }
        }
        
        if(this.master.eqLow) {
            this.master.eqLow.gain.setTargetAtTime(20 * Math.log10(Math.max(0.01, mEqL)), now, 0.05);
            this.master.eqMid.gain.setTargetAtTime(20 * Math.log10(Math.max(0.01, mEqM)), now, 0.05);
            this.master.eqHigh.gain.setTargetAtTime(20 * Math.log10(Math.max(0.01, mEqH)), now, 0.05);
        }

        for(let i=1; i<=this.channelCount; i++) {
            const ch = this.channels[i];
            if(!ch) continue;

            const vol = getVal(`vol_${i}`, DEFAULTS.vol);
            const pan = getVal(`pan_${i}`, DEFAULTS.pan);
            const mute = getVal(`mute_${i}`, DEFAULTS.mute);
            const solo = getVal(`solo_${i}`, DEFAULTS.solo);
            const eql = getVal(`eq_low_${i}`, DEFAULTS.eq);
            const eqm = getVal(`eq_mid_${i}`, DEFAULTS.eq);
            const eqh = getVal(`eq_high_${i}`, DEFAULTS.eq);
            const comp = getVal(`comp_${i}`, DEFAULTS.comp);
            const dt = getVal(`d_time_${i}`, DEFAULTS.d_time);
            const df = getVal(`d_fb_${i}`, DEFAULTS.d_fb);
            const dm = getVal(`d_mix_${i}`, DEFAULTS.d_mix);

            let anySolo = false;
            for(let j=1; j<=this.channelCount; j++) {
                 if (getVal(`solo_${j}`, false)) anySolo = true;
            }
            
            let effVol = vol;
            if (anySolo) { if(!solo) effVol = 0.0; } else if (mute) effVol = 0.0;

            ch.gain.gain.setTargetAtTime(effVol, now, 0.05);
            ch.pan.pan.setTargetAtTime(pan, now, 0.05);
            ch.eqLow.gain.setTargetAtTime(20 * Math.log10(Math.max(0.01, eql)), now, 0.05);
            ch.eqMid.gain.setTargetAtTime(20 * Math.log10(Math.max(0.01, eqm)), now, 0.05);
            ch.eqHigh.gain.setTargetAtTime(20 * Math.log10(Math.max(0.01, eqh)), now, 0.05);

            if (comp > 0) {
                ch.comp.threshold.setTargetAtTime(-5 - (comp * 25), now, 0.1);
                ch.comp.ratio.setTargetAtTime(1 + (comp * 4), now, 0.1);
            } else {
                ch.comp.ratio.setTargetAtTime(1, now, 0.1);
            }

            ch.delay.delayTime.setTargetAtTime(dt, now, 0.1);
            ch.delayFb.gain.setTargetAtTime(df, now, 0.1);
            ch.delayMix.gain.setTargetAtTime(dm, now, 0.1);
            ch.delayDry.gain.setTargetAtTime(1.0 - dm, now, 0.1);
        }
    }
    
    getLevels() {
        if(!this.isPlaying) return { channels: [], master: 0 };
        const res = { channels: [], master: 0 };
        const arr = new Uint8Array(128);
        for(let i=1; i<=this.channelCount; i++) {
            if(this.channels[i] && this.channels[i].analyser) {
                this.channels[i].analyser.getByteFrequencyData(arr);
                let sum=0; for(let j=0; j<arr.length; j++) sum+=arr[j];
                res.channels[i] = (sum/arr.length)/64;
            }
        }
        if(this.master.analyser) {
            this.master.analyser.getByteFrequencyData(arr);
            let sum=0; for(let j=0; j<arr.length; j++) sum+=arr[j];
            res.master = (sum/arr.length)/64;
        }
        return res;
    }
}

// --- UI COMPONENTS ---

function getParamStatus(node, paramName) {
    const widget = node.widgets ? node.widgets.find(w => w.name === paramName) : null;
    const input = node.inputs ? node.inputs.find(i => i.name === paramName) : null;
    return {
        widget: widget,
        input: input,
        isAutomated: !!(input && input.link),
        exists: !!(widget || input)
    };
}

function createMeter(height, node, volParamName, engine, channelIndex, isMaster=false) {
    const container = document.createElement("div");
    Object.assign(container.style, { width: "6px", height: `${height}px`, backgroundColor: "#000", display: "flex", flexDirection: "column-reverse", gap: "1px", padding: "1px", borderRadius: "2px", boxSizing: "border-box", flexShrink: "0" });
    const segments = [];
    for(let i=0; i<15; i++) {
        const seg = document.createElement("div");
        let color = i>12 ? "#f00" : i>10 ? "#ff0" : "#0f0";
        Object.assign(seg.style, { width: "100%", flex: "1", backgroundColor: color, opacity: "0.2", borderRadius: "1px", transition: "opacity 0.05s" });
        container.appendChild(seg);
        segments.push(seg);
    }
    const animate = () => {
        if(!container.isConnected) return;
        let signal = 0;
        if (engine && engine.isPlaying) {
            const levels = engine.getLevels();
            signal = isMaster ? levels.master : (levels.channels[channelIndex] || 0);
        } else {
            const status = getParamStatus(node, volParamName);
            const val = status.widget ? status.widget.value : DEFAULTS.vol;
            if(val > 0.01) signal = val * 0.1; 
        }
        signal = Math.min(1.0, Math.max(0, signal));
        const active = Math.floor(signal * 15);
        for(let i=0; i<15; i++) segments[i].style.opacity = (i < active) ? "1.0" : "0.2";
        requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
    return container;
}

function createMiniKnob(label, paramName, node, range=[0, 1], color="#aaa") {
    const wrapper = document.createElement("div");
    Object.assign(wrapper.style, { display: "flex", flexDirection: "column", alignItems: "center", margin: "1px 0", boxSizing: "border-box" });
    const knob = document.createElement("div");
    Object.assign(wrapper.style, { flexShrink: "0" });
    Object.assign(knob.style, { width: "18px", height: "18px", borderRadius: "50%", backgroundColor: "#222", border: "1px solid #444", position: "relative", cursor: "ns-resize", boxShadow: "inset 0 0 3px #000", touchAction: "none", boxSizing: "border-box" });
    const pointer = document.createElement("div");
    Object.assign(pointer.style, { width: "1px", height: "6px", backgroundColor: color, position: "absolute", top: "1px", left: "7px", transformOrigin: "50% 7px", boxSizing: "border-box" });
    knob.appendChild(pointer);
    const lbl = document.createElement("div");
    lbl.textContent = label;
    Object.assign(lbl.style, { fontSize: "8px", color: "#666", marginTop: "1px", fontFamily: "sans-serif", fontWeight: "bold", textAlign: "center", lineHeight: "1", boxSizing: "border-box", transform: "scale(0.9)" });
    
    const autoLbl = document.createElement("div");
    autoLbl.textContent = "A";
    Object.assign(autoLbl.style, { position: "absolute", top: "2px", left: "4px", fontSize: "10px", color: "#0af", fontWeight: "bold", display: "none", pointerEvents: "none" });
    knob.appendChild(autoLbl);

    wrapper.appendChild(knob);
    wrapper.appendChild(lbl);
    
    let currentVal = range[0];

    const updateVisual = () => {
        const status = getParamStatus(node, paramName);
        if (status.isAutomated) {
            autoLbl.style.display = "block";
            pointer.style.display = "none";
            knob.style.borderColor = "#08a";
            knob.style.cursor = "default";
            knob.title = `${label}: Automated`;
        } else {
            autoLbl.style.display = "none";
            pointer.style.display = "block";
            knob.style.borderColor = "#444";
            knob.style.cursor = "ns-resize";
            currentVal = status.widget ? status.widget.value : (DEFAULTS[paramName] ?? range[0]);
            const norm = (currentVal - range[0]) / (range[1] - range[0]);
            pointer.style.transform = `rotate(${(norm * 270) - 135}deg)`;
            knob.title = `${label}: ${currentVal.toFixed(2)}`;
        }
    };
    
    wrapper.refresh = updateVisual;
    updateVisual(); 
    
    let startY=0, startVal=0;
    const onMove = (e) => {
        const delta = startY - e.clientY;
        const multiplier = e.shiftKey ? 0.001 : 0.005; 
        const scale = (range[1] - range[0]);
        let newVal = startVal + (delta * multiplier * scale);
        newVal = Math.max(range[0], Math.min(range[1], newVal));
        
        const status = getParamStatus(node, paramName);
        if (status.widget && !status.isAutomated) {
            status.widget.value = newVal;
            currentVal = newVal; 
            updateVisual();
        }
    };
    const onUp = (e) => { window.removeEventListener("pointermove", onMove); window.removeEventListener("pointerup", onUp); if (knob.releasePointerCapture) knob.releasePointerCapture(e.pointerId); };
    const startDrag = (e) => { 
        const status = getParamStatus(node, paramName);
        if(status.isAutomated) return;
        e.stopPropagation(); e.preventDefault(); startY = e.clientY; startVal = currentVal; 
        if (knob.setPointerCapture) knob.setPointerCapture(e.pointerId); 
        window.addEventListener("pointermove", onMove); window.addEventListener("pointerup", onUp); 
    };

    knob.addEventListener("pointerdown", startDrag); 
    knob.addEventListener("dblclick", (e) => { 
        e.stopPropagation(); 
        const status = getParamStatus(node, paramName);
        if(status.isAutomated) return;
        currentVal = (range[0]+range[1])/2; 
        if(["High","Mid","Low","Width","Ceil"].includes(label)) currentVal=1.0; 
        if(["PAN","Bal","Drive","Gate","Comp"].includes(label)) currentVal=0.0;
        if(label==="LoCut") currentVal=20.0; if(label==="HiCut") currentVal=20000.0;
        if(status.widget) status.widget.value = currentVal;
        updateVisual(); 
    });
    knob.addEventListener("wheel", (e) => e.stopPropagation(), {passive: true});
    return wrapper;
}

function createKnob(label, paramName, node) { return createMiniKnob(label, paramName, node, [-1.0, 1.0], "#fff"); }

function createFader(paramName, node, height=120, isMaster=false) {
    const track = document.createElement("div");
    Object.assign(track.style, { width: "12px", height: "100%", minHeight: "60px", backgroundColor: "#111", border: "1px solid #333", borderRadius: "2px", position: "relative", margin: "0", cursor: "ns-resize", boxShadow: "inset 1px 1px 2px #000", touchAction: "none", boxSizing: "border-box" });
    const handle = document.createElement("div");
    Object.assign(handle.style, { width: "24px", height: "12px", backgroundColor: "#555", border: "1px solid #777", borderRadius: "2px", position: "absolute", left: "-7px", boxShadow: "0 2px 4px rgba(0,0,0,0.5)", backgroundImage: "linear-gradient(to bottom, #666, #444)", pointerEvents: "none", boxSizing: "border-box" });
    track.appendChild(handle);
    const autoInd = document.createElement("div");
    Object.assign(autoInd.style, { width: "100%", height: "100%", backgroundColor: "rgba(0, 170, 255, 0.2)", border: "1px solid #0af", display: "none", position: "absolute", top:0, left:0, pointerEvents:"none" });
    track.appendChild(autoInd);

    const def = isMaster ? DEFAULTS.master_vol : DEFAULTS.vol;
    let currentVal = def;
    const max = isMaster ? 2.0 : 1.5; 
    
    const updateVisual = () => {
        const status = getParamStatus(node, paramName);
        if (status.isAutomated) {
             handle.style.display = "none";
             autoInd.style.display = "block";
             track.style.cursor = "default";
             track.title = "Automated";
        } else {
             handle.style.display = "block";
             autoInd.style.display = "none";
             track.style.cursor = "ns-resize";
             currentVal = status.widget ? status.widget.value : def;
             const norm = (currentVal - 0) / (max - 0);
             handle.style.bottom = `calc(${Math.max(0,Math.min(100,norm*100))}% - 6px)`;
             track.title = `Volume: ${currentVal.toFixed(2)}`;
        }
    };
    track.refresh = updateVisual;
    updateVisual();

    let startY=0, startVal=0;
    const onMove = (e) => {
        const delta = startY - e.clientY;
        const multiplier = e.shiftKey ? 0.001 : 0.005;
        let newVal = startVal + (delta * multiplier);
        newVal = Math.max(0.0, Math.min(max, newVal));
        const status = getParamStatus(node, paramName);
        if(status.widget && !status.isAutomated) {
            status.widget.value = newVal;
            currentVal = newVal; 
            updateVisual();
        }
    };
    const onUp = (e) => { window.removeEventListener("pointermove", onMove); window.removeEventListener("pointerup", onUp); if(track.releasePointerCapture) track.releasePointerCapture(e.pointerId); };
    const startDrag = (e) => { 
        const status = getParamStatus(node, paramName);
        if(status.isAutomated) return;
        e.stopPropagation(); e.preventDefault(); startY = e.clientY; startVal = currentVal; 
        if(track.setPointerCapture) track.setPointerCapture(e.pointerId); 
        window.addEventListener("pointermove", onMove); window.addEventListener("pointerup", onUp); 
    };
    track.addEventListener("pointerdown", startDrag); 
    track.addEventListener("dblclick", (e) => { 
        e.stopPropagation(); 
        const status = getParamStatus(node, paramName);
        if(status.isAutomated) return;
        currentVal = def; 
        if(status.widget) status.widget.value = def; 
        updateVisual(); 
    });
    track.addEventListener("wheel", (e) => e.stopPropagation(), {passive: true});
    return track;
}

function createButton(label, paramName, node, color, onClick) {
    const btn = document.createElement("div");
    btn.textContent = label;
    Object.assign(btn.style, { width: "24px", height: "16px", backgroundColor: "#333", border: "1px solid #444", borderRadius: "3px", fontSize: "9px", color: "#888", textAlign: "center", lineHeight: "16px", cursor: "pointer", margin: "2px auto", fontFamily: "sans-serif", fontWeight:"bold", touchAction: "none", boxSizing: "border-box", flexShrink: "0" });
    if (onClick) {
        btn.addEventListener("pointerdown", (e) => {
            e.stopPropagation(); e.preventDefault();
            btn.style.backgroundColor = color;
            onClick();
            setTimeout(() => { btn.style.backgroundColor = "#333"; }, 200);
        });
    } else {
        let active = false;
        const update = () => {
            const status = getParamStatus(node, paramName);
            if (status.isAutomated) {
                btn.style.borderColor = "#08a";
                btn.style.color = "#0af";
                btn.textContent = "A"; 
                btn.style.cursor = "default";
                btn.style.boxShadow = "none";
                btn.style.backgroundColor = "#112";
            } else {
                btn.style.borderColor = "#444";
                btn.textContent = label;
                btn.style.cursor = "pointer";
                active = status.widget ? status.widget.value : false;
                if(active) { btn.style.backgroundColor = color; btn.style.color = "#222"; btn.style.boxShadow = `0 0 4px ${color}`; }
                else { btn.style.backgroundColor = "#2a2a2a"; btn.style.color = "#666"; btn.style.boxShadow = "none"; }
            }
        };
        btn.refresh = update;
        update();
        btn.addEventListener("pointerdown", (e) => {
            const status = getParamStatus(node, paramName);
            if(status.isAutomated) return;
            e.stopPropagation(); e.preventDefault();
            active = !active; 
            if(status.widget) status.widget.value = active;
            update();
        });
    }
    return btn;
}

function createDivider() {
    const div = document.createElement("div");
    Object.assign(div.style, { width: "80%", height: "1px", backgroundColor: "#444", margin: "4px 0", boxSizing: "border-box", flexShrink: "0" });
    return div;
}

function refreshUI(container) {
    const walk = (el) => {
        if(el.refresh) el.refresh();
        if(el.children) Array.from(el.children).forEach(walk);
    };
    walk(container);
}

// --- MIXER LAYOUT ---
function buildMixerUI(node, channelCount) {
    const engine = new MixerAudioEngine(channelCount);
    
    // UI HIDING FIX: Iterate all widgets and hide them from the view
    // so they don't clutter the node, but keep them for logic.
    if (node.widgets) {
        node.widgets.forEach(w => {
            // standard comyui way to hide widget: computeSize returns [0, -4]
            w.computeSize = () => [0, -4];
            // Optionally, we can set type to "hidden" but that might affect saving values
            // depending on Comfy version. computeSize is safest for visual hiding.
            // Some themes might need type="custom" to fully hide.
        });
    }

    const paramLoop = () => { 
        if(node.graph) {
            engine.updateParams(node);
            if (node.ui_container && node.ui_container.isConnected) {
                refreshUI(node.ui_container);
            }
        }
        requestAnimationFrame(paramLoop); 
    };
    requestAnimationFrame(paramLoop);

    const container = document.createElement("div");
    node.ui_container = container; 

    Object.assign(container.style, { 
        display: "flex", flexDirection: "row", 
        backgroundColor: "#111", borderRadius: "6px", padding: "8px", boxSizing: "border-box", gap: "4px", 
        width: "100%", height: "100%", 
        overflowX: "auto", overflowY: "hidden",
        alignItems: "stretch", touchAction: "none" 
    });
    
    const stop = (e) => e.stopPropagation();
    container.addEventListener("pointerdown", stop); 
    container.addEventListener("wheel", stop, {passive: true});

    const doReset = () => {
        if(confirm("Reset all mixer settings?")) {
            const resetVal = (name, val) => {
                 const status = getParamStatus(node, name);
                 if (status.widget && !status.isAutomated) status.widget.value = val;
            };
            for(let i=1; i<=channelCount; i++) {
                resetVal(`vol_${i}`, DEFAULTS.vol);
                resetVal(`pan_${i}`, DEFAULTS.pan);
                resetVal(`eq_low_${i}`, DEFAULTS.eq);
                resetVal(`eq_mid_${i}`, DEFAULTS.eq);
                resetVal(`eq_high_${i}`, DEFAULTS.eq);
                resetVal(`gate_${i}`, DEFAULTS.gate);
                resetVal(`comp_${i}`, DEFAULTS.comp);
                resetVal(`d_time_${i}`, DEFAULTS.d_time);
                resetVal(`d_fb_${i}`, DEFAULTS.d_fb);
                resetVal(`d_mix_${i}`, DEFAULTS.d_mix);
                resetVal(`d_echo_${i}`, DEFAULTS.d_echo);
                resetVal(`mute_${i}`, DEFAULTS.mute);
                resetVal(`solo_${i}`, DEFAULTS.solo);
            }
            resetVal("master_vol", DEFAULTS.master_vol);
            resetVal("master_gate", DEFAULTS.master_gate);
            resetVal("master_comp", DEFAULTS.master_comp);
            resetVal("master_eq_high", DEFAULTS.master_eq);
            resetVal("master_eq_mid", DEFAULTS.master_eq);
            resetVal("master_eq_low", DEFAULTS.master_eq);
            resetVal("master_balance", DEFAULTS.master_bal);
            resetVal("master_width", DEFAULTS.master_width);
            resetVal("master_drive", DEFAULTS.master_drive);
            resetVal("master_locut", DEFAULTS.master_locut);
            resetVal("master_hicut", DEFAULTS.master_hicut);
            resetVal("master_ceil", DEFAULTS.master_ceil);
            resetVal("master_mono", DEFAULTS.master_mono);
            
            node.setDirtyCanvas(true);
            refreshUI(container); 
        }
    };

    // CHANNELS
    for(let i=1; i<=channelCount; i++) {
        const strip = document.createElement("div");
        Object.assign(strip.style, { display: "flex", flexDirection: "column", flexGrow: "0", flexShrink: "0", minWidth: "46px", backgroundColor: "#1e1e1e", border: "1px solid #333", borderRadius: "4px", padding: "4px 0", boxSizing: "border-box", alignItems: "center", height: "100%" });
        const lbl = document.createElement("div");
        lbl.textContent = i;
        Object.assign(lbl.style, { textAlign: "center", color: "#fff", fontWeight: "bold", fontSize: "12px", marginBottom: "4px", boxSizing: "border-box", flexShrink: "0" });
        strip.appendChild(lbl);
        strip.appendChild(createMiniKnob("Time", `d_time_${i}`, node, [0.01, 2.0], "#0af"));
        strip.appendChild(createMiniKnob("Fdbk", `d_fb_${i}`, node, [0.0, 0.95], "#0af"));
        strip.appendChild(createMiniKnob("Mix", `d_mix_${i}`, node, [0.0, 1.0], "#0af"));
        strip.appendChild(createMiniKnob("Echo", `d_echo_${i}`, node, [1, 16], "#0af"));
        strip.appendChild(createDivider());
        strip.appendChild(createMiniKnob("Gate", `gate_${i}`, node, [0.0, 1.0], "#f50"));
        strip.appendChild(createMiniKnob("Comp", `comp_${i}`, node, [0.0, 1.0], "#fa0"));
        strip.appendChild(createDivider());
        strip.appendChild(createMiniKnob("High", `eq_high_${i}`, node, [0, 3]));
        strip.appendChild(createMiniKnob("Mid", `eq_mid_${i}`, node, [0, 3]));
        strip.appendChild(createMiniKnob("Low", `eq_low_${i}`, node, [0, 3]));
        strip.appendChild(createDivider());
        strip.appendChild(createKnob("PAN", `pan_${i}`, node));
        strip.appendChild(createButton("M", `mute_${i}`, node, "#f55"));
        strip.appendChild(createButton("S", `solo_${i}`, node, "#ee5"));
        
        const spacer = document.createElement("div");
        Object.assign(spacer.style, { height: "5px", flexShrink: "0" });
        strip.appendChild(spacer);
        const fRow = document.createElement("div");
        Object.assign(fRow.style, { display: "flex", justifyContent: "center", gap: "2px", marginBottom: "4px", flex: "1", minHeight: "0" });
        fRow.appendChild(createFader(`vol_${i}`, node, null, false)); 
        fRow.appendChild(createMeter("100%", node, `vol_${i}`, engine, i)); 
        strip.appendChild(fRow);
        container.appendChild(strip);
    }

    // MASTER
    const master = document.createElement("div");
    Object.assign(master.style, { display: "flex", flexDirection: "column", flexGrow: "0", flexShrink: "0", minWidth: "50px", backgroundColor: "#222", border: "1px solid #555", borderRadius: "4px", padding: "4px 0", marginLeft: "4px", boxSizing: "border-box", alignItems: "center", height: "100%", position: "sticky", right: "0", zIndex: "10" });
    const mLbl = document.createElement("div"); mLbl.textContent = "M"; Object.assign(mLbl.style, { textAlign: "center", color: "#ccc", fontWeight: "bold", fontSize: "12px", marginBottom: "4px", boxSizing: "border-box", flexShrink: "0" });
    master.appendChild(mLbl);
    const playBtn = document.createElement("div");
    playBtn.textContent = "▶";
    Object.assign(playBtn.style, { width: "24px", height: "24px", borderRadius: "50%", backgroundColor: "#333", border: "2px solid #555", color: "#0f0", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", fontSize: "12px", marginBottom: "6px", boxShadow: "0 2px 4px #000", flexShrink: "0" });
    playBtn.onclick = async () => { if(engine.isPlaying) { engine.stop(); playBtn.textContent="▶"; playBtn.style.color="#0f0"; playBtn.style.borderColor="#555"; } else { playBtn.textContent="⏳"; await engine.loadSources(node); engine.start(); playBtn.textContent="■"; playBtn.style.color="#f55"; playBtn.style.borderColor="#f55"; } };
    master.appendChild(playBtn);
    const btnRow = document.createElement("div");
    Object.assign(btnRow.style, { display: "flex", gap: "2px", marginBottom: "4px", flexShrink: "0" });
    btnRow.appendChild(createButton("R", "reset_trigger", node, "#fff", doReset));
    btnRow.appendChild(createButton("Mn", "master_mono", node, "#0af"));
    master.appendChild(btnRow);
    master.appendChild(createMiniKnob("Drive", "master_drive", node, [0.0, 1.0], "#d44"));
    master.appendChild(createMiniKnob("LoCut", "master_locut", node, [20.0, 200.0], "#888"));
    master.appendChild(createMiniKnob("HiCut", "master_hicut", node, [8000.0, 20000.0], "#888"));
    master.appendChild(createMiniKnob("Ceil", "master_ceil", node, [0.1, 1.0], "#d44"));
    master.appendChild(createDivider());
    master.appendChild(createMiniKnob("Gate", "master_gate", node, [0.0, 1.0], "#f50"));
    master.appendChild(createMiniKnob("Comp", "master_comp", node, [0.0, 1.0], "#fa0"));
    master.appendChild(createDivider());
    master.appendChild(createMiniKnob("High", "master_eq_high", node, [0, 3]));
    master.appendChild(createMiniKnob("Mid", "master_eq_mid", node, [0, 3]));
    master.appendChild(createMiniKnob("Low", "master_eq_low", node, [0, 3]));
    master.appendChild(createDivider());
    master.appendChild(createMiniKnob("Width", "master_width", node, [0, 2], "#fff"));
    master.appendChild(createMiniKnob("Bal", "master_balance", node, [-1, 1], "#fff"));
    const spacer = document.createElement("div");
    Object.assign(spacer.style, { height: "5px", flexShrink: "0" });
    master.appendChild(spacer);
    const mFaderRow = document.createElement("div");
    Object.assign(mFaderRow.style, { display: "flex", flexDirection: "row", justifyContent: "center", gap: "4px", marginBottom: "4px", flex: "1", minHeight: "0" });
    mFaderRow.appendChild(createMeter("100%", node, "master_vol", engine, 0, true)); 
    mFaderRow.appendChild(createFader("master_vol", node, null, true));
    mFaderRow.appendChild(createMeter("100%", node, "master_vol", engine, 0, true)); 
    master.appendChild(mFaderRow);
    container.appendChild(master);

    node.addDOMWidget("mixer_ui", "div", container, { serialize: false });
    
    // Resize node to fit custom UI
    const width = (channelCount * 54) + 70; 
    node.setSize([width, 680]); 
}

app.registerExtension({
    name: "Internode.AudioMixer",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeAudioMixer" || nodeData.name === "InternodeAudioMixer8") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                buildMixerUI(this, nodeData.name === "InternodeAudioMixer8" ? 8 : 4);
                
                // Keep configuration sync
                const originalConfigure = this.configure;
                this.configure = function(info) {
                    originalConfigure?.apply(this, arguments);
                }
                return r;
            };
        }
    }
});