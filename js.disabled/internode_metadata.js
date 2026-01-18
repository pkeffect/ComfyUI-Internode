// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_metadata.js
// VERSION: 3.1.0

import { app } from "../../scripts/app.js";

console.log("%c#### Internode: Metadata Inspector Loaded", "color: cyan; font-weight: bold;");

app.registerExtension({
    name: "Internode.MetadataInspector",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeMetadataInspector") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // 1. Container
                const container = document.createElement("div");
                Object.assign(container.style, {
                    width: "100%", height: "100%",
                    backgroundColor: "#111", 
                    color: "#0f0",
                    fontFamily: "monospace",
                    fontSize: "11px",
                    padding: "10px",
                    boxSizing: "border-box",
                    overflow: "auto",
                    whiteSpace: "pre-wrap",
                    borderRadius: "4px",
                    border: "1px solid #333"
                });
                
                container.textContent = "Run node to inspect metadata...";

                this.addDOMWidget("metadata_view", "div", container, { serialize: false });

                // 2. Handle Output
                this.onExecuted = function (message) {
                    if (message && message.json) {
                        try {
                            // Syntax Highlight
                            const obj = JSON.parse(message.json[0]);
                            const formatted = JSON.stringify(obj, null, 2);
                            
                            // Simple highlighting
                            container.innerHTML = syntaxHighlight(formatted);
                        } catch (e) {
                            container.textContent = message.json[0];
                        }
                    }
                };

                this.setSize([400, 300]);
                return r;
            };
        }
    }
});

// Helper for Colors
function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        var style = 'color: #ff5e5e;'; // Number red
        
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
                style = 'color: #88c0d0; font-weight: bold;'; // Key Blue
            } else {
                cls = 'string';
                style = 'color: #a3be8c;'; // String Green
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
            style = 'color: #d08770;'; // Bool Orange
        } else if (/null/.test(match)) {
            cls = 'null';
            style = 'color: #5e81ac;'; // Null Blue
        }
        return '<span style="' + style + '">' + match + '</span>';
    });
}