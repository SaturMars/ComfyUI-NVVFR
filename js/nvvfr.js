import { app } from '../../../scripts/app.js'
import { api } from '../../../scripts/api.js'

function chainCallback(object, property, callback) {
    if (object == undefined) {
        console.error("Tried to add callback to non-existant object")
        return;
    }
    if (property in object && object[property]) {
        const callback_orig = object[property]
        object[property] = function () {
            const r = callback_orig.apply(this, arguments);
            return callback.apply(this, arguments) ?? r
        };
    } else {
        object[property] = callback;
    }
}

function addVideoPreview(nodeType, isInput=true) {
    chainCallback(nodeType.prototype, "onNodeCreated", function() {
        var element = document.createElement("div");
        const previewNode = this;
        var previewWidget = this.addDOMWidget("videopreview", "preview", element, {
            serialize: false,
            hideOnZoom: false,
            getValue() {
                return element.value;
            },
            setValue(v) {
                element.value = v;
            },
        });
        
        previewWidget.computeSize = function(width) {
            if (this.aspectRatio && !this.parentEl.hidden) {
                let height = (previewNode.size[0]-20)/ this.aspectRatio + 10;
                if (!(height > 0)) {
                    height = 0;
                }
                this.computedHeight = height + 10;
                return [width, height];
            }
            return [width, -4];
        }
        
        element.addEventListener('contextmenu', (e)  => {
            e.preventDefault()
            return app.canvas._mousedown_callback(e)
        }, true);
        
        element.addEventListener('pointerdown', (e)  => {
            e.preventDefault()
            return app.canvas._mousedown_callback(e)
        }, true);
        
        element.addEventListener('mousewheel', (e)  => {
            e.preventDefault()
            return app.canvas._mousewheel_callback(e)
        }, true);
        
        element.addEventListener('pointermove', (e)  => {
            e.preventDefault()
            return app.canvas._mousemove_callback(e)
        }, true);
        
        element.addEventListener('pointerup', (e)  => {
            e.preventDefault()
            return app.canvas._mouseup_callback(e)
        }, true);
        
        previewWidget.value = {hidden: false, paused: false, params: {}, muted: true}
        previewWidget.parentEl = document.createElement("div");
        previewWidget.parentEl.className = "vhs_preview";
        previewWidget.parentEl.style['width'] = "100%"
        element.appendChild(previewWidget.parentEl);
        
        previewWidget.videoEl = document.createElement("video");
        previewWidget.videoEl.controls = false;
        previewWidget.videoEl.loop = true;
        previewWidget.videoEl.muted = true;
        previewWidget.videoEl.style['width'] = "100%"
        
        previewWidget.videoEl.addEventListener("loadedmetadata", () => {
            previewWidget.aspectRatio = previewWidget.videoEl.videoWidth / previewWidget.videoEl.videoHeight;
            fitHeight(this);
        });
        
        previewWidget.videoEl.addEventListener("error", () => {
            previewWidget.parentEl.hidden = true;
            fitHeight(this);
        });
        
        previewWidget.videoEl.onmouseenter =  () => {
            previewWidget.videoEl.muted = previewWidget.value.muted
        };
        
        previewWidget.videoEl.onmouseleave = () => {
            previewWidget.videoEl.muted = true;
        };

        previewWidget.parentEl.appendChild(previewWidget.videoEl)
        
        this.updateParameters = (params, force_update = false) => {
            if (!previewWidget.value.params) {
                if(typeof(previewWidget.value) != 'object') {
                    previewWidget.value =  {hidden: false, paused: false}
                }
                previewWidget.value.params = {}
            }
            Object.assign(previewWidget.value.params, params)
            
            if (force_update) {
                previewWidget.updateSource();
            } else {
                setTimeout(() => previewWidget.updateSource(), 100);
            }
        };
        
        previewWidget.updateSource = function () {
            if (this.value.params == undefined) {
                return;
            }
            
            let params = {}
            Object.assign(params, this.value.params);
            params.timestamp = Date.now()
            this.parentEl.hidden = this.value.hidden;
            
            if (params.format?.split('/')[0] == 'video' || params.format == 'folder') {
                this.videoEl.autoplay = !this.value.paused && !this.value.hidden;
                this.videoEl.src = api.apiURL('/view?' + new URLSearchParams(params));
                this.videoEl.hidden = false;
            }
        }
        
        previewWidget.callback = previewWidget.updateSource
    });
}

function addPreviewOptions(nodeType) {
    chainCallback(nodeType.prototype, "getExtraMenuOptions", function(_, options) {
        let optNew = []
        const previewWidget = this.widgets.find((w) => w.name === "videopreview");

        let url = null
        if (previewWidget?.videoEl?.hidden == false && previewWidget.videoEl.src) {
            if (['input', 'output', 'temp'].includes(previewWidget.value.params.type)) {
                url = api.apiURL('/view?' + new URLSearchParams(previewWidget.value.params));
            }
        }
        
        if (url) {
            optNew.push(
                {
                    content: "Open preview",
                    callback: () => {
                        window.open(url, "_blank")
                    },
                },
                {
                    content: "Save preview",
                    callback: () => {
                        const a = document.createElement("a");
                        a.href = url;
                        a.setAttribute("download", previewWidget.value.params.filename);
                        document.body.append(a);
                        a.click();
                        requestAnimationFrame(() => a.remove());
                    },
                }
            );
        }
        
        const PauseDesc = (previewWidget.value.paused ? "Resume" : "Pause") + " preview";
        if(previewWidget.videoEl.hidden == false) {
            optNew.push({content: PauseDesc, callback: () => {
                if(previewWidget.value.paused) {
                    previewWidget.videoEl?.play();
                } else {
                    previewWidget.videoEl?.pause();
                }
                previewWidget.value.paused = !previewWidget.value.paused;
            }});
        }
        
        const visDesc = (previewWidget.value.hidden ? "Show" : "Hide") + " preview";
        optNew.push({content: visDesc, callback: () => {
            if (!previewWidget.videoEl.hidden && !previewWidget.value.hidden) {
                previewWidget.videoEl.pause();
            } else if (previewWidget.value.hidden && !previewWidget.videoEl.hidden && !previewWidget.value.paused) {
                previewWidget.videoEl.play();
            }
            previewWidget.value.hidden = !previewWidget.value.hidden;
            previewWidget.parentEl.hidden = previewWidget.value.hidden;
            fitHeight(this);
        }});
        
        const muteDesc = (previewWidget.value.muted ? "Unmute" : "Mute") + " Preview"
        optNew.push({content: muteDesc, callback: () => {
            previewWidget.value.muted = !previewWidget.value.muted
        }})
        
        if(options.length > 0 && options[0] != null && optNew.length > 0) {
            optNew.push(null);
        }
        options.unshift(...optNew);
    });
}

function fitHeight(node) {
    node.setSize([node.size[0], node.computeSize([node.size[0], node.size[1]])[1]])
    node?.graph?.setDirtyCanvas(true);
}

app.registerExtension({
    name: "NVVFR.Preview",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData?.name == "NVVFR") {
            addVideoPreview(nodeType, false);
            addPreviewOptions(nodeType);
            
            chainCallback(nodeType.prototype, "onExecuted", function(message) {
                console.log("NVVFR onExecuted message:", message);
                
                // 检查message的结构
                if (message && message.output_path) {
                    let outputPath = message.output_path;
                    
                    // 如果outputPath是数组，取第一个元素
                    if (Array.isArray(outputPath)) {
                        outputPath = outputPath[0];
                    }
                    
                    // 确保outputPath是字符串
                    if (typeof outputPath === 'string') {
                        console.log("NVVFR output path:", outputPath);
                        
                        const filename = outputPath.split('/').pop().split('\\').pop();
                        
                        // 构建预览参数
                        let params = {
                            filename: filename,
                            type: "output",
                            format: "video/mp4",
                            fullpath: outputPath
                        };
                        
                        console.log("NVVFR preview params:", params);
                        
                        // 更新预览
                        this.updateParameters(params, true);
                        
                        // 自动播放预览
                        setTimeout(() => {
                            const previewWidget = this.widgets.find((w) => w.name === "videopreview");
                            if (previewWidget && previewWidget.videoEl) {
                                previewWidget.value.paused = false;
                                previewWidget.value.hidden = false;
                                previewWidget.videoEl.autoplay = true;
                                previewWidget.videoEl.muted = true;
                                previewWidget.parentEl.hidden = false;
                                previewWidget.updateSource();
                                
                                // 确保视频开始播放
                                previewWidget.videoEl.play().catch(e => {
                                    console.log("Auto-play was prevented, user interaction required");
                                });
                            }
                        }, 500);
                    } else {
                        console.error("NVVFR: outputPath is not a string:", typeof outputPath, outputPath);
                    }
                } else {
                    console.error("NVVFR: No output_path found in message:", message);
                }
            });
        }
    }
});
