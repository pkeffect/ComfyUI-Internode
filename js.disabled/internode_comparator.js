// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_comparator.js
// VERSION: 3.1.0

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("%c#### Internode: A/B Comparator Loaded", "color: cyan; font-weight: bold;");

app.registerExtension({
    name: "Internode.ABComparator",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeImageComparer") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // --- WIDGET HIDING (Nodes 2.0) ---
                // No input widgets to hide for this node really, but standard practice:
                // if (!this._internodeOriginalWidgets) {
                //    this._internodeOriginalWidgets = this.widgets ? [...this.widgets] : [];
                // }

                const root = document.createElement("div");
                Object.assign(root.style, {
                    width: "100%", height: "100%", minHeight: "300px",
                    backgroundColor: "#000", position: "relative",
                    display: "flex", flexDirection: "column",
                    overflow: "hidden", borderRadius: "4px"
                });

                // Viewer Container
                const container = document.createElement("div");
                Object.assign(container.style, {
                    flex: "1", position: "relative", overflow: "hidden",
                    backgroundImage: "linear-gradient(45deg, #111 25%, transparent 25%), linear-gradient(-45deg, #111 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #111 75%), linear-gradient(-45deg, transparent 75%, #111 75%)",
                    backgroundSize: "20px 20px", backgroundColor: "#1a1a1a"
                });

                // Shared styles for media
                const mediaStyle = {
                    position: "absolute", top: "0", left: "0",
                    width: "100%", height: "100%",
                    objectFit: "contain", display: "none"
                };

                const imgA = document.createElement("img"); Object.assign(imgA.style, mediaStyle);
                const imgB = document.createElement("img"); Object.assign(imgB.style, mediaStyle);

                // Labels
                const lblA = document.createElement("div"); lblA.textContent = "A";
                Object.assign(lblA.style, { position: "absolute", bottom: "5px", left: "5px", color: "rgba(255,255,255,0.5)", fontWeight: "bold", textShadow: "0 1px 2px black", pointerEvents: "none", zIndex: 5 });

                const lblB = document.createElement("div"); lblB.textContent = "B";
                Object.assign(lblB.style, { position: "absolute", bottom: "5px", right: "5px", color: "rgba(255,255,255,0.5)", fontWeight: "bold", textShadow: "0 1px 2px black", pointerEvents: "none", zIndex: 5 });

                // Slider
                const slider = document.createElement("div");
                Object.assign(slider.style, {
                    position: "absolute", top: "0", bottom: "0", left: "50%",
                    width: "2px", backgroundColor: "white", cursor: "ew-resize", zIndex: 10,
                    boxShadow: "0 0 4px rgba(0,0,0,0.8)"
                });

                const handle = document.createElement("div");
                Object.assign(handle.style, {
                    position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)",
                    width: "20px", height: "20px", borderRadius: "50%", backgroundColor: "white",
                    display: "flex", alignItems: "center", justifyContent: "center", color: "black", fontSize: "12px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.5)"
                });
                handle.innerHTML = "⇄";
                slider.appendChild(handle);

                // Hierarchy: Container -> ImgA -> ImgB -> Labels -> Slider
                container.appendChild(imgA);
                container.appendChild(imgB);
                container.appendChild(lblA);
                container.appendChild(lblB);
                container.appendChild(slider);
                root.appendChild(container);

                // Logic
                let pct = 50;

                const updateView = () => {
                    slider.style.left = `${pct}%`;
                    imgB.style.clipPath = `polygon(${pct}% 0, 100% 0, 100% 100%, ${pct}% 100%)`;
                };

                const setPos = (clientX) => {
                    const rect = container.getBoundingClientRect();
                    pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
                    updateView();
                };

                let dragging = false;
                container.addEventListener("mousedown", (e) => { dragging = true; setPos(e.clientX); });
                window.addEventListener("mousemove", (e) => { if (dragging) setPos(e.clientX); });
                window.addEventListener("mouseup", () => { dragging = false; });

                // Hover mode fallback if not dragging? optional, keeping drag for precision

                this.onExecuted = function (message) {
                    if (!message || !message.ui) return;
                    // Support both new dictionary format and fallback (though new python node returns dict)
                    const imgsA = message.ui.a_images || [];
                    const imgsB = message.ui.b_images || [];

                    if (imgsA.length > 0) {
                        const i = imgsA[0];
                        imgA.src = api.apiURL(`/view?filename=${encodeURIComponent(i.filename)}&type=${i.type}&subfolder=${encodeURIComponent(i.subfolder || "")}`);
                        imgA.style.display = "block";
                    }
                    if (imgsB.length > 0) {
                        const i = imgsB[0];
                        imgB.src = api.apiURL(`/view?filename=${encodeURIComponent(i.filename)}&type=${i.type}&subfolder=${encodeURIComponent(i.subfolder || "")}`);
                        imgB.style.display = "block";
                    }
                };

                this.addDOMWidget("compare_view", "div", root, { serialize: false });
                this.setSize([512, 512]);
                requestAnimationFrame(updateView);
                return r;
            };
        }
    }
});