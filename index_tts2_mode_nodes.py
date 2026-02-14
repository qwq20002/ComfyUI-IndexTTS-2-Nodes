import json
import torch
import numpy as np
from typing import Any, Tuple

from .indextts2 import IndexTTS2Loader, IndexTTS2Engine

# Global shared loader/engine to avoid duplicating model weights across nodes
_GLOBAL_LOADER = IndexTTS2Loader()
_GLOBAL_ENGINE = IndexTTS2Engine(_GLOBAL_LOADER)


class _IndexTTS2BaseMixin:
    @staticmethod
    def _process_audio_input(audio: Any) -> Tuple[np.ndarray, int]:
        if isinstance(audio, dict) and "waveform" in audio and "sample_rate" in audio:
            wave = audio["waveform"]
            sr = int(audio["sample_rate"])
            if isinstance(wave, torch.Tensor):
                if wave.dim() == 3:
                    wave = wave[0, 0].detach().cpu().numpy()
                elif wave.dim() == 1:
                    wave = wave.detach().cpu().numpy()
                else:
                    wave = wave.flatten().detach().cpu().numpy()
            elif isinstance(wave, np.ndarray):
                if wave.ndim == 3:
                    wave = wave[0, 0]
                elif wave.ndim == 2:
                    wave = wave[0]
            return wave.astype(np.float32), sr
        elif isinstance(audio, tuple) and len(audio) == 2:
            wave, sr = audio
            if isinstance(wave, torch.Tensor):
                wave = wave.detach().cpu().numpy()
            return wave.astype(np.float32), int(sr)
        else:
            raise ValueError("AUDIO input must be ComfyUI dict or (wave, sr)")

    @classmethod
    def _base_inputs(cls):
        return {
            "text": ("STRING", {"multiline": True, "default": "Hello, this is IndexTTS2."}),
            "reference_audio": ("AUDIO",),
            "mode": (["Auto", "Duration", "Tokens"], {"default": "Auto"}),
        }

    @classmethod
    def _common_optional(cls):
        return {
            # Advanced generation parameters
            "do_sample_mode": (["off", "on"], {"default": "on"}),
            "temperature": ("FLOAT", {"default": 0.8, "min": 0.1, "max": 2.0, "step": 0.05}),
            "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
            "top_k": ("INT", {"default": 30, "min": 0, "max": 100, "step": 1}),
            "num_beams": ("INT", {"default": 3, "min": 1, "max": 10, "step": 1}),
            "repetition_penalty": ("FLOAT", {"default": 10.0, "min": 1.0, "max": 10.0, "step": 0.1}),
            "length_penalty": ("FLOAT", {"default": 0.0, "min": -2.0, "max": 2.0, "step": 0.1}),
            "max_mel_tokens": ("INT", {"default": 1815, "min": 50, "max": 1815, "step": 5}),
            "max_tokens_per_sentence": ("INT", {"default": 120, "min": 0, "max": 600, "step": 5}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 2**32 - 1}),
            # External cache control dict from utility node
            "cache_control": (["off", "on"], {"default": "off"}),
        }

    def _do_generate(self, engine: IndexTTS2Engine, **kwargs):
        sr, wave, sub = engine.generate(**kwargs)
        wave_t = torch.tensor(wave, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        audio = {"waveform": wave_t, "sample_rate": int(sr)}
        return audio, kwargs.get("seed", 0), (sub or "")

class IndexTTS2UnifiedNode(_IndexTTS2BaseMixin):
    @classmethod
    def INPUT_TYPES(cls):
        # 1. 获取基础参数 (text, reference_audio, mode)
        required = cls._base_inputs()
        
        # 2. 插入我们的“模式切换开关”
        # 注意：这里加了一个 control_mode
        required["control_mode"] = (["Audio Reference", "Emotion Vector", "Text Description"], {"default": "Audio Reference"})

        # 3. 获取通用可选参数 (temperature, seed, etc.)
        optional = cls._common_optional().copy()

        # 4. 合并所有模式的特有参数到 optional 中
        
        # [Audio Mode] 参数
        optional["emo_ref_audio"] = ("AUDIO",)
        optional["emotion_weight"] = ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.4, "step": 0.05})

        # [Vector Mode] 参数 (保留你想要的8个滑块)
        # 为了方便 JS 管理，名字保持原样
        emotions = ["Happy", "Angry", "Sad", "Fear", "Hate", "Love", "Surprise", "Neutral"]
        for emo in emotions:
            optional[emo] = ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.4, "step": 0.01})

        # [Text Mode] 参数
        optional["emotion_description"] = ("STRING", {"multiline": True, "default": ""})
        return {"required": required, "optional": optional}

    RETURN_TYPES = ("AUDIO", "INT", "STRING")
    RETURN_NAMES = ("audio", "seed", "subtitle")
    FUNCTION = "generate"
    CATEGORY = "audio"

    def __init__(self):
        self.loader = _GLOBAL_LOADER
        self.engine = _GLOBAL_ENGINE

    def generate(self, text, reference_audio, mode, control_mode,
                 # 接收所有可能的参数
                 emo_ref_audio=None, emotion_weight=0.8, emotion_description="",
                 Happy=0.0, Angry=0.0, Sad=0.0, Fear=0.0, Hate=0.0, Love=0.0, Surprise=0.0, Neutral=0.0,
                 # 通用参数
                 do_sample_mode="off", temperature=0.8, top_p=0.9, top_k=30, num_beams=3,
                 repetition_penalty=10.0, length_penalty=0.0, max_mel_tokens=1815,
                 max_tokens_per_sentence=120, seed=0, return_subtitles=True,
                 cache_control="on"):

        # 预处理主参考音频
        ref = self._process_audio_input(reference_audio)
        
        # --- 核心逻辑分流 ---
        final_emo_ref_audio = None
        final_emo_vector = None
        final_emo_text = None
        final_emo_weight = 0.8
        use_qwen = False

        if control_mode == "Audio Reference":
            # 逻辑来自 IndexTTS2EmotionAudioNode
            if emo_ref_audio is not None:
                final_emo_ref_audio = self._process_audio_input(emo_ref_audio)
            final_emo_weight = float(emotion_weight)

        elif control_mode == "Emotion Vector":
            # 逻辑来自 IndexTTS2EmotionVectorNode (核心：归一化处理)
            vec = [Happy, Angry, Sad, Fear, Hate, Love, Surprise, Neutral]
            s = float(sum(max(0.0, float(x)) for x in vec))
            # 原作者的归一化逻辑
            final_emo_vector = ([float(max(0.0, float(x)))/s for x in vec] if s > 0 else [0.0]*7 + [1.0])
            final_emo_weight = 0.8 # 向量模式下通常不需要 weight，或者你可以复用 emotion_weight

        elif control_mode == "Text Description":
            # 逻辑来自 IndexTTS2EmotionTextNode
            raw_text = emotion_description.strip() if isinstance(emotion_description, str) else ""
            if raw_text:
                final_emo_text = raw_text
                use_qwen = True # 只有这个模式启用 Qwen
            final_emo_weight = 0.8

        # --- 调用统一引擎 ---
        out = self._do_generate(
            self.engine,
            text=text, reference_audio=ref, mode=mode,
            do_sample=(do_sample_mode == "on"), temperature=temperature, top_p=top_p, top_k=top_k, num_beams=num_beams,
            repetition_penalty=repetition_penalty, length_penalty=length_penalty,
            max_mel_tokens=max_mel_tokens, max_tokens_per_sentence=max_tokens_per_sentence,
            
            # 传入处理后的参数
            emo_text=final_emo_text,
            emo_ref_audio=final_emo_ref_audio,
            emo_vector=final_emo_vector,
            emo_weight=final_emo_weight,
            
            use_qwen=use_qwen, # 动态开关
            verbose=use_qwen,  # Qwen 模式下开启日志
            seed=seed, return_subtitles=True,
        )

        # Cache Control
        try:
            if not cache_control == "on":
                self.loader.unload_tts()
        except Exception:
            pass
        
        return out