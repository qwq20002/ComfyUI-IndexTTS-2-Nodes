import torch
import torchaudio
import numpy as np
from transformers import pipeline

class AudioToEmotion:
    def __init__(self):
        self.classifier = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reference_audio": ("AUDIO",),
                # 新增：全局强度控制 (0.0 ~ 2.0)，默认 0.5 让它收敛一点
                "intensity": ("FLOAT", {"default": 0.6, "min": 0.1, "max": 2.0, "step": 0.1}),
                # 新增：中性偏置 (0.0 ~ 1.0)，这才是稀释过激情感的关键
                "neutral_fill": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 1.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("Happy", "Angry", "Sad", "Fear", "Hate", "Love", "Surprise", "Neutral")
    FUNCTION = "analyze_emotion"
    CATEGORY = "IndexTTS/Utils"

    def analyze_emotion(self, reference_audio, intensity=0.6, neutral_fill=0.3):
        if self.classifier is None:
            self.classifier = pipeline("audio-classification", model="superb/wav2vec2-base-superb-er")

        # ... (音频预处理部分保持不变，省略以节省空间) ...
        # ... 假设 waveform 已经处理好并转为 numpy ...
        waveform = self._preprocess_audio(reference_audio) # 假设你封装了上面的处理逻辑

        # --- 核心修改开始 ---
        
        # 1. 获取原始分数
        results = self.classifier(waveform, top_k=None)
        scores = {item['label']: item['score'] for item in results}

        # 2. 提取并应用 "软化" 逻辑
        # 这里的关键是：不要直接输出原始概率，而是要允许 Neutral 占据主导地位
        
        # 映射字典
        emo_map = {
            "Happy": scores.get('happy', 0.0),
            "Angry": scores.get('angry', 0.0),
            "Sad": scores.get('sad', 0.0),
            "Fear": scores.get('fear', 0.0),
            "Surprise": scores.get('surprise', 0.0),
            "Neutral": scores.get('neutral', 0.0),
            "Hate": 0.0, # 模型无此输出
            "Love": 0.0  # 模型无此输出
        }

        # 3. 算法优化：非线性压缩 + 动态稀释
        # 如果 intensity < 1.0，我们会压制非 Neutral 的情感
        # 如果 intensity > 1.0，我们会放大它们
        
        final_scores = {}
        
        for k, v in emo_map.items():
            if k == "Neutral":
                continue # Neutral 单独处理
            
            # 幂函数处理：平方会压制低分值 (0.4^2 = 0.16)，保留高分值
            # 配合 intensity 系数
            val = (v ** 1.5) * intensity
            final_scores[k] = float(val)

        # 4. Neutral 的特殊处理：填充剩余空间
        # 我们人为地给 Neutral 加一个保底值 (neutral_fill)
        # 这样即使其他情感算出来是 0.4，Neutral 只要够大，归一化后 Fear 就不会变成 100%
        
        raw_neutral = emo_map["Neutral"]
        # Neutral = 原始值 + 人工填充 - (其他情感的总和 * 系数) -> 动态平衡
        # 简单粗暴点：直接给 Neutral 加权重
        final_scores["Neutral"] = float(raw_neutral + neutral_fill)

        return (
            final_scores["Happy"], 
            final_scores["Angry"], 
            final_scores["Sad"], 
            final_scores["Fear"], 
            final_scores["Hate"], 
            final_scores["Love"], 
            final_scores["Surprise"], 
            final_scores["Neutral"]
        )

    def _preprocess_audio(self, reference_audio):
        # 把之前的音频处理逻辑放在这里
        waveform = reference_audio["waveform"]
        sr = reference_audio["sample_rate"]
        if not isinstance(waveform, torch.Tensor):
            waveform = torch.tensor(waveform)
        if waveform.dim() == 3: 
            waveform = waveform[0].mean(dim=0) 
        elif waveform.dim() == 2:
            waveform = waveform.mean(dim=0)
        target_sr = 16000
        if sr != target_sr:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
            waveform = resampler(waveform)
        return waveform.cpu().numpy()