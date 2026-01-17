// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_sticky.js
// VERSION: 3.0.8

import { app } from "../../scripts/app.js";

console.log("%c#### Internode: Sticky Note UI Loaded", "color: yellow; background: #333; font-weight: bold;");

// --- UTILS ---
function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function parseMarkdown(text, color) {
    if (!text) return "";
    const lines = text.split('\n');
    let html = '';
    
    // Adjust header border color based on text color intensity
    const borderColor = (color === '#ffffff' || color === '#eeeeee') ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.2)';

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        
        // Headers
        if (line.startsWith('#')) {
            const level = line.match(/^#+/)[0].length;
            const content = line.slice(level).trim();
            html += `<div style="font-weight:800; font-size:${1.4 - (level*0.1)}em; margin-bottom:4px; opacity: 0.9; border-bottom:1px dashed ${borderColor};">${escapeHtml(content)}</div>`;
            continue;
        }
        
        // Lists
        if (line.match(/^\s*[-*]\s+(.*)/)) {
            const content = line.replace(/^\s*[-*]\s+/, '').trim();
            html += `<div style="display:flex; margin-left:5px;">
                        <span style="margin-right:5px; opacity:0.6;">•</span>
                        <span>${processInline(content)}</span>
                     </div>`;
            continue;
        }

        // Standard Line
        if (line.trim().length > 0) {
            html += `<div style="margin-bottom:4px;">${processInline(line)}</div>`;
        } else {
            html += '<div style="height:10px;"></div>';
        }
    }
    return html;
}

function processInline(text) {
    text = escapeHtml(text);
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>'); 
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    text = text.replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,0.1); padding:0 4px; border-radius:3px; font-family:monospace; font-size:0.9em;">$1</code>');
    return text;
}

const COLOR_MAP = {
    // Backgrounds
    "Yellow": ["#fff740", "#ffff88"],
    "Green":  ["#b3ff66", "#d9ffb3"],
    "Pink":   ["#ff99cc", "#ffcce5"],
    "Orange": ["#ffcc66", "#ffe6b3"],
    "Blue":   ["#66ccff", "#b3e6ff"],
    "White":  ["#f0f0f0", "#ffffff"],
    
    // Text Colors
    "Black": "#222222",
    "Gray":  "#555555",
    "White": "#ffffff",
    "Red":   "#cc0000",
    "Blue":  "#0033cc"
};

app.registerExtension({
    name: "Internode.StickyNote",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeStickyNote") {
            
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                if (onConfigure) onConfigure.apply(this, arguments);
<<<<<<< HEAD
                const textWidget = this._stickyGetWidget ? this._stickyGetWidget("text") : this.widgets?.find(w => w.name === "text");
                const colorWidget = this._stickyGetWidget ? this._stickyGetWidget("note_color") : this.widgets?.find(w => w.name === "note_color");
                const fontWidget = this._stickyGetWidget ? this._stickyGetWidget("text_color") : this.widgets?.find(w => w.name === "text_color");
=======
                const textWidget = this.widgets?.find(w => w.name === "text");
                const colorWidget = this.widgets?.find(w => w.name === "note_color");
                const fontWidget = this.widgets?.find(w => w.name === "text_color");
>>>>>>> 402770905de74eb3ee18465e48f6c336d49e71ff

                if (this.sticky_ui) {
                    if (textWidget) this.sticky_ui.textarea.value = textWidget.value;
                    // Trigger visual update
                    this.sticky_ui.applyTheme(
                        colorWidget ? colorWidget.value : "Yellow",
                        fontWidget ? fontWidget.value : "Black"
                    );
                    if (this.sticky_ui.updateState) this.sticky_ui.updateState();
                }
            };

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

<<<<<<< HEAD
                // Store original widgets for Nodes 2.0 compatibility
                if (!this._stickyOriginalWidgets) {
                    this._stickyOriginalWidgets = this.widgets ? [...this.widgets] : [];
                }
                
                const hideWidgets = () => {
                    if (!this.widgets) return;
                    const widgetsToKeep = [];
                    const widgetsToHide = [];
                    
                    this.widgets.forEach(w => {
                        if (w.name === "sticky_ui") {
                            widgetsToKeep.push(w);
                        } else {
                            widgetsToHide.push(w);
                            w.computeSize = () => [0, -4];
                            if (w.element) w.element.style.display = "none";
                        }
                    });
                    
                    this.widgets = widgetsToKeep;
                    this._stickyHiddenWidgets = widgetsToHide;
                };
                
                if (!this._stickyGetWidget) {
                    this._stickyGetWidget = (name) => {
                        const visible = this.widgets ? this.widgets.find(w => w.name === name) : null;
                        if (visible) return visible;
                        const hidden = this._stickyHiddenWidgets ? this._stickyHiddenWidgets.find(w => w.name === name) : null;
                        if (hidden) return hidden;
                        return this._stickyOriginalWidgets ? this._stickyOriginalWidgets.find(w => w.name === name) : null;
                    };
                }

                const textWidget = this._stickyOriginalWidgets.find(w => w.name === "text");
                const noteColorWidget = this._stickyOriginalWidgets.find(w => w.name === "note_color");
                const textColorWidget = this._stickyOriginalWidgets.find(w => w.name === "text_color");
=======
                // Helper to hide but keep widgets
                const hideWidget = (name) => {
                    const w = this.widgets.find(wid => wid.name === name);
                    if (w) {
                        w.computeSize = () => [0, 0];
                        w.draw = function() { return; };
                    }
                    return w;
                };

                const textWidget = hideWidget("text");
                const noteColorWidget = hideWidget("note_color");
                const textColorWidget = hideWidget("text_color");
>>>>>>> 402770905de74eb3ee18465e48f6c336d49e71ff

                // 1. Root Container
                const root = document.createElement("div");
                Object.assign(root.style, {
                    width: "100%", height: "100%",
                    display: "flex", flexDirection: "column",
                    borderRadius: "2px",
                    boxShadow: "2px 4px 8px rgba(0,0,0,0.3)",
                    fontFamily: '"Comic Sans MS", "Marker Felt", sans-serif',
                    fontSize: "14px",
                    boxSizing: "border-box",
                    overflow: "hidden",
                    transition: "background 0.3s, color 0.3s"
                });

                // 2. Toolbar
                const toolbar = document.createElement("div");
                Object.assign(toolbar.style, {
                    height: "20px", width: "100%",
                    backgroundColor: "rgba(0,0,0,0.05)",
                    display: "flex", justifyContent: "flex-end",
                    padding: "0 5px", boxSizing: "border-box", cursor: "move"
                });
                
                const toggleBtn = document.createElement("div");
                toggleBtn.textContent = "✎";
                Object.assign(toggleBtn.style, {
                    cursor: "pointer", fontSize: "12px", fontWeight: "bold",
                    opacity: "0.6", padding: "0 5px", userSelect: "none"
                });
                toolbar.appendChild(toggleBtn);

                // 3. Content
                const contentArea = document.createElement("div");
                Object.assign(contentArea.style, { width: "100%", flex: "1", position: "relative", overflow: "hidden" });

                const textarea = document.createElement("textarea");
                Object.assign(textarea.style, {
                    width: "100%", height: "100%",
                    backgroundColor: "rgba(255,255,255,0.15)",
                    border: "none", outline: "none", resize: "none",
                    padding: "10px", color: "inherit",
                    fontFamily: "monospace", fontSize: "12px",
                    boxSizing: "border-box"
                });
                if(textWidget) textarea.value = textWidget.value;

                const preview = document.createElement("div");
                Object.assign(preview.style, {
                    width: "100%", height: "100%",
                    padding: "10px", overflowY: "auto",
                    boxSizing: "border-box", wordWrap: "break-word"
                });

                // 4. Logic & Theming
                let currentTextColor = "#222";

                const applyTheme = (bgColorName, textColorName) => {
                    const bg = COLOR_MAP[bgColorName] || COLOR_MAP["Yellow"];
                    const txt = COLOR_MAP[textColorName] || "#222";
                    
                    root.style.backgroundColor = bg[0];
                    root.style.backgroundImage = `linear-gradient(to bottom right, ${bg[1]}, ${bg[0]})`;
                    root.style.color = txt;
                    currentTextColor = txt;
                    
                    // Re-render markdown to update border colors
                    if (preview.style.display !== "none") {
                        preview.innerHTML = parseMarkdown(textarea.value, currentTextColor);
                    }
                };

                // Initial Theme Apply
                applyTheme(
                    noteColorWidget ? noteColorWidget.value : "Yellow",
                    textColorWidget ? textColorWidget.value : "Black"
                );

                let isPreview = true;
                const updateState = () => {
                    if (isPreview) {
                        preview.innerHTML = parseMarkdown(textarea.value, currentTextColor);
                        textarea.style.display = "none";
                        preview.style.display = "block";
                        toggleBtn.textContent = "✎";
                    } else {
                        textarea.style.display = "block";
                        preview.style.display = "none";
                        toggleBtn.textContent = "✔";
                    }
                };
                updateState();

                // 5. Events
                toggleBtn.addEventListener("mousedown", (e) => e.stopPropagation());
                toggleBtn.onclick = () => { isPreview = !isPreview; updateState(); };

                textarea.addEventListener("input", () => {
                    if(textWidget) textWidget.value = textarea.value;
                });

                // Listen for property changes in ComfyUI Panel
                if (noteColorWidget) {
                    noteColorWidget.callback = (v) => {
                        applyTheme(v, textColorWidget.value);
                    };
                }
                if (textColorWidget) {
                    textColorWidget.callback = (v) => {
                        applyTheme(noteColorWidget.value, v);
                    };
                }

                const stop = (e) => e.stopPropagation();
                textarea.addEventListener("mousedown", stop);
                textarea.addEventListener("wheel", stop, {passive: true});
                preview.addEventListener("mousedown", stop);
                preview.addEventListener("wheel", stop, {passive: true});

                contentArea.appendChild(textarea);
                contentArea.appendChild(preview);
                root.appendChild(toolbar);
                root.appendChild(contentArea);

<<<<<<< HEAD
                const domWidget = this.addDOMWidget("sticky_ui", "div", root, { serialize: false });
                domWidget.computedHeight = 220;
                
                hideWidgets();
                this.stickyHideWidgets = hideWidgets;
=======
                this.addDOMWidget("sticky_ui", "div", root, { serialize: false });
>>>>>>> 402770905de74eb3ee18465e48f6c336d49e71ff
                
                // Expose methods for onConfigure
                this.sticky_ui = {
                    textarea: textarea,
                    applyTheme: applyTheme,
                    updateState: updateState
                };

                this.setSize([220, 220]);
<<<<<<< HEAD
                this.resizable = true;
                
                // Override computeSize
                this.computeSize = function(out) {
                    let height = LiteGraph.NODE_TITLE_HEIGHT || 30;
                    if (this.widgets) {
                        for (let w of this.widgets) {
                            if (w.name === "sticky_ui" && w.computedHeight) {
                                height += w.computedHeight;
                            }
                        }
                    }
                    const width = this.size && this.size[0] > 220 ? this.size[0] : 220;
                    const finalHeight = this.size && this.size[1] ? this.size[1] : height;
                    if (out) {
                        out[0] = width;
                        out[1] = finalHeight;
                        return out;
                    }
                    return [width, finalHeight];
                };
                
                // Handle reconfiguration
                const originalConfigure = this.configure;
                this.configure = function(info) {
                    originalConfigure?.apply(this, arguments);
                    if (this.stickyHideWidgets) {
                        requestAnimationFrame(() => this.stickyHideWidgets());
                    }
                };
                
=======
>>>>>>> 402770905de74eb3ee18465e48f6c336d49e71ff
                return r;
            };
        }
    }
});