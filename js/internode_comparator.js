// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_comparator.js
// VERSION: 3.1.0

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("%c#### Internode: A/B Comparator Loaded", "color: cyan; font-weight: bold;");

app.registerExtension({
    name: "Internode.ABComparator",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeABComparator") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // 1. Main Container
                const root = document.createElement("div");
                Object.assign(root.style, {
                    width: "100%", height: "100%",
                    backgroundColor: "#000",
                    display: "flex", flexDirection: "column",
                    overflow: "hidden", borderRadius: "4px",
                    position: "relative",
                    userSelect: "none"
                });

                // 2. Viewer Area (Holds A and B)
                const viewArea = document.createElement("div");
                Object.assign(viewArea.style, {
                    flex: "1", position: "relative",
                    backgroundImage: "linear-gradient(45deg, #111 25%, transparent 25%), linear-gradient(-45deg, #111 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #111 75%), linear-gradient(-45deg, transparent 75%, #111 75%)",
                    backgroundSize: "20px 20px",
                    backgroundColor: "#1a1a1a",
                    overflow: "hidden"
                });

                // Media Elements
                const createMedia = (isVid) => {
                    const el = isVid ? document.createElement("video") : document.createElement("img");
                    Object.assign(el.style, {
                        position: "absolute", top: "0", left: "0",
                        width: "100%", height: "100%",
                        objectFit: "contain",
                        display: "none"
                    });
                    if(isVid) { el.loop = true; el.muted = true; }
                    return el;
                };

                const mediaA = createMedia(false); // Type determined at runtime, placeholders
                const mediaB = createMedia(false); 
                
                // Labels
                const labelA = document.createElement("div");
                labelA.textContent = "A";
                Object.assign(labelA.style, { position: "absolute", bottom: "10px", left: "10px", color: "rgba(255,255,255,0.5)", fontWeight: "bold", pointerEvents: "none", zIndex: "10" });
                
                const labelB = document.createElement("div");
                labelB.textContent = "B";
                Object.assign(labelB.style, { position: "absolute", bottom: "10px", right: "10px", color: "rgba(255,255,255,0.5)", fontWeight: "bold", pointerEvents: "none", zIndex: "10" });

                // 3. Slider Handle
                const slider = document.createElement("div");
                Object.assign(slider.style, {
                    position: "absolute", top: "0", bottom: "0", left: "50%",
                    width: "4px", marginLeft: "-2px",
                    backgroundColor: "rgba(255,255,255,0.8)",
                    cursor: "ew-resize", zIndex: "20",
                    boxShadow: "0 0 5px rgba(0,0,0,0.5)"
                });
                
                const thumb = document.createElement("div");
                Object.assign(thumb.style, {
                    position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)",
                    width: "24px", height: "24px", borderRadius: "50%",
                    backgroundColor: "#fff",
                    boxShadow: "0 2px 5px rgba(0,0,0,0.5)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: "#000", fontSize: "10px", fontWeight: "bold"
                });
                thumb.innerHTML = "&#8596;"; // Arrow
                slider.appendChild(thumb);

                // Hierarchy
                // viewArea -> mediaA (Bottom) -> mediaB (Top, Clipped) -> slider
                viewArea.appendChild(mediaA);
                viewArea.appendChild(mediaB);
                viewArea.appendChild(labelA);
                viewArea.appendChild(labelB);
                viewArea.appendChild(slider);
                root.appendChild(viewArea);

                // 4. Interaction Logic
                let isDragging = false;
                let sliderPos = 50; // Percentage

                const updateClip = () => {
                    slider.style.left = `${sliderPos}%`;
                    // Clip Media B (The "After" image usually on right, or overlay)
                    // Let's make Media B the RIGHT side image, Media A the LEFT side image?
                    // Standard A/B: 
                    // Media A is full width (background).
                    // Media B is full width (foreground).
                    // We clip Media B to show only the right side? 
                    // Or Clip Media B to show only Left side? 
                    
                    // Implementation: B is ON TOP. We clip B so it only shows from Slider -> Right.
                    // clip-path: inset(top right bottom left)
                    // If slider is at 50%, we clip the left 50% of B.
                    mediaB.style.clipPath = `inset(0 0 0 ${sliderPos}%)`;
                };

                viewArea.addEventListener("mousedown", (e) => { isDragging = true; });
                window.addEventListener("mouseup", () => { isDragging = false; });
                
                viewArea.addEventListener("mousemove", (e) => {
                    if (!isDragging) return;
                    const rect = viewArea.getBoundingClientRect();
                    let x = e.clientX - rect.left;
                    let pct = (x / rect.width) * 100;
                    sliderPos = Math.max(0, Math.min(100, pct));
                    updateClip();
                });

                // 5. Load Logic
                this.onExecuted = function (message) {
                    if (!message || !message.files || message.files.length < 2) return;
                    
                    const urlA = api.apiURL(`/view?filename=${message.files[0]}&type=temp`);
                    const urlB = api.apiURL(`/view?filename=${message.files[1]}&type=temp`);
                    
                    const isVideo = message.types[0] === "video";
                    
                    // Helper to replace element if type changed
                    const replaceEl = (oldEl, newTag) => {
                        const newEl = document.createElement(newTag);
                        newEl.style.cssText = oldEl.style.cssText;
                        if (newTag === "video") { newEl.loop = true; newEl.muted = true; }
                        oldEl.replaceWith(newEl);
                        return newEl;
                    };

                    const tag = isVideo ? "video" : "img";
                    
                    // Update Elements references
                    const finalA = replaceEl(mediaA, tag);
                    const finalB = replaceEl(mediaB, tag);
                    
                    // Update internal references for click handlers
                    // (We cheat and just grab children index 0 and 1 next time or update vars if scoping allowed)
                    // Ideally we update the vars in scope, but due to closure we need to be careful.
                    // Let's re-append to viewArea to be safe
                    viewArea.innerHTML = ""; 
                    viewArea.appendChild(finalA);
                    viewArea.appendChild(finalB); // B is on top
                    viewArea.appendChild(labelA);
                    viewArea.appendChild(labelB);
                    viewArea.appendChild(slider);

                    finalA.src = urlA;
                    finalB.src = urlB;
                    
                    finalA.style.display = "block";
                    finalB.style.display = "block";
                    
                    // Video Sync Logic
                    if (isVideo) {
                        const sync = (e) => {
                            if (e.target === finalA) finalB.currentTime = finalA.currentTime;
                            // if (e.target === finalB) finalA.currentTime = finalB.currentTime; // Avoid loops
                        };
                        
                        finalA.onplay = () => finalB.play();
                        finalA.onpause = () => finalB.pause();
                        finalA.ontimeupdate = sync;
                        
                        // Click to play/pause
                        viewArea.onclick = () => {
                            if (finalA.paused) finalA.play(); else finalA.pause();
                        };
                    } else {
                        viewArea.onclick = null;
                    }
                    
                    updateClip();
                };

                this.addDOMWidget("comparator_ui", "div", root, { serialize: false });
                this.setSize([500, 400]);
                return r;
            };
        }
    }
});