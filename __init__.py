""" 
@title: IndexTTS for ComfyUI
@author: ComfyUI-Index-TTS
@description: ComfyUI接口的工业级零样本文本到语音合成系统
"""

import os
import sys

# 确保当前目录在导入路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)


from .index_tts2_mode_nodes import IndexTTS2UnifiedNode
from .index_tts2_pro import IndexTTS2ProNode  # 导入TTS2多角色小说朗读节点

# 注册ComfyUI节点
NODE_CLASS_MAPPINGS = {
    "IndexTTS2UnifiedNode": IndexTTS2UnifiedNode,
    "IndexTTS2ProNode": IndexTTS2ProNode,  # TTS2多角色小说朗读节点
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IndexTTS2UnifiedNode": "Index TTS 2 - Customized",  # 统一节点显示名
    "IndexTTS2ProNode": "Index TTS 2 - Multi Speaker",  # TTS2多角色小说朗读节点
}
WEB_DIRECTORY="./js"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS',"WEB_DIRECTORY"]
