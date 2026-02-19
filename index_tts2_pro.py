"""
IndexTTS2 Pro Node - 多角色小说朗读节点
支持 IndexTTS-2 模型的多角色语音合成
"""

import json
import re
import numpy as np
import torch
from typing import Any, Tuple, Optional, List, Dict

from .indextts2 import IndexTTS2Loader, IndexTTS2Engine


class IndexTTS2ProNode:
    """
    ComfyUI的IndexTTS2 Pro节点，专用于小说阅读，支持多角色语音合成
    使用 IndexTTS-2 模型
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "structured_text": ("STRING", {"multiline": True, "default": "<Narrator>这是一段旁白文本。<Character1>你好，我是角色1。<Narrator>他说道。"}),
                "character0_audio": ("AUDIO", {"description": "正文/旁白的参考音频"}),
                "mode": (["Auto", "Duration", "Tokens"], {"default": "Auto"}),
            },
            "optional": {
                "character1_audio": ("AUDIO", {"description": "角色1的参考音频"}),
                "character2_audio": ("AUDIO", {"description": "角色2的参考音频"}),
                "character3_audio": ("AUDIO", {"description": "角色3的参考音频"}),
                "character4_audio": ("AUDIO", {"description": "角色4的参考音频"}),
                "character5_audio": ("AUDIO", {"description": "角色5的参考音频"}),
                # 高级生成参数
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
                # 缓存控制
                "cache_control": (["off","on"], {"default": "off"}),
                "export_subtitle":(["None",".srt"],{"default":"None"})
            }
        }
    
    RETURN_TYPES = ("AUDIO", "INT", "STRING")
    RETURN_NAMES = ("audio", "seed","subtitle")
    FUNCTION = "generate_multi_voice_speech"
    CATEGORY = "audio"
    
    def __init__(self):
        self.loader = IndexTTS2Loader()
        self.engine = IndexTTS2Engine(self.loader)
        print(f"[IndexTTS2 Pro] 初始化节点")
    
    @staticmethod
    def _process_audio_input(audio: Any) -> Optional[Tuple[np.ndarray, int]]:
        """处理ComfyUI的音频格式"""
        if audio is None:
            return None
            
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
    
    def _parse_structured_text(self,text: str):
        segments = []
        pattern = re.compile(r'(\[[^\]]+\]|\([^\)]+\)|\{[^\}]+\})')
        parts = pattern.split(text)
        curr_role = "Character0"
        curr_emo = "Neutral"
        emotions={}
        for i in range(len(parts)):
            part = parts[i]
            part = part.strip()
            if not part: continue
            if part.startswith('['): # 切换角色
                curr_role = part[1:-1]
                if curr_role not in list(emotions.keys()):
                    emotions[part[1:-1]]="Neutral"
            elif part.startswith('('): # 更改的是curr_role这个角色的情感
                curr_emo = part[1:-1]
                emotions[curr_role]=curr_emo
                
            elif part.startswith('{'): # 插入停顿
                try:
                    duration = float(part[1:-2]) # 提取 "1.2"
                    segments.append({"type": "pause", "duration": duration})
                except: pass
            else: # 普通文本
                segments.append({
                    "type": "speech",
                    "role": curr_role,
                    "emotion": emotions[curr_role],
                    "text": part
                })
        return segments
    def _sec_to_time(self, sec):
        """将秒数转换为标准的 SRT 时间格式: HH:MM:SS,mmm"""
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int(round(sec % 1, 3) * 1000)
        # 使用 f-string 自动补零，比手动 rjust 更高效
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def generate_multi_voice_speech(
        self,
        structured_text: str,
        character0_audio,
        mode: str = "Auto",
        character1_audio=None,
        character2_audio=None,
        character3_audio=None,
        character4_audio=None,
        character5_audio=None,
        do_sample_mode: str = "on",
        temperature: float = 0.8,
        top_p: float = 0.9,
        top_k: int = 30,
        num_beams: int = 3,
        repetition_penalty: float = 10.0,
        length_penalty: float = 0.0,
        max_mel_tokens: int = 1815,
        max_tokens_per_sentence: int = 120,
        seed: int = 0,
        cache_control=None,
        export_subtitle="None"
    ):
        """
        生成多角色语音的主函数
        """
        try:
            print(f"[IndexTTS2 Pro] 开始多角色语音生成...")
            parsed_segments = self._parse_structured_text(structured_text)
            character_audios = {}
            for i, char_audio in enumerate([character0_audio,character1_audio,character2_audio,character3_audio,character4_audio,character5_audio], 0):
                if char_audio is not None:
                    character_audios[f"Character{i}"] = self._process_audio_input(char_audio)
            generated_subtitle=""
            # 生成音频片段
            audio_segments = []
            current_time=0.0
            print(parsed_segments)
            subtitle_count=1
            for part in parsed_segments:
                sr=44100
                if part["type"]=="speech":
                    # 选择参考音频
                    if not(part["role"] in list(character_audios.keys())):
                        print(part["role"] , list(character_audios.keys()))
                        raise ValueError("缺失语音，已暂停推理")
                    
                    try:
                        sr, wave, _ = self.engine.generate(
                            text=part["text"],
                            reference_audio=character_audios[part["role"]],
                            mode=mode,
                            do_sample=(do_sample_mode == "on"),
                            temperature=temperature,
                            top_p=top_p,
                            top_k=top_k,
                            num_beams=num_beams,
                            repetition_penalty=repetition_penalty,
                            length_penalty=length_penalty,
                            max_mel_tokens=max_mel_tokens,
                            max_tokens_per_sentence=max_tokens_per_sentence,
                            emo_text=part["emotion"],
                            seed=seed,
                            return_subtitles=False,
                        )
                        #先写入字幕
                        #格式：hour:minute:second,millisecond --> hour:minute:second,millisecond
                        '''
                        字幕序号
                        字幕显示的起始时间
                        字幕内容（可多行）
                        空白行（表示本字幕段的结束）
                        '''
                        audio_length = len(wave) / sr
                        if export_subtitle != "None":
                            generated_subtitle+="{}\n{} --> {}\n{}\n\n".format(subtitle_count,self._sec_to_time(current_time),self._sec_to_time(current_time+audio_length),part["text"])
                        current_time +=audio_length
                        subtitle_count+=1
                        audio_segments.append((wave, sr))
                        print(f"[IndexTTS2 Pro] 生成音频: {audio_length:.2f}秒")

                    except Exception as e:
                        print(f"[IndexTTS2 Pro] 生成 {part["role"]} 语音失败: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                else:
                    duration = part["duration"]
                    silence_wave = np.zeros(int(duration * sr), dtype=np.float32)
                    audio_segments.append((silence_wave, sr))
                    current_time += duration
            
            if not audio_segments:
                raise ValueError("没有成功生成任何音频段落")
            
            # 连接所有音频片段
            sample_rate = audio_segments[0][1]
            all_waves = [seg[0] for seg in audio_segments]
            concatenated = np.concatenate(all_waves, axis=0)
            
            total_duration = len(concatenated) / sample_rate
            print(f"[IndexTTS2 Pro] 多角色语音生成完成，总长度: {total_duration:.2f}秒")
            
            # 转换为 ComfyUI 格式
            wave_tensor = torch.tensor(concatenated, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
            audio_output = {"waveform": wave_tensor, "sample_rate": int(sample_rate)}
            # 处理缓存控制
            try:
                keep = bool(cache_control.get("keep_cached")) if isinstance(cache_control, dict) else False
                if not keep:
                    self.loader.unload_tts()
            except Exception:
                pass
            
            return (audio_output, seed, generated_subtitle)
            
        except Exception as e:
            import traceback
            print(f"[IndexTTS2 Pro] 生成失败: {e}")
            print(traceback.format_exc())
            raise RuntimeError(f"多角色语音生成失败: {e}")