// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_player.js
// VERSION: 3.0.9

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("%c#### Internode: Universal Player Loaded", "color: cyan; font-weight: bold;");

app.registerExtension({
    name: "Internode.UniversalPlayer",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeUniversalPlayer") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // 1. Container
                const container = document.createElement("div");
                Object.assign(container.style, {
                    width: "100%", height: "100%",
                    backgroundColor: "#000",
                    display: "flex", flexDirection: "column",
                    overflow: "hidden", borderRadius: "4px",
                    position: "relative"
                });

                // 2. Media Area
                const mediaContainer = document.createElement("div");
                Object.assign(mediaContainer.style, {
                    flex: "1", width: "100%", display: "flex", 
                    alignItems: "center", justifyContent: "center",
                    backgroundImage: "linear-gradient(45deg, #111 25%, transparent 25%), linear-gradient(-45deg, #111 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #111 75%), linear-gradient(-45deg, transparent 75%, #111 75%)",
                    backgroundSize: "20px 20px",
                    backgroundPosition: "0 0, 0 10px, 10px -10px, -10px 0px",
                    backgroundColor: "#1a1a1a"
                });
                
                const vidEl = document.createElement("video");
                vidEl.controls = true;
                vidEl.loop = true;
                Object.assign(vidEl.style, {
                    maxWidth: "100%", maxHeight: "100%", display: "none"
                });
                
                const audEl = document.createElement("audio");
                audEl.controls = true;
                audEl.loop = true;
                Object.assign(audEl.style, {
                    width: "90%", display: "none"
                });

                mediaContainer.appendChild(vidEl);
                mediaContainer.appendChild(audEl);
                container.appendChild(mediaContainer);

                // 3. Status Overlay
                const status = document.createElement("div");
                status.textContent = "Waiting for media...";
                Object.assign(status.style, {
                    position: "absolute", top: "50%", left: "50%", 
                    transform: "translate(-50%, -50%)",
                    color: "#666", fontSize: "12px", fontFamily: "sans-serif",
                    pointerEvents: "none"
                });
                container.appendChild(status);

                this.addDOMWidget("player_ui", "div", container, { serialize: false });

                // 4. Handle Execution Result
                this.onExecuted = function (message) {
                    if (!message || !message.file || message.file.length === 0) return;
                    
                    const filename = message.file[0];
                    const type = message.type[0]; // "video" or "audio" or "none"
                    const folder = message.folder[0]; // "_temp"
                    
                    // Construct URL
                    // api.apiURL handles adding /api/view...
                    // Standard Comfy view: /view?filename=x&type=temp
                    const params = new URLSearchParams({
                        filename: filename,
                        type: folder === "_temp" ? "temp" : "output"
                    });
                    const url = api.apiURL("/view?" + params.toString());

                    if (type === "video") {
                        vidEl.src = url;
                        vidEl.style.display = "block";
                        audEl.style.display = "none";
                        audEl.pause();
                        status.style.display = "none";
                        vidEl.play().catch(e => console.log("Auto-play blocked", e));
                    } else if (type === "audio") {
                        audEl.src = url;
                        audEl.style.display = "block";
                        vidEl.style.display = "none";
                        vidEl.pause();
                        status.style.display = "none";
                        audEl.play().catch(e => console.log("Auto-play blocked", e));
                    } else {
                        status.style.display = "block";
                        status.textContent = "No Media Output";
                    }
                };

                this.setSize([400, 300]);
                return r;
            };
        }
    }
});