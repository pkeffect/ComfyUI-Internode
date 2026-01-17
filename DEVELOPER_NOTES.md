# Internode Developer Context

## Architecture
- **Structure:** Domain-Driven Design (`internode/dsp`, `internode/vst`, etc.).
- **Dual Engine:** UI uses Web Audio API (JS), Backend uses PyTorch/Torchaudio (Python).
- **Frontend:** JS files live in `/js`. Python nodes live in `/internode/<category>/`.

## Rules for New Nodes
1. **Inputs:** Always use standard ComfyUI types (`AUDIO`, `IMAGE`, `FLOAT`, `INT`).
2. **Widgets:** If a node needs custom UI (knobs, textareas), a matching JS file is required in `/js`.
3. **Registration:** New nodes must be registered in the root `__init__.py` inside a `try/except` block to prevent crashes if dependencies are missing.
4. **Dependencies:** If a new library is needed, check `requirements.txt` first.

## Current Categories
- `dsp`: Mixing, Audio I/O.
- `vst`: Hosting instruments/effects.
- `analysis`: Reactivity, Spectrograms.
- `generative`: ACE-Step, MusicGen.
- `utils`: Sticky notes, Markdown.

---

## ComfyUI Nodes 1.0 vs 2.0 Compatibility Guide

### Problem Statement
ComfyUI's Nodes 2.0 rendering system fundamentally changed how widgets are displayed. Unlike Nodes 1.0 (which respected `computeSize` and `hidden` flags), **Nodes 2.0 iterates through the `node.widgets` array and renders every widget**, regardless of visibility flags. This causes custom UI nodes (like Mixer, Studio Surface, etc.) to show both the custom UI AND all underlying parameter widgets, resulting in massive vertical stretching.

### Root Cause Analysis
1. **Nodes 1.0 Behavior:**
   - Respects `widget.computeSize = () => [0, -4]` to hide widgets
   - Respects `widget.hidden = true` flag
   - Custom DOM widgets render cleanly over hidden widgets

2. **Nodes 2.0 Behavior:**
   - **Ignores `hidden` flags** - still renders the widget
   - **Ignores `computeSize` return values** - calculates size from widget count
   - Renders ALL widgets in the `node.widgets` array sequentially
   - Results in visible parameter widgets below the custom UI

### The Solution: Widget Array Manipulation

The only reliable way to hide widgets in Nodes 2.0 is to **physically remove them from the `node.widgets` array** while maintaining functionality through a custom accessor pattern.

#### Implementation Pattern (Generic)

```javascript
function buildCustomUI(node) {
    // 1. STORE ORIGINAL WIDGETS
    // Before modifying the array, preserve the original for later access
    if (!node._customNodeOriginalWidgets) {
        node._customNodeOriginalWidgets = node.widgets ? [...node.widgets] : [];
    }
    
    // 2. WIDGET SEPARATION FUNCTION
    const hideWidgets = () => {
        if (!node.widgets) return;
        
        const widgetsToKeep = [];    // Visible (DOM widget only)
        const widgetsToHide = [];    // Hidden but functional
        
        node.widgets.forEach(w => {
            if (w.name === "custom_ui") {  // Your DOM widget name
                widgetsToKeep.push(w);
            } else {
                widgetsToHide.push(w);
                w.computeSize = () => [0, -4];  // For Nodes 1.0 compat
                if (w.element) w.element.style.display = "none";
            }
        });
        
        // KEY: Replace the widgets array with only visible widgets
        node.widgets = widgetsToKeep;
        node._customNodeHiddenWidgets = widgetsToHide;
    };
    
    // 3. CUSTOM WIDGET ACCESSOR
    // Provide a function to access hidden widgets by name
    if (!node._customNodeGetWidget) {
        node._customNodeGetWidget = (name) => {
            // Check visible first
            const visible = node.widgets ? node.widgets.find(w => w.name === name) : null;
            if (visible) return visible;
            
            // Check hidden storage
            const hidden = node._customNodeHiddenWidgets ? 
                          node._customNodeHiddenWidgets.find(w => w.name === name) : null;
            if (hidden) return hidden;
            
            // Fallback to original
            return node._customNodeOriginalWidgets ? 
                   node._customNodeOriginalWidgets.find(w => w.name === name) : null;
        };
    }
    
    hideWidgets();
    node.customNodeHideWidgets = hideWidgets; // Attach for reconfiguration
    
    // 4. BUILD YOUR CUSTOM UI
    const root = document.createElement("div");
    Object.assign(root.style, {
        position: "relative",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        boxSizing: "border-box"
    });
    
    // ... build your custom UI elements ...
    
    // 5. ADD DOM WIDGET WITH FIXED HEIGHT
    const domWidget = node.addDOMWidget("custom_ui", "div", root, { serialize: false });
    domWidget.computedHeight = 600;  // YOUR DESIRED HEIGHT
    
    root.style.minHeight = "600px";
    root.style.height = "600px";
    
    // 6. SET NODE SIZE
    node.setSize([400, 600]);  // YOUR DESIRED SIZE
    node.resizable = true;
}
```

#### Implementation in Extension Registration

```javascript
app.registerExtension({
    name: "YourExtension.CustomNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "YourCustomNode") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                buildCustomUI(this);
                
                // 7. OVERRIDE COMPUTESIZE
                // Prevent Nodes 2.0 from calculating height from hidden widgets
                this.computeSize = function(out) {
                    const baseWidth = 400;   // YOUR WIDTH
                    const baseHeight = 600;  // YOUR HEIGHT
                    
                    // Start with title bar
                    let height = LiteGraph.NODE_TITLE_HEIGHT || 30;
                    
                    // Add only visible widget heights (DOM widget)
                    if (this.widgets) {
                        for (let w of this.widgets) {
                            if (w.name === "custom_ui" && w.computedHeight) {
                                height += w.computedHeight;
                            }
                        }
                    }
                    
                    // Preserve manual resizing
                    const width = this.size && this.size[0] > baseWidth ? this.size[0] : baseWidth;
                    const finalHeight = this.size && this.size[1] ? this.size[1] : height;
                    
                    if (out) {
                        out[0] = width;
                        out[1] = finalHeight;
                        return out;
                    }
                    return [width, finalHeight];
                };
                
                // 8. HANDLE RECONFIGURATION (loading saved workflows)
                const originalConfigure = this.configure;
                this.configure = function(info) {
                    originalConfigure?.apply(this, arguments);
                    if (this.customNodeHideWidgets) { 
                        requestAnimationFrame(() => this.customNodeHideWidgets()); 
                    }
                }
                
                return r;
            };
        }
    }
});
```

#### Accessing Hidden Widgets in Your UI Code

When you need to read/write widget values in your custom UI:

```javascript
function getParamValue(node, paramName) {
    // Use custom accessor instead of node.widgets.find()
    const widget = node._customNodeGetWidget ? 
                   node._customNodeGetWidget(paramName) : 
                   (node.widgets ? node.widgets.find(w => w.name === paramName) : null);
    
    return widget ? widget.value : null;
}

function setParamValue(node, paramName, value) {
    const widget = node._customNodeGetWidget ? 
                   node._customNodeGetWidget(paramName) : null;
    
    if (widget) {
        widget.value = value;
        node.setDirtyCanvas(true);  // Trigger redraw
    }
}
```

### Key Principles

1. **Never rely on visibility flags alone** - Nodes 2.0 ignores them
2. **Physically remove widgets from `node.widgets` array** - Only way to prevent rendering
3. **Always provide a custom accessor** - Hidden widgets still need to be functional
4. **Override `computeSize`** - Prevent auto-calculation from widget count
5. **Set `computedHeight` on DOM widget** - Tell the system how much space you need
6. **Handle `configure` event** - Re-hide widgets when loading saved workflows
7. **Use `requestAnimationFrame` in configure** - Ensure DOM is ready before hiding

### Testing Checklist

- [ ] Node displays correctly in Nodes 1.0 mode
- [ ] Node displays correctly in Nodes 2.0 mode
- [ ] No parameter widgets visible in either mode
- [ ] Custom UI fills the entire node
- [ ] Node can be resized (if `resizable = true`)
- [ ] Resizing works in both directions (expand/contract)
- [ ] Widget values persist when saved and reloaded
- [ ] Automated parameters (linked inputs) still work
- [ ] Parameter changes trigger graph updates correctly

### Affected Nodes in Internode

The following nodes use this pattern:
- `InternodeAudioMixer` / `InternodeAudioMixer8` (`js/internode_mixer.js`)
- `InternodeStudioSurface` (`js/internode_studio.js`)
- `IntermodeStickyNote` (`js/internode_sticky.js`)
- `InternodeMarkdownNode` (`js/internode_markdown.js`)
- `InternodeUniversalPlayer` (`js/internode_player.js`)
- `InternodeABComparator` (`js/internode_comparator.js`)

### Common Pitfalls

❌ **DON'T:** Just set `widget.hidden = true` (Nodes 2.0 ignores it)
❌ **DON'T:** Use absolute positioning to cover widgets (breaks resizing)
❌ **DON'T:** Delete widgets entirely (breaks serialization/deserialization)
✅ **DO:** Remove from array, store separately, provide accessor
✅ **DO:** Override `computeSize` to return correct dimensions
✅ **DO:** Use `position: relative` for container, let it flow naturally

---

## General Development Guidelines

- Never remove anything unless asked specifically
- If unsure, ask
- Never truncate files