// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_asset_browser.js
// VERSION: 3.4.0 (Lazy Loading Fix)

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("%c#### Internode: Asset Browser Loaded (Lazy)", "color: cyan; font-weight: bold;");

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
                let fileList = fileWidget.options.values || [];
                let filteredList = [...fileList]; // Current filtered view
                let renderedCount = 0;
                const BATCH_SIZE = 50;
                
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
                
                // Sentinel element for infinite scroll
                const sentinel = document.createElement("div");
                sentinel.style.height = "20px";
                sentinel.style.gridColumn = "1 / -1"; 

                // Function to render a batch
                const renderBatch = () => {
                    const fragment = document.createDocumentFragment();
                    const nextBatch = filteredList.slice(renderedCount, renderedCount + BATCH_SIZE);
                    
                    if (nextBatch.length === 0) return false; // No more items

                    nextBatch.forEach(filename => {
                        const item = document.createElement("div");
                        Object.assign(item.style, {
                            aspectRatio: "1/1", cursor: "pointer",
                            backgroundColor: "#000", position: "relative",
                            border: filename === fileWidget.value ? "2px solid #0f0" : "1px solid #333"
                        });
                        
                        const url = api.apiURL(`/view?filename=${encodeURIComponent(filename)}&type=input`);
                        const ext = filename.split('.').pop().toLowerCase();
                        const isVid = ['mp4', 'mov', 'avi', 'webm'].includes(ext);
                        
                        // Use CSS Background for performance vs creating img tags initially
                        // Actually img tag with loading="lazy" is good, but intersection observer controls insertion here.
                        const img = document.createElement("img");
                        img.src = url;
                        img.loading = "lazy";
                        Object.assign(img.style, {
                            width: "100%", height: "100%", objectFit: "cover",
                            opacity: "0.8", transition: "opacity 0.2s"
                        });
                        
                        item.onmouseenter = () => img.style.opacity = "1.0";
                        item.onmouseleave = () => img.style.opacity = "0.8";
                        
                        item.onclick = () => {
                            fileWidget.value = filename;
                            Array.from(grid.children).forEach(c => c.style.border = "1px solid #333");
                            item.style.border = "2px solid #0f0";
                        };

                        const lbl = document.createElement("div");
                        lbl.textContent = filename;
                        Object.assign(lbl.style, {
                            position: "absolute", bottom: "0", left: "0", right: "0",
                            backgroundColor: "rgba(0,0,0,0.7)", color: "#fff",
                            fontSize: "9px", padding: "2px", overflow: "hidden",
                            whiteSpace: "nowrap", textOverflow: "ellipsis",
                            pointerEvents: "none"
                        });

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
                        fragment.appendChild(item);
                    });
                    
                    // Insert before sentinel
                    grid.insertBefore(fragment, sentinel);
                    renderedCount += nextBatch.length;
                    return true;
                };

                // Initialize Infinite Scroll Observer
                const observer = new IntersectionObserver((entries) => {
                    if (entries[0].isIntersecting) {
                        renderBatch();
                    }
                }, { root: grid, rootMargin: "200px" });

                // 5. Main Render Function (Reset)
                const resetGrid = (filterText = "") => {
                    grid.innerHTML = "";
                    renderedCount = 0;
                    grid.appendChild(sentinel); // Add sentinel back
                    
                    const lowerFilter = filterText.toLowerCase();
                    filteredList = fileList.filter(f => f.toLowerCase().includes(lowerFilter));
                    
                    if (filteredList.length === 0) {
                        grid.innerHTML = "<div style='color:#666; padding:10px; font-size:11px;'>No matches found</div>";
                    } else {
                        renderBatch(); // Load first batch
                        observer.observe(sentinel);
                    }
                };

                // Initialize
                container.appendChild(searchBar);
                container.appendChild(grid);
                
                // Event Listeners
                searchBar.addEventListener("input", (e) => resetGrid(e.target.value));
                searchBar.addEventListener("mousedown", (e) => e.stopPropagation()); 
                
                // Initial Render
                resetGrid();

                this.addDOMWidget("asset_browser", "div", container, { serialize: false });
                this.setSize([300, 400]);
                
                return r;
            };
        }
    }
});