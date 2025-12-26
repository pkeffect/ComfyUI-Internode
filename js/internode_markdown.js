// ComfyUI/custom_nodes/ComfyUI-Internode/js/internode_markdown.js
// VERSION: 3.0.0

import { app } from "../../scripts/app.js";

console.log("%c#### Internode: Markdown UI v2.0 Loaded", "color: green; font-weight: bold;");

function parseMarkdown(text) {
    if (!text) return "<span style='color:#666; font-style:italic;'>Empty...</span>";
    
    const lines = text.split('\n');
    let html = '';
    let inCodeBlock = false;
    let inTable = false;
    let tableRows = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        // Code Blocks
        if (line.trim().startsWith('```')) {
            if (inCodeBlock) {
                html += '</pre></div>';
            } else {
                html += '<div style="background:#161b22; padding:10px; border-radius:6px; margin:8px 0; border:1px solid #30363d;"><pre style="margin:0; white-space:pre-wrap; font-family:monospace; color:#e6edf3; font-size:0.9em;">';
            }
            inCodeBlock = !inCodeBlock;
            continue;
        }
        if (inCodeBlock) {
            line = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            html += line + '\n';
            continue;
        }

        // Table detection
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
            if (!inTable) {
                inTable = true;
                tableRows = [];
            }
            tableRows.push(line);
            continue;
        } else if (inTable) {
            // End of table, render it
            html += renderTable(tableRows);
            inTable = false;
            tableRows = [];
        }

        // Horizontal Rule
        if (line.trim() === '---' || line.trim() === '***') {
            html += '<hr style="border:0; border-top:1px solid #30363d; margin:16px 0;">';
            continue;
        }

        // Headers
        if (line.startsWith('#')) {
            const level = line.match(/^#+/)[0].length;
            const content = line.slice(level).trim();
            const size = 1.6 - (level * 0.1); 
            const border = level <= 2 ? 'border-bottom:1px solid #30363d; padding-bottom:0.3em;' : '';
            html += `<h${level} style="margin:20px 0 10px 0; font-size:${size}em; font-weight:600; color:#e6edf3; ${border}">${processInline(content)}</h${level}>`;
            continue;
        }

        // Blockquotes
        if (line.trim().startsWith('>')) {
            const content = line.replace(/^>\s*/, '').trim();
            html += `<blockquote style="border-left:4px solid #30363d; padding-left:16px; margin:16px 0; color:#8b949e;">${processInline(content)}</blockquote>`;
            continue;
        }

        // Numbered Lists
        if (line.match(/^\s*\d+\.\s+(.*)/)) {
            const content = line.replace(/^\s*\d+\.\s+/, '').trim();
            const num = line.match(/^\s*(\d+)\./)[1];
            html += `<div style="display:flex; margin:4px 0;">
                        <span style="color:#8b949e; margin-right:8px; min-width:20px;">${num}.</span>
                        <span style="line-height:1.5;">${processInline(content)}</span>
                     </div>`;
            continue;
        }

        // Unordered Lists
        if (line.match(/^\s*[-*]\s+(.*)/)) {
            const content = line.replace(/^\s*[-*]\s+/, '').trim();
            html += `<div style="display:flex; margin:4px 0;">
                        <span style="color:#8b949e; margin-right:8px;">\u2022</span>
                        <span style="line-height:1.5;">${processInline(content)}</span>
                     </div>`;
            continue;
        }

        // Task Lists
        if (line.match(/^\s*[-*]\s+\[([ xX])\]\s+(.*)/)) {
            const match = line.match(/^\s*[-*]\s+\[([ xX])\]\s+(.*)/);
            const checked = match[1].toLowerCase() === 'x';
            const content = match[2].trim();
            const checkbox = checked 
                ? '<span style="color:#3fb950; margin-right:8px;">\u2611</span>'
                : '<span style="color:#8b949e; margin-right:8px;">\u2610</span>';
            html += `<div style="display:flex; margin:4px 0;">
                        ${checkbox}
                        <span style="line-height:1.5;${checked ? ' text-decoration:line-through; color:#8b949e;' : ''}">${processInline(content)}</span>
                     </div>`;
            continue;
        }

        // Paragraphs
        if (line.trim().length > 0) {
            html += `<p style="margin-bottom:10px; line-height:1.5;">${processInline(line)}</p>`;
        }
    }

    // Handle table at end of input
    if (inTable && tableRows.length > 0) {
        html += renderTable(tableRows);
    }

    return html;
}

function renderTable(rows) {
    if (rows.length < 2) return ''; // Need at least header + separator
    
    let html = '<table style="border-collapse:collapse; margin:16px 0; width:100%;">';
    
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        
        // Skip separator row (contains only dashes and pipes)
        if (row.match(/^\|[\s\-:|]+\|$/)) continue;
        
        const cells = row.split('|').filter((cell, idx, arr) => idx > 0 && idx < arr.length - 1);
        const isHeader = i === 0;
        const tag = isHeader ? 'th' : 'td';
        const bgColor = isHeader ? '#161b22' : (i % 2 === 0 ? '#0d1117' : '#161b22');
        const fontWeight = isHeader ? 'font-weight:600;' : '';
        
        html += '<tr>';
        for (const cell of cells) {
            html += `<${tag} style="border:1px solid #30363d; padding:8px 12px; background:${bgColor}; ${fontWeight}">${processInline(cell.trim())}</${tag}>`;
        }
        html += '</tr>';
    }
    
    html += '</table>';
    return html;
}

function processInline(text) {
    // Process in specific order to handle nesting better
    
    // Escape HTML entities first
    text = text.replace(/&(?![a-zA-Z]+;)/g, '&amp;');
    
    // Images (before links to avoid conflict)
    text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;">');
    
    // Links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:#58a6ff; text-decoration:none;">$1</a>');
    
    // Bold + Italic combined (***text*** or ___text___)
    text = text.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong style="color:#e6edf3;"><em>$1</em></strong>');
    text = text.replace(/___([^_]+)___/g, '<strong style="color:#e6edf3;"><em>$1</em></strong>');
    
    // Bold (**text** or __text__)
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong style="color:#e6edf3;">$1</strong>');
    text = text.replace(/__([^_]+)__/g, '<strong style="color:#e6edf3;">$1</strong>');
    
    // Italic (*text* or _text_) - be careful not to match inside words
    text = text.replace(/(?<![a-zA-Z0-9])\*([^*]+)\*(?![a-zA-Z0-9])/g, '<em style="color:#e6edf3;">$1</em>');
    text = text.replace(/(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])/g, '<em style="color:#e6edf3;">$1</em>');
    
    // Strikethrough (~~text~~)
    text = text.replace(/~~([^~]+)~~/g, '<del style="color:#8b949e;">$1</del>');
    
    // Inline code (`code`) - process last to preserve content
    text = text.replace(/`([^`]+)`/g, '<code style="background:rgba(110,118,129,0.4); padding:2px 5px; border-radius:4px; font-family:monospace;">$1</code>');
    
    return text;
}

app.registerExtension({
    name: "Internode.MarkdownNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "InternodeMarkdownNote") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // 1. Locate and Hide Default Widget
                const textWidget = this.widgets.find(w => w.name === "text");
                if (textWidget) {
                    textWidget.type = "custom";
                    textWidget.computeSize = () => [0, 0];
                    textWidget.draw = function() { return; }; 
                }

                // 2. Main Container
                const container = document.createElement("div");
                Object.assign(container.style, {
                    height: "100%",
                    width: "100%",
                    minHeight: "400px", // FORCE MINIMUM HEIGHT
                    backgroundColor: "#0d1117",
                    border: "1px solid #30363d",
                    borderRadius: "6px",
                    display: "flex",
                    flexDirection: "column",
                    boxSizing: "border-box",
                    overflow: "hidden" 
                });

                // 3. Toolbar (Top)
                const toolbar = document.createElement("div");
                Object.assign(toolbar.style, {
                    height: "40px",
                    width: "100%",
                    backgroundColor: "#161b22",
                    borderBottom: "1px solid #30363d",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0 10px",
                    flexShrink: "0",
                    boxSizing: "border-box"
                });

                const label = document.createElement("span");
                label.textContent = "Markdown Note";
                label.style.color = "#8b949e";
                label.style.fontSize = "12px";
                label.style.fontWeight = "bold";

                const toggleBtn = document.createElement("button");
                Object.assign(toggleBtn.style, {
                    cursor: "pointer",
                    height: "28px",
                    padding: "0 12px",
                    fontSize: "12px",
                    fontWeight: "600",
                    borderRadius: "4px",
                    border: "1px solid #30363d",
                    backgroundColor: "#21262d",
                    color: "#c9d1d9",
                    outline: "none"
                });

                toolbar.appendChild(label);
                toolbar.appendChild(toggleBtn);

                // 4. Content Area (Holds Editor and Preview)
                const contentArea = document.createElement("div");
                Object.assign(contentArea.style, {
                    width: "100%",
                    height: "calc(100% - 40px)",
                    minHeight: "360px", // FORCE EDITOR MINIMUM HEIGHT
                    backgroundColor: "#0d1117",
                    position: "relative",
                    overflow: "hidden"
                });

                // 5. Textarea (Edit Mode)
                const textarea = document.createElement("textarea");
                Object.assign(textarea.style, {
                    width: "100%",
                    height: "100%",
                    backgroundColor: "#1a1f24",
                    color: "#e6edf3",
                    border: "none",
                    padding: "15px",
                    resize: "none",
                    fontSize: "14px",
                    fontFamily: "monospace",
                    lineHeight: "1.5",
                    outline: "none",
                    boxSizing: "border-box",
                    display: "block" 
                });
                
                if(textWidget) textarea.value = textWidget.value;

                // 6. Preview Div (Preview Mode)
                const preview = document.createElement("div");
                Object.assign(preview.style, {
                    width: "100%",
                    height: "100%",
                    padding: "15px",
                    overflowY: "auto",
                    color: "#c9d1d9",
                    fontFamily: "sans-serif",
                    fontSize: "14px",
                    boxSizing: "border-box",
                    display: "none" 
                });

                // 7. Logic
                let isPreview = false; 

                const updateState = () => {
                    if (isPreview) {
                        // Show Preview
                        preview.innerHTML = parseMarkdown(textarea.value);
                        textarea.style.display = "none";
                        preview.style.display = "block";
                        
                        toggleBtn.textContent = "\u270F\uFE0F Edit";
                        toggleBtn.style.backgroundColor = "#21262d"; 
                        toggleBtn.style.color = "#c9d1d9";
                    } else {
                        // Show Edit
                        preview.style.display = "none";
                        textarea.style.display = "block";
                        
                        toggleBtn.textContent = "\uD83D\uDC41\uFE0F Preview";
                        toggleBtn.style.backgroundColor = "#238636"; 
                        toggleBtn.style.color = "#fff";
                    }
                };

                // Initialize in Edit Mode
                updateState();

                // Events
                toggleBtn.addEventListener("mousedown", (e) => e.stopPropagation());
                toggleBtn.onclick = (e) => {
                    isPreview = !isPreview;
                    updateState();
                };

                textarea.addEventListener("input", () => {
                    if(textWidget) textWidget.value = textarea.value;
                });

                // Stop events
                const stopProp = (e) => e.stopPropagation();
                textarea.addEventListener("mousedown", stopProp);
                textarea.addEventListener("wheel", stopProp, {passive: true});
                preview.addEventListener("mousedown", stopProp);
                preview.addEventListener("wheel", stopProp, {passive: true});

                // Assemble
                contentArea.appendChild(textarea);
                contentArea.appendChild(preview);
                container.appendChild(toolbar);
                container.appendChild(contentArea);

                this.addDOMWidget("markdown_ui", "div", container, { serialize: false });

                // **UPDATED DEFAULT SIZE**
                this.setSize([500, 700]);
                
                return r;
            };
        }
    },
});
