import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Comfy.IndexTTS2.UnifiedMode",
    async nodeCreated(node) {
        if (node.comfyClass !== "IndexTTS2UnifiedNode") return;

        // 定义每个模式对应的控件名称（必须与 Python 中的 key 完全一致）
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
            
            // 获取所有受影响的控件名称
            const allControlledWidgets = Object.values(WIDGET_GROUPS).flat();

            for (const w of node.widgets) {
                if (!allControlledWidgets.includes(w.name)) continue;
                if (w.type === "converted-widget" || w.name === "Happy" && node.inputs?.some(i => i.name === "Happy")) {continue; }
                // 判断当前控件是否属于当前选中的模式
                const shouldShow = WIDGET_GROUPS[currentMode]?.includes(w.name);

                if (shouldShow) {
                    // 恢复显示
                    w.type = w.origType || w.type;
                    w.options = w.origOptions || w.options;
                    w.draw=w.origDraw;
                    // 恢复高度（通常数字/滑动条控件高度在 20 左右）
                    w.computeSize = w.origComputeSize; 
                } else {
                    // 彻底隐藏
                    if (w.type !== "hidden") {
                        w.origType = w.type;
                        w.origOptions = w.options;
                        w.origComputeSize = w.computeSize;
                        w.draw= function(ctx,node,widght_width,y,widget_height){
                        };
                        w.type = "hidden";
                        // 强制高度归零，防止占用空白位置
                        w.computeSize = () => [0, -4]; 
                    }
                }
            }
            const currentWidth = node.size[0];
            let size = node.computeSize();
            if (size[1] < 100) size[1] = 100;
            size[0]=currentWidth;
            node.setSize(size);
            node.setDirtyCanvas(true, true);
            
        };

        // 绑定回调：用户切换下拉菜单时触发
        modeWidget.callback = () => {
            updateVisibility();
        };

        // 延迟执行一次初始化，确保所有 Widget 都已渲染完毕
        setTimeout(updateVisibility, 100);
    }
});