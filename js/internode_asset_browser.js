// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_asset_browser.js
// VERSION: 3.1.0

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("%c#### Internode: Asset Browser Loaded", "color: cyan; font-weight: bold;");

app.registerExtension({
    name: "Internode.AssetBrowser",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeAssetBrowser") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // 1. Hijack the Filename Widget
                const fileWidget = this.widgets.find(w => w.name === "filename");
                if (!fileWidget) return r;

                // Get list of files from the widget options (Comfy populates this)
                // Note: ComfyUI populates 'options.values' for COMBO widgets
                let fileList = fileWidget.options.values || [];
                
                // Hide default widget
                fileWidget.type = "custom";
                fileWidget.computeSize = () => [0, -4];
                fileWidget.draw = () => {};

                // 2. Setup UI Container
                const container = document.createElement("div");
                Object.assign(container.style, {
                    width: "100%", height: "100%",
                    display: "flex", flexDirection: "column",
                    backgroundColor: "#111", borderRadius: "4px",
                    overflow: "hidden"
                });

                // 3. Search Bar
                const searchBar = document.createElement("input");
                searchBar.placeholder = "🔍 Filter assets...";
                Object.assign(searchBar.style, {
                    width: "100%", padding: "5px",
                    backgroundColor: "#222", border: "none",
                    borderBottom: "1px solid #333",
                    color: "#fff", outline: "none",
                    fontSize: "12px", flexShrink: "0"
                });

                // 4. Grid Area
                const grid = document.createElement("div");
                Object.assign(grid.style, {
                    flex: "1", overflowY: "auto",
                    display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
                    gap: "2px", padding: "2px",
                    alignContent: "start"
                });

                // 5. Render Function
                const renderGrid = (filterText = "") => {
                    grid.innerHTML = "";
                    const lowerFilter = filterText.toLowerCase();
                    
                    // Filter files
                    const matches = fileList.filter(f => f.toLowerCase().includes(lowerFilter));
                    
                    // Limit rendering for performance if list is huge (e.g., show first 100 matches)
                    const displayList = matches.slice(0, 100);

                    displayList.forEach(filename => {
                        const item = document.createElement("div");
                        Object.assign(item.style, {
                            aspectRatio: "1/1", cursor: "pointer",
                            backgroundColor: "#000", position: "relative",
                            border: filename === fileWidget.value ? "2px solid #0f0" : "1px solid #333"
                        });
                        
                        // Construct Thumbnail URL
                        // Use ComfyUI view API. For images it works. For video it might just show icon or first frame depending on server.
                        const url = api.apiURL(`/view?filename=${encodeURIComponent(filename)}&type=input`);
                        
                        // Check extension for icon vs image
                        const ext = filename.split('.').pop().toLowerCase();
                        const isVid = ['mp4', 'mov', 'avi', 'webm'].includes(ext);
                        
                        const img = document.createElement("img");
                        img.src = url;
                        Object.assign(img.style, {
                            width: "100%", height: "100%", objectFit: "cover",
                            opacity: "0.8", transition: "opacity 0.2s"
                        });
                        
                        // Hover effect
                        item.onmouseenter = () => img.style.opacity = "1.0";
                        item.onmouseleave = () => img.style.opacity = "0.8";
                        
                        // Selection
                        item.onclick = () => {
                            fileWidget.value = filename;
                            // Update visual selection
                            Array.from(grid.children).forEach(c => c.style.border = "1px solid #333");
                            item.style.border = "2px solid #0f0";
                        };

                        // Label
                        const lbl = document.createElement("div");
                        lbl.textContent = filename;
                        Object.assign(lbl.style, {
                            position: "absolute", bottom: "0", left: "0", right: "0",
                            backgroundColor: "rgba(0,0,0,0.7)", color: "#fff",
                            fontSize: "9px", padding: "2px", overflow: "hidden",
                            whiteSpace: "nowrap", textOverflow: "ellipsis",
                            pointerEvents: "none"
                        });

                        // Video Badge
                        if (isVid) {
                            const badge = document.createElement("div");
                            badge.textContent = "▶";
                            Object.assign(badge.style, {
                                position: "absolute", top: "2px", right: "2px",
                                color: "#0af", fontSize: "10px", fontWeight:"bold",
                                textShadow: "0 1px 2px #000"
                            });
                            item.appendChild(badge);
                        }

                        item.appendChild(img);
                        item.appendChild(lbl);
                        grid.appendChild(item);
                    });
                    
                    if (matches.length === 0) {
                        grid.innerHTML = "<div style='color:#666; padding:10px; font-size:11px;'>No matches found</div>";
                    }
                };

                // Initialize
                container.appendChild(searchBar);
                container.appendChild(grid);
                
                // Event Listeners
                searchBar.addEventListener("input", (e) => renderGrid(e.target.value));
                searchBar.addEventListener("mousedown", (e) => e.stopPropagation()); // Prevent node dragging
                
                // Initial Render
                renderGrid();

                this.addDOMWidget("asset_browser", "div", container, { serialize: false });
                
                // Size
                this.setSize([300, 400]);
                
                return r;
            };
        }
    }
});