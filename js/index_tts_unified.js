import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Comfy.IndexTTS2.UnifiedMode",
    async nodeCreated(node) {
        if (node.comfyClass !== "IndexTTS2UnifiedNode") return;

        const WIDGET_GROUPS = {
            "Audio Reference": ["emotion_weight"],
            "Emotion Vector": [
                "Happy", "Angry", "Sad", "Fear", 
                "Hate", "Love", "Surprise", "Neutral"
            ],
            "Text Description": ["emotion_description"]
        };

        const modeWidget = node.widgets.find((w) => w.name === "control_mode");

        const updateVisibility = () => {
            const currentMode = modeWidget.value;
            const allControlledWidgets = Object.values(WIDGET_GROUPS).flat();

            for (const w of node.widgets) {
                if (!allControlledWidgets.includes(w.name)) continue;

                const shouldShow = WIDGET_GROUPS[currentMode]?.includes(w.name);

                if (shouldShow) {
                    if (w.type === "hidden") {
                        // 1. 恢复类型
                        w.type = w.origType;
                        
                        // 2. 恢复尺寸计算逻辑：如果是实例方法就还原，如果是继承方法就删除屏蔽
                        if (w.origComputeSize !== undefined) {
                            w.computeSize = w.origComputeSize;
                        } else {
                            delete w.computeSize; 
                        }
                        
                        // 3. 恢复绘制逻辑
                        if (w.origDraw !== undefined) {
                            w.draw = w.origDraw;
                        } else {
                            delete w.draw; 
                        }

                        // 4. 恢复 DOM 元素（针对多行文本框）
                        if (w.inputEl) {
                            w.inputEl.style.display = "";
                        }
                    }
                } else {
                    if (w.type !== "hidden") {
                        w.origType = w.type;
                        
                        // 只有当实例上确实存在覆盖方法时才保存，否则保存为 undefined
                        w.origComputeSize = Object.hasOwn(w, 'computeSize') ? w.computeSize : undefined;
                        w.origDraw = Object.hasOwn(w, 'draw') ? w.draw : undefined;

                        w.type = "hidden";
                        w.computeSize = () => [0, -4];
                        w.draw = () => {};

                        if (w.inputEl) {
                            w.inputEl.style.display = "none";
                        }
                    }
                }
            }

            // 【核心修复：强制重算节点尺寸】
            // 先把高度临时设为极小值，强制 computeSize 根据当前可见控件重新撑开真实高度
            const currentWidth = node.size[0];
            node.setSize([currentWidth, 10]); 
            
            let newSize = node.computeSize();
            newSize[0] = currentWidth; // 保持用户拖拽的宽度不变
            node.setSize(newSize);
            
            node.setDirtyCanvas(true, true);
            if (app.graph) {
                app.graph.setDirtyCanvas(true, true);
            }
        };

        modeWidget.callback = () => {
            updateVisibility();
        };

        // 延迟执行以确保所有内部 DOM 挂载完毕
        setTimeout(updateVisibility, 100);
    }
});