// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_studio.js
// VERSION: 3.2.0 (Full Restoration)

import { app } from "../../scripts/app.js";

// --- EMBEDDED CSS (Exact Port from keys.css) ---
const STUDIO_STYLES = `
.internode-studio-root {
    --bg-body: #121212; --chassis: #0a0a0a; --panel-face: #1e1e1e; 
    --module-bg: #151515; --border-dark: #333; --text-dim: #aaa; 
    --text-bright: #e0e0e0; --accent-1: #00f2ff; --accent-2: #ffaa00; 
    --lcd-text: #aaffaa; --led-red: #ff3333; --led-green: #33ff33; 
    width: 100%; height: 100%; display: flex; flex-direction: column;
    font-family: 'Segoe UI', sans-serif; color: var(--text-dim);
    background: #000; overflow: hidden; position: relative;
}
.internode-studio-root * { box-sizing: border-box; user-select: none; }

/* LAYOUT */
.internode-studio-root .synth-chassis { display: flex; width: 100%; height: 100%; background: var(--chassis); }

.internode-studio-root .sidebar-master { 
    width: 200px; background: #111; border-right: 1px solid #222; 
    display: flex; flex-direction: column; padding: 10px; gap: 10px; flex-shrink: 0; height: 100%;
}
.internode-studio-root .rack-space { 
    flex-grow: 1; background: #1a1a1a; padding: 5px; gap: 5px; overflow: hidden;
    display: grid; grid-template-columns: 60px 1fr; grid-template-rows: auto 1fr auto 1fr;
}

/* GRID PLACEMENTS */
.internode-studio-root #deck-top-ctrl { grid-row: 1; grid-column: 1 / span 2; }
.internode-studio-root #meter-top-container { grid-row: 2; grid-column: 1; }
.internode-studio-root #manual-top { grid-row: 2; grid-column: 2; }
.internode-studio-root #deck-bot-ctrl { grid-row: 3; grid-column: 1 / span 2; margin-top: 5px; }
.internode-studio-root #meter-bot-container { grid-row: 4; grid-column: 1; }
.internode-studio-root #manual-bottom { grid-row: 4; grid-column: 2; }

/* MODULES */
.internode-studio-root .master-module { background: #181818; border: 1px solid var(--border-dark); border-radius: 4px; padding: 10px; display: flex; flex-direction: column; align-items: center; width: 100%; flex-shrink: 0; }
.internode-studio-root .spacer-panel { flex-grow: 1; background: #181818; border: 1px solid var(--border-dark); border-radius: 4px; min-height: 20px; }
.internode-studio-root .mod-header { width: 100%; text-align: center; font-size: 10px; letter-spacing: 2px; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 10px; color: var(--text-dim); font-weight: 700; }
.internode-studio-root .tall-module { height: 320px; justify-content: flex-start; }

/* KNOBS & FADERS */
.internode-studio-root .knob-grid { display: flex; width: 100%; justify-content: space-around; gap: 5px; }
.internode-studio-root .knob-unit { display: flex; flex-direction: column; align-items: center; gap: 3px; height: 100%; justify-content: flex-end; }
.internode-studio-root .knob-unit label { font-size: 8px; color: #888; font-weight:600; }
.internode-studio-root .knob { width: 34px; height: 34px; border-radius: 50%; background: conic-gradient(#333 0%, #111 100%); border: 1px solid #000; box-shadow: 0 3px 6px rgba(0,0,0,0.5); position: relative; cursor: ns-resize; flex-shrink: 0; }
.internode-studio-root .knob::after { content:''; position: absolute; top: 4px; left: 50%; width: 2px; height: 35%; background: #fff; transform: translateX(-50%); pointer-events: none; }
.internode-studio-root .knob.accent::after { background: var(--accent-1); box-shadow: 0 0 5px var(--accent-1); }
.internode-studio-root #b-vol::after { background: var(--accent-2); box-shadow: 0 0 5px var(--accent-2); }
.internode-studio-root .knob.small { width: 28px; height: 28px; }

/* OUTPUT SECTION */
.internode-studio-root .output-row { display: flex; width: 100%; justify-content: space-around; align-items: center; height: 100%; }
.internode-studio-root canvas.vu-meter-canvas { background: #080808; border: 2px solid #333; width: 45px; height: 250px; border-radius: 2px; }
.internode-studio-root .fader-track { width: 50px; height: 250px; background: #080808; border: 1px solid #333; position: relative; display: flex; justify-content: center; border-radius: 2px; box-shadow: inset 0 0 10px #000; }
.internode-studio-root .fader-track input[type=range] { -webkit-appearance: none; width: 240px; height: 50px; background: transparent; transform: rotate(-90deg); transform-origin: 50% 50%; position: absolute; top: 50%; left: 50%; margin-left: -120px; margin-top: -25px; z-index: 5; cursor: ns-resize; }
.internode-studio-root .fader-track input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 50px; width: 25px; background: linear-gradient(180deg, #000 0%, #333 10%, #222 50%, #000 100%); border: 1px solid #111; border-radius: 4px; position: relative; box-shadow: -5px 0 5px rgba(0,0,0,0.8); }

/* WHEELS */
.internode-studio-root .wheels-container { display: flex; gap: 10px; justify-content: center; width: 100%; }
.internode-studio-root .wheel-group { text-align: center; display: flex; flex-direction: column; align-items: center; }
.internode-studio-root .wheel-housing { width: 40px; height: 100px; background: #050505; border: 1px solid #333; border-radius: 4px; position: relative; overflow: hidden; }
.internode-studio-root .wheel { width: 30px; height: 120%; background: repeating-linear-gradient(0deg, #222, #222 2px, #333 3px, #333 5px); position: absolute; left: 4px; border-radius: 8px; cursor: ns-resize; top: -10%; }

/* DECKS */
.internode-studio-root .deck-container { background: var(--chassis); border: 1px solid #222; display: flex; flex-direction: column; position: relative; flex: 0 0 auto; }
.internode-studio-root .rack-ears { position: absolute; left: -22px; top: 60px; transform: rotate(-90deg); font-size: 10px; letter-spacing: 2px; color: #666; font-weight: 900; width: 80px; text-align: center; }
.internode-studio-root .bottom-ear { color: #855; }
.internode-studio-root .control-face { background: linear-gradient(180deg, #222, #1b1b1b); height: 170px; padding: 8px; display: flex; gap: 4px; align-items: center; border-bottom: 1px solid #000; flex-shrink: 0; overflow-x: auto; justify-content: space-between; }

.internode-studio-root .module { background: var(--module-bg); border: 1px solid #333; height: 100%; padding: 5px; border-radius: 2px; display: flex; flex-direction: column; align-items: center; min-width: 60px; flex-shrink: 0; justify-content: space-between; }
.internode-studio-root .module.wide-6 { min-width: 180px; flex-grow: 1; }
.internode-studio-root .module.half { width: 70px; }
.internode-studio-root .module-label { font-size: 9px; color: var(--text-dim); width: 100%; border-bottom: 1px solid #222; margin-bottom: 5px; padding-bottom: 2px; text-align: center; white-space: nowrap; letter-spacing: 1px; }

/* GRIDS */
.internode-studio-root .grid-2x2 { display: grid; grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(2, 1fr); gap: 5px; width: 100%; height: 100%; align-items: center; justify-items: center; }
.internode-studio-root .grid-2x4 { display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(2, 1fr); gap: 5px; width: 100%; height: 100%; align-items: center; justify-items: center; }
.internode-studio-root .grid-2x6 { display: grid; grid-template-columns: repeat(6, 1fr); grid-template-rows: repeat(2, 1fr); gap: 5px; width: 100%; height: 100%; align-items: center; justify-items: center; }
.internode-studio-root .grid-2x6 .fx-select:nth-of-type(1) { grid-column: 1 / span 3; grid-row: 1; }
.internode-studio-root .grid-2x6 .fx-select:nth-of-type(2) { grid-column: 4 / span 3; grid-row: 1; }
.internode-studio-root .grid-2x6 .knob-unit:nth-of-type(1) { grid-column: 1; grid-row: 2; }
.internode-studio-root .grid-2x6 .knob-unit:nth-of-type(2) { grid-column: 2; grid-row: 2; }
.internode-studio-root .grid-2x6 .knob-unit:nth-of-type(3) { grid-column: 4; grid-row: 2; }
.internode-studio-root .grid-2x6 .knob-unit:nth-of-type(4) { grid-column: 5; grid-row: 2; }

/* CONTROLS */
.internode-studio-root .wave-btn { background: #222; border: 1px solid #444; color: #888; font-size: 8px; cursor: pointer; width: 100%; height: 22px; transition: color 0.2s; }
.internode-studio-root .wave-btn.active[data-deck="top"] { background: var(--accent-1); color: #000; font-weight: bold; box-shadow: 0 0 5px var(--accent-1); }
.internode-studio-root .wave-btn.active[data-deck="bot"] { background: var(--accent-2); color: #000; font-weight: bold; box-shadow: 0 0 5px var(--accent-2); }
.internode-studio-root .oct-btn { background: linear-gradient(#333, #222); color: #ccc; }
.internode-studio-root .mini-toggle { background: #333; border: 1px solid #555; color: #ccc; font-size: 8px; width: 100%; cursor: pointer; padding: 2px; }
.internode-studio-root .fx-select { width: 100%; background: #000; border: 1px solid #444; color: #ccc; font-size: 9px; font-family: monospace; padding: 2px; }
.internode-studio-root .toggle-btn { background: #222; border: 1px solid #444; color: #ccc; width: 100%; height: 20px; font-size: 8px; cursor: pointer; border-radius: 2px; }
.internode-studio-root .rec-btn, .internode-studio-root .play-btn { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #333; background: #111; color: #777; cursor: pointer; font-size: 10px; display: flex; justify-content: center; align-items: center; }

.internode-studio-root .lcd-panel { background: #000; border: 2px solid #444; border-radius: 4px; padding: 2px; grid-column: span 2; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
.internode-studio-root .lcd-screen { font-family: monospace; color: var(--lcd-text); font-size: 18px; text-shadow: 0 0 5px var(--lcd-text); }
.internode-studio-root .accent-text { color: #ffaa55; text-shadow: 0 0 5px #ffaa55; }

/* DECK METERS */
.internode-studio-root .deck-meter { background: #111; border: 2px solid #333; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; padding: 5px; }
.internode-studio-root .deck-meter canvas { flex-grow: 1; width: 100%; height: 0 !important; min-height: 0; background: #000; border: 1px solid #222; margin-bottom: 5px; }
.internode-studio-root .meter-gain { height: 45px; flex-shrink: 0; width: 100%; justify-content: flex-end; }

/* KEYBOARDS */
.internode-studio-root .keys-wrapper { width: 100%; height: 100%; min-height: 120px; position: relative; background: #000; border-top: 4px solid #000; overflow: hidden; padding-bottom: 2px; }
.internode-studio-root .inverted { border-top-color: var(--accent-1); }
.internode-studio-root #manual-bottom { border-top-color: var(--accent-2); }

.internode-studio-root .key { position: absolute; top:0; height: 100%; cursor: pointer; box-sizing: border-box; }

/* Bottom Deck (Standard) */
.internode-studio-root .keys-wrapper:not(.inverted) .key.white { background: linear-gradient(#fff 0%, #e0e0e0 100%); border: 1px solid #999; border-bottom: 6px solid #888; border-radius: 0 0 3px 3px; z-index: 1; }
.internode-studio-root .keys-wrapper:not(.inverted) .key.white.active { background: #bbb; transform: translateY(4px); border-bottom-width: 2px; }
.internode-studio-root .keys-wrapper:not(.inverted) .key.black { background: linear-gradient(#222, #000); border: 1px solid #000; border-bottom: 8px solid #000; height: 65%; z-index: 10; border-radius: 0 0 2px 2px; box-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
.internode-studio-root .keys-wrapper:not(.inverted) .key.black.active { background: #222; transform: translateY(4px); border-bottom-width: 2px; box-shadow: inset 0 0 5px #555; }

/* Top Deck (Inverted) */
.internode-studio-root .inverted .key.white { background: #252525; border: 1px solid #333; border-bottom: 6px solid #111; z-index: 1; }
.internode-studio-root .inverted .key.white.active { background: #111; transform: translateY(4px); border-color: #444; }
.internode-studio-root .inverted .key.black { background: linear-gradient(#eee, #ccc); border: 1px solid #999; border-bottom: 8px solid #888; height: 65%; z-index: 10; box-shadow: 2px 2px 4px rgba(0,0,0,0.8); }
.internode-studio-root .inverted .key.black.active { background: #fff; transform: translateY(4px); }

/* OVERLAY */
.internode-studio-root .overlay { position: absolute; inset: 0; background: #000; z-index: 99; display: flex; align-items: center; justify-content: center; }
.internode-studio-root .power-btn { background: #d81b60; color: white; border: none; padding: 12px 30px; font-weight: bold; border-radius: 3px; letter-spacing: 2px; cursor: pointer; box-shadow: 0 0 20px rgba(216,27,96,0.4); }
`;

function injectStyles() {
    if (document.getElementById("internode-studio-css")) return;
    const style = document.createElement("style");
    style.id = "internode-studio-css";
    style.textContent = STUDIO_STYLES;
    document.head.appendChild(style);
}

// --- STUDIO CLASS ---
class StudioInstance {
    constructor(container, widget) {
        this.root = container;
        this.widget = widget;
        
        // Audio
        this.ctx = null;
        this.masterGain = null;
        this.decks = {
            top: { nodes: {}, active: {}, analyser: null },
            bot: { nodes: {}, active: {}, analyser: null }
        };
        this.activeNotes = {};
        
        // System State
        this.sys = {
            top: { octave: 0, wave: '0', cutoff: 20000, res: 0, vol: 0.7 },
            bot: { octave: 0, wave: '1', cutoff: 20000, res: 0, vol: 0.7 }
        };

        if(widget && widget.value && widget.value !== "{}") {
            try {
                const saved = JSON.parse(widget.value);
                Object.assign(this.sys.top, saved.top);
                Object.assign(this.sys.bot, saved.bot);
            } catch(e) {}
        }

        this.init();
    }

    init() {
        this.renderLayout();
        this.initUI();
        
        const pwr = this.root.querySelector('.power-btn');
        pwr.onclick = async () => {
            await this.initAudio();
            this.root.querySelector('.overlay').style.display = 'none';
        };
    }

    renderLayout() {
        // EXACT HTML REPLICATION FROM ORIGINAL
        this.root.innerHTML = `
        <div class="overlay"><div style="text-align:center;"><h1 style="color:#fff; font-weight:100; letter-spacing:5px; margin-bottom:20px;">PRO STACK SYNTH</h1><button class="power-btn">INITIALIZE SYSTEM</button></div></div>
        
        <div class="synth-chassis">
            <!-- SIDEBAR -->
            <div class="sidebar-master">
                <div class="master-module">
                    <div class="mod-header">MASTER EQ</div>
                    <div class="knob-grid">
                        <div class="knob-unit"><div class="knob" data-deck="master" data-param="eqHigh"></div><label>HI</label></div>
                        <div class="knob-unit"><div class="knob" data-deck="master" data-param="eqMid"></div><label>MID</label></div>
                        <div class="knob-unit"><div class="knob" data-deck="master" data-param="eqLow"></div><label>LOW</label></div>
                    </div>
                </div>
                
                <div class="master-module">
                    <div class="mod-header">PERFORM</div>
                    <div class="wheels-container">
                        <div class="wheel-group"><div class="wheel-housing"><div class="wheel"></div></div><label>PITCH</label></div>
                        <div class="wheel-group"><div class="wheel-housing"><div class="wheel"></div></div><label>MOD</label></div>
                    </div>
                </div>

                <div class="spacer-panel"></div>
                
                <div class="master-module tall-module" style="height:auto; min-height:280px; justify-content: flex-end;">
                    <div class="mod-header">OUTPUT</div>
                    <div class="output-row">
                        <canvas class="vu-meter-canvas" id="vu-master"></canvas>
                        <div class="fader-track"><input type="range" id="master-vol" min="0" max="1" step="0.01" value="0.6"></div>
                    </div>
                </div>
            </div>
            
            <!-- RACK SPACE -->
            <div class="rack-space">
                
                <!-- TOP DECK -->
                <div class="deck-container" id="deck-top-ctrl">
                    <div class="rack-ears">UPPER</div>
                    <div class="control-face">
                        <div class="module">
                            <div class="module-label">OSC ENGINE</div>
                            <div class="grid-2x4">
                                <button class="wave-btn ${this.sys.top.wave==0?'active':''}" data-deck="top" data-val="0">SAW</button>
                                <button class="wave-btn ${this.sys.top.wave==1?'active':''}" data-deck="top" data-val="1">SQR</button>
                                <button class="wave-btn ${this.sys.top.wave==2?'active':''}" data-deck="top" data-val="2">TRI</button>
                                <button class="wave-btn ${this.sys.top.wave==3?'active':''}" data-deck="top" data-val="3">SIN</button>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="sub"></div><label>MOD</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="noise"></div><label>COL</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="detune"></div><label>VAR</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="glide"></div><label>GLD</label></div>
                            </div>
                            <button class="mini-toggle">SUBTRACTIVE</button>
                        </div>
                        <div class="module half">
                            <div class="module-label">OCTAVE</div>
                            <div class="grid-2x2">
                                <div class="lcd-panel"><div class="lcd-screen" id="disp-top">${this.sys.top.octave}</div></div>
                                <button class="oct-btn wave-btn" data-deck="top" data-action="down">▼</button>
                                <button class="oct-btn wave-btn" data-deck="top" data-action="up">▲</button>
                            </div>
                        </div>
                        <div class="module">
                            <div class="module-label">FILTER / LFO</div>
                            <div class="grid-2x4">
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="cutoff"></div><label>CUT</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="res"></div><label>RES</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="env"></div><label>ENV</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="trk"></div><label>TRK</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="rate"></div><label>RATE</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="depth"></div><label>DPTH</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="top" data-param="pwm"></div><label>PWM</label></div>
                                <button class="mini-toggle">SINE</button>
                            </div>
                        </div>
                        <div class="module wide-6">
                            <div class="module-label">TOOLS</div>
                            <div class="grid-2x6">
                                <button class="toggle-btn">ARP</button><button class="toggle-btn">HOLD</button><button class="toggle-btn">UP</button>
                                <div class="knob-unit"><div class="knob"></div><label>SPD</label></div>
                                <button class="rec-btn">●</button><button class="play-btn">►</button>
                            </div>
                        </div>
                        <div class="module wide-6">
                            <div class="module-label">FX CHAIN</div>
                            <div class="grid-2x6">
                                <select class="fx-select"><option>-- FX A --</option></select>
                                <div class="knob-unit"><div class="knob"></div><label>P1</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>P2</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>P1</label></div>
                                <select class="fx-select"><option>-- FX B --</option></select>
                                <div class="knob-unit"><div class="knob"></div><label>P2</label></div>
                            </div>
                        </div>
                        <div class="module">
                            <div class="module-label">EQ</div>
                            <div class="grid-2x2">
                                <div class="knob-unit"><div class="knob"></div><label>HI</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>MID</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>LO</label></div>
                            </div>
                        </div>
                        <div class="module">
                            <div class="module-label">ENVELOPE</div>
                            <div class="grid-2x2">
                                <div class="knob-unit"><div class="knob"></div><label>ATK</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>DEC</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>SUS</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>REL</label></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="deck-meter" id="meter-top-container">
                    <canvas id="vu-top" class="vu-meter-canvas"></canvas>
                    <div class="knob-unit meter-gain">
                        <div class="knob small accent" data-deck="top" data-param="vol"></div><label>GAIN</label>
                    </div>
                </div>
                <div class="keys-wrapper inverted" id="manual-top"></div>

                <!-- BOTTOM DECK -->
                <div class="deck-container" id="deck-bot-ctrl">
                    <div class="rack-ears bottom-ear">LOWER</div>
                    <div class="control-face">
                        <!-- Same modules as top but for bot -->
                        <div class="module"><div class="module-label">OSC ENGINE</div>
                            <div class="grid-2x4">
                                <button class="wave-btn ${this.sys.bot.wave==0?'active':''}" data-deck="bot" data-val="0">SAW</button>
                                <button class="wave-btn ${this.sys.bot.wave==1?'active':''}" data-deck="bot" data-val="1">SQR</button>
                                <button class="wave-btn ${this.sys.bot.wave==2?'active':''}" data-deck="bot" data-val="2">TRI</button>
                                <button class="wave-btn ${this.sys.bot.wave==3?'active':''}" data-deck="bot" data-val="3">SIN</button>
                                <div class="knob-unit"><div class="knob"></div><label>MOD</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>COL</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>VAR</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>GLD</label></div>
                            </div>
                            <button class="mini-toggle">SUBTRACTIVE</button>
                        </div>
                        <div class="module half"><div class="module-label">OCTAVE</div>
                            <div class="grid-2x2">
                                <div class="lcd-panel"><div class="lcd-screen accent-text" id="disp-bot">${this.sys.bot.octave}</div></div>
                                <button class="oct-btn wave-btn" data-deck="bot" data-action="down">▼</button>
                                <button class="oct-btn wave-btn" data-deck="bot" data-action="up">▲</button>
                            </div>
                        </div>
                        <div class="module"><div class="module-label">FILTER / LFO</div>
                            <div class="grid-2x4">
                                <div class="knob-unit"><div class="knob" data-deck="bot" data-param="cutoff"></div><label>CUT</label></div>
                                <div class="knob-unit"><div class="knob" data-deck="bot" data-param="res"></div><label>RES</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>ENV</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>TRK</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>RATE</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>DPTH</label></div>
                                <div class="knob-unit"><div class="knob"></div><label>PWM</label></div>
                                <button class="mini-toggle">SINE</button>
                            </div>
                        </div>
                        <div class="module wide-6"><div class="module-label">TOOLS</div><div class="grid-2x6">
                            <button class="toggle-btn">ARP</button><button class="toggle-btn">HOLD</button><button class="toggle-btn">UP</button>
                            <div class="knob-unit"><div class="knob"></div><label>SPD</label></div>
                            <button class="rec-btn">●</button><button class="play-btn">►</button>
                        </div></div>
                        <div class="module wide-6"><div class="module-label">FX CHAIN</div><div class="grid-2x6">
                            <select class="fx-select"><option>-- FX A --</option></select>
                            <div class="knob-unit"><div class="knob"></div><label>P1</label></div><div class="knob-unit"><div class="knob"></div><label>P2</label></div>
                            <div class="knob-unit"><div class="knob"></div><label>P1</label></div><select class="fx-select"><option>-- FX B --</option></select><div class="knob-unit"><div class="knob"></div><label>P2</label></div>
                        </div></div>
                        <div class="module"><div class="module-label">EQ</div><div class="grid-2x2">
                            <div class="knob-unit"><div class="knob"></div><label>HI</label></div><div class="knob-unit"><div class="knob"></div><label>MID</label></div><div class="knob-unit"><div class="knob"></div><label>LO</label></div>
                        </div></div>
                        <div class="module"><div class="module-label">ENVELOPE</div><div class="grid-2x2">
                            <div class="knob-unit"><div class="knob"></div><label>ATK</label></div><div class="knob-unit"><div class="knob"></div><label>DEC</label></div><div class="knob-unit"><div class="knob"></div><label>SUS</label></div><div class="knob-unit"><div class="knob"></div><label>REL</label></div>
                        </div></div>
                    </div>
                </div>

                <div class="deck-meter" id="meter-bot-container">
                    <canvas id="vu-bot" class="vu-meter-canvas"></canvas>
                    <div class="knob-unit meter-gain">
                        <div class="knob small accent" id="b-vol" data-deck="bot" data-param="vol"></div><label>GAIN</label>
                    </div>
                </div>
                <div class="keys-wrapper" id="manual-bottom"></div>
            </div>
        </div>
        `;
    }

    async initAudio() {
        this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        if(this.ctx.state === 'suspended') await this.ctx.resume();
        
        // Master Chain
        this.analyser = this.ctx.createAnalyser(); this.analyser.fftSize = 2048;
        this.masterGain = this.ctx.createGain(); this.masterGain.gain.value = 0.6;
        this.masterGain.connect(this.analyser);
        this.analyser.connect(this.ctx.destination);
        
        this.setupDeck('top');
        this.setupDeck('bot');
        this.startMetersLoop();
    }

    setupDeck(id) {
        const d = this.decks[id];
        d.analyser = this.ctx.createAnalyser();
        d.nodes.main = this.ctx.createGain(); d.nodes.main.gain.value = 0.7;
        d.nodes.voiceSum = this.ctx.createGain();
        
        d.nodes.filter = this.ctx.createBiquadFilter();
        d.nodes.filter.type = 'lowpass'; d.nodes.filter.frequency.value = 20000;
        
        // Correct Chain: VoiceSum -> Filter -> Main -> Analyser -> Master
        d.nodes.voiceSum.connect(d.nodes.filter);
        d.nodes.filter.connect(d.nodes.main);
        d.nodes.main.connect(d.analyser);
        d.nodes.main.connect(this.masterGain);
    }

    playNote(midi, deck) {
        if(!this.ctx) return;
        const id = `${deck}-${midi}`;
        if(this.activeNotes[id]) this.stopNote(midi, deck);
        
        const freq = 440 * Math.pow(2, (midi - 69) / 12);
        const osc = this.ctx.createOscillator();
        const types = ['sawtooth', 'square', 'triangle', 'sine'];
        osc.type = types[parseInt(this.sys[deck].wave)];
        osc.frequency.value = freq;
        
        const env = this.ctx.createGain();
        env.gain.setValueAtTime(0, this.ctx.currentTime);
        env.gain.linearRampToValueAtTime(1, this.ctx.currentTime + 0.05);
        env.gain.setTargetAtTime(0.5, this.ctx.currentTime + 0.05, 0.2); // Decay to Sustain
        
        osc.connect(env);
        env.connect(this.decks[deck].nodes.voiceSum); // Connect to deck input
        
        osc.start();
        this.activeNotes[id] = { osc, env };
        this.saveState();
    }

    stopNote(midi, deck) {
        const id = `${deck}-${midi}`;
        if(!this.activeNotes[id]) return;
        
        const { osc, env } = this.activeNotes[id];
        const t = this.ctx.currentTime;
        env.gain.cancelScheduledValues(t);
        env.gain.setValueAtTime(env.gain.value, t);
        env.gain.linearRampToValueAtTime(0, t + 0.15); // Release
        osc.stop(t + 0.16);
        delete this.activeNotes[id];
    }

    initUI() {
        this.renderKeys('manual-top', 'top', 48);
        this.renderKeys('manual-bottom', 'bot', 36);
        
        // Knobs Logic
        this.root.querySelectorAll('.knob').forEach(k => {
            let val = 0.5;
            if(k.dataset.param === 'cutoff') val = 1.0;
            k.style.transform = `rotate(${(val*270)-135}deg)`;
            k.onmousedown = (e) => {
                const sy = e.clientY;
                const startDeg = parseFloat(k.style.transform.replace(/[^\d.-]/g,''))||-135;
                const move = (ev) => {
                    let d = startDeg + (sy - ev.clientY)*2.5;
                    d = Math.max(-135, Math.min(135, d));
                    k.style.transform = `rotate(${d}deg)`;
                    
                    const deck = k.dataset.deck || k.dataset.type;
                    const param = k.dataset.param;
                    const norm = (d+135)/270;
                    
                    if(deck === 'master' && param === 'vol') this.masterGain.gain.value = norm;
                    if((deck=='top'||deck=='bot')) {
                        if(param=='cutoff') {
                            this.sys[deck].cutoff = 20 + (norm*20000);
                            if(this.decks[deck].nodes.filter) 
                                this.decks[deck].nodes.filter.frequency.setTargetAtTime(this.sys[deck].cutoff, this.ctx.currentTime, 0.1);
                        }
                    }
                    this.saveState();
                };
                const up = () => { window.removeEventListener('mousemove',move); window.removeEventListener('mouseup',up); };
                window.addEventListener('mousemove',move); window.addEventListener('mouseup',up);
            }
        });

        // Wave Buttons
        this.root.querySelectorAll('.wave-btn[data-val]').forEach(b => {
            b.onclick = () => {
                const d = b.dataset.deck;
                this.root.querySelectorAll(`.wave-btn[data-deck="${d}"][data-val]`).forEach(x=>x.classList.remove('active'));
                b.classList.add('active');
                this.sys[d].wave = b.dataset.val;
                this.saveState();
            };
        });
        
        // Octave Buttons
        this.root.querySelectorAll('.wave-btn[data-action]').forEach(b => {
            b.onclick = () => {
                const d = b.dataset.deck;
                if(b.dataset.action === 'up' && this.sys[d].octave < 2) this.sys[d].octave++;
                if(b.dataset.action === 'down' && this.sys[d].octave > -2) this.sys[d].octave--;
                this.root.querySelector(`#disp-${d}`).textContent = this.sys[d].octave;
                this.renderKeys(d==='top'?'manual-top':'manual-bottom', d, d==='top'?48:36); // Re-render to update MIDI mapping
                this.saveState();
            }
        });
    }

    renderKeys(id, deck, startMidi) {
        const cont = this.root.querySelector(`#${id}`);
        if(!cont) return;
        cont.innerHTML = ''; 
        const numKeys = 49; 
        const wWidth = 100 / 29; 
        let wIdx = 0;
        
        // Octave Shift Logic
        const shift = this.sys[deck].octave * 12;
        
        for(let i=0; i<numKeys; i++){
            const m = startMidi + i; 
            const n = m % 12;
            const isBlk = [1,3,6,8,10].includes(n);
            const k = document.createElement('div');
            
            k.onmousedown = (e) => { e.preventDefault(); k.classList.add('active'); this.playNote(m + shift, deck); };
            k.onmouseup = k.onmouseleave = (e) => { e.preventDefault(); k.classList.remove('active'); this.stopNote(m + shift, deck); };
            
            if(isBlk) {
                k.className = 'key black';
                k.style.width = (wWidth * 0.65) + '%';
                k.style.left = ((wIdx * wWidth) - (wWidth * 0.325)) + '%'; 
            } else {
                k.className = 'key white'; 
                k.style.width = wWidth + '%'; 
                k.style.left = (wIdx * wWidth) + '%';
                wIdx++;
            }
            cont.appendChild(k);
        }
    }

    startMetersLoop() {
        const draw = (cid, an) => {
            const cvs = this.root.querySelector(`#${cid}`);
            if(!cvs || !an) return;
            const ctx = cvs.getContext('2d');
            const w = cvs.width, h = cvs.height;
            ctx.clearRect(0,0,w,h);
            ctx.fillStyle = '#111'; ctx.fillRect(0,0,w,h);
            
            const data = new Uint8Array(2048);
            an.getByteTimeDomainData(data);
            let sum=0; for(let i=0;i<data.length;i++){ const v=(data[i]-128)/128; sum+=v*v; }
            const rms = Math.sqrt(sum/data.length);
            
            // Segmented Meter
            const segs = 20; const gap = 2; const sH = (h - (segs*gap))/segs;
            const lit = Math.floor(rms * 50); // Sensitivity
            
            for(let i=0; i<segs; i++) {
                const idx = segs - 1 - i; 
                const isLit = lit > idx;
                let col = '#0f0';
                if(i < 4) col = '#f00'; 
                else if(i < 9) col = '#ff0';
                
                ctx.fillStyle = isLit ? col : '#222';
                ctx.fillRect(2, i*(sH+gap), w-4, sH);
            }
        };
        
        const loop = () => {
            draw('vu-master', this.analyser);
            draw('vu-top', this.decks.top.analyser);
            draw('vu-bot', this.decks.bot.analyser);
            requestAnimationFrame(loop);
        };
        loop();
    }

    saveState() {
        if(this.widget) this.widget.value = JSON.stringify(this.sys);
    }
}

// --- REGISTRATION ---
app.registerExtension({
    name: "Internode.StudioSurface",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeStudioSurface") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                injectStyles();
                
                const widget = this.widgets.find(w => w.name === "ui_state");
                if (widget) { widget.type = "custom"; widget.computeSize = () => [0, -4]; }

                const container = document.createElement("div");
                container.className = "internode-studio-root";
                
                new StudioInstance(container, widget);
                
                this.addDOMWidget("studio_ui", "div", container, { serialize: false });
                this.setSize([900, 600]); 
                return r;
            };
        }
    }
});