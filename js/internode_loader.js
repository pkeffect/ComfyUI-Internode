// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_loader.js
// VERSION: 3.0.0

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("%c#### Internode: Loaders UI v4.0.0 Loaded", "color: cyan; font-weight: bold;");

app.registerExtension({
    name: "Internode.Loaders",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        
        const loaderTypes = ["InternodeAudioLoader", "InternodeVideoLoader", "InternodeImageLoader"];
        
        if (loaderTypes.includes(nodeData.name)) {

            let widgetName = "audio_file";
            let acceptTypes = "audio/*,.wav,.mp3,.flac";
            let typeLabel = "Audio";

            if (nodeData.name === "InternodeVideoLoader") {
                widgetName = "video_file";
                acceptTypes = "video/*,.mp4,.mkv,.avi,.mov,.webm";
                typeLabel = "Video";
            } else if (nodeData.name === "InternodeImageLoader") {
                widgetName = "image_file";
                acceptTypes = "image/*,.png,.jpg,.jpeg,.webp,.bmp";
                typeLabel = "Image";
            }

            const updateNodeTitle = (node, widget) => {
                const val = widget.value;
                if (val && val !== "none") {
                    node.title = `${typeLabel}: ${val.split('/').pop()}`;
                } else {
                    node.title = `${typeLabel} Loader`;
                }
            };

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const fileWidget = this.widgets.find(w => w.name === widgetName);
                if(fileWidget) {
                    fileWidget.type = "custom";
                    fileWidget.computeSize = () => [0, -4];
                }

                const container = document.createElement("div");
                Object.assign(container.style, { width: "100%", padding: "5px", boxSizing: "border-box", display: "flex", flexDirection: "column", gap: "5px", alignItems: "center" });

                const previewCtx = document.createElement("div");
                Object.assign(previewCtx.style, { width: "100%", minHeight: "120px", maxHeight: "250px", backgroundColor: "#000", border: "1px solid #333", borderRadius: "4px", display: "flex", justifyContent: "center", alignItems: "center", overflow: "hidden", position: "relative" });
                previewCtx.innerHTML = '<span style="color:#444; font-size:11px; font-family:sans-serif;">No Media</span>';

                this.updatePreview = (filename) => {
                    if (!filename || filename === "none") {
                        previewCtx.innerHTML = '<span style="color:#444; font-size:11px; font-family:sans-serif;">No Media</span>';
                        return;
                    }
                    const url = api.apiURL(`/view?filename=${encodeURIComponent(filename)}&type=input`);
                    previewCtx.innerHTML = "";

                    if (nodeData.name === "InternodeImageLoader") {
                        const img = document.createElement("img");
                        img.src = url;
                        Object.assign(img.style, { maxWidth: "100%", maxHeight: "250px", objectFit: "contain" });
                        previewCtx.appendChild(img);
                    } else if (nodeData.name === "InternodeVideoLoader") {
                        const vid = document.createElement("video");
                        vid.src = url; vid.controls = true; vid.muted = true; vid.preload = "metadata";
                        Object.assign(vid.style, { maxWidth: "100%", maxHeight: "250px" });
                        previewCtx.appendChild(vid);
                    } else { // Audio
                        const wrapper = document.createElement("div");
                        Object.assign(wrapper.style, { width: "90%", textAlign: "center" });
                        wrapper.innerHTML = `<div style="font-size:40px;">🎵</div><div style="font-size:11px; color:#ccc; margin:5px 0; word-break:break-all;">${filename}</div>`;
                        const audio = document.createElement("audio");
                        audio.src = url; audio.controls = true;
                        Object.assign(audio.style, { width: "100%", height: "30px" });
                        wrapper.appendChild(audio);
                        previewCtx.appendChild(wrapper);
                    }
                    node.title = `${typeLabel}: ${filename}`;
                };

                const handleFile = async (file) => {
                    if (!file) return;
                    try {
                        previewCtx.innerHTML = '<span style="color:#0af; font-size:12px;">Uploading...</span>';
                        const formData = new FormData();
                        formData.append('image', file); formData.append('overwrite', 'true');
                        const resp = await api.fetchApi("/upload/image", { method: "POST", body: formData });
                        if (resp.status === 200) {
                            const data = await resp.json();
                            if(fileWidget) {
                                fileWidget.value = data.name;
                                this.updatePreview(data.name);
                            }
                        } else {
                            alert(`Upload failed: ${resp.statusText}`);
                            previewCtx.innerHTML = '<span style="color:#f55;">Upload Failed</span>';
                        }
                    } catch (error) {
                        console.error(error);
                        previewCtx.innerHTML = '<span style="color:#f55;">Error</span>';
                    }
                };

                const button = document.createElement("button");
                button.textContent = `Load ${typeLabel}`;
                Object.assign(button.style, { width: "100%", height: "24px", fontSize: "12px", cursor: "pointer", backgroundColor: "#222", color: "#ccc", border: "1px solid #444", borderRadius: "3px", marginTop: "2px" });
                
                const fileInput = document.createElement("input");
                fileInput.type = "file";
                fileInput.accept = acceptTypes;
                fileInput.style.display = "none";
                
                button.addEventListener("click", (e) => { e.preventDefault(); fileInput.click(); });
                fileInput.addEventListener("change", (e) => { if (e.target.files.length) handleFile(e.target.files[0]); });
                
                container.appendChild(previewCtx);
                container.appendChild(button);
                container.appendChild(fileInput);

                this.addDOMWidget("loader_ui", "div", container, { serialize: false });
                
                this.onDragOver = (e) => { e.preventDefault(); return true; };
                this.onDragDrop = (e) => {
                    e.preventDefault(); e.stopPropagation();
                    if (e.dataTransfer.files.length > 0) {
                        handleFile(e.dataTransfer.files[0]);
                        return true;
                    }
                    return false;
                };

                if(fileWidget && fileWidget.value) this.updatePreview(fileWidget.value);
                this.setSize([300, 320]);
                return r;
            };

            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                onConfigure?.apply(this, arguments);
                const fileWidget = this.widgets.find(w => w.name === widgetName);
                if(fileWidget && this.updatePreview) this.updatePreview(fileWidget.value);
            };
        }
    }
});