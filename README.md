# ComfyUI IndexTTS 2

> 本项目基于B站开源项目进行二次开发，仅用于开源社区内的交流与学习，严禁用于任何非法目的以及与侵犯版权相关的任何行为。

## 免责声明

本项目所有个人使用行为与开发者本人及本项目本身均无任何关联。开发者对于项目使用者的行为不承担任何责任，使用者应自行承担使用过程中可能产生的所有风险和法律责任。请广大使用者在遵守法律法规及相关规定的前提下，合理、合法地使用本项目，维护开源社区的良好秩序与健康发展。

感谢您的理解与支持！

---

## 📌 项目简介

本插件是 [ComfyUI-Index-TTS](https://github.com/chenpipi0807/ComfyUI-Index-TTS) 的二次开发版本，主要改进如下：

- **全面拥抱新地**：移除旧版 IndexTTS 支持，让节点不在臃肿。
- **节点合并优化**：将三种情感控制方式合并为一个节点，同时移除多余的 cache control 节点，让工作流画布更加简洁清爽。
- **保留核心功能**：保留所有常用核心功能，满足日常语音合成需求。
- **全新多人节点**：新节点**Index TTS 2 - Analyze Emotion**加入，完美的情感一键复刻。

---

## 📌 新成员加入

隆重介绍全新的**Index TTS 2 - Multi Speaker**多人合成节点：

- **更丰富的情感变化**：所有角色都能动态调整感情，所有感情独立保留，没头脑和不高兴也能一起搭一台戏
- **更简单的结构台本**：GPT-3.5也能秒懂的LLM_Prompt，马上导入马上复制
- **更戏剧的暂停符号**：灵活插入{xs}静默，有时候留白也是一种美
- **更便捷的字幕生成**：自动生成可复制使用的.srt字幕格式

---

## 🔧 安装与使用

1. **这一步很重要！！！** 先启动你的ComfyUI，在右下角找到**控制台**，点击后切换到**终端**
2. 使用git指令下载该项目：
   ```bash
   cd custom_nodes
   git clone https://github.com/qwq20002/ComfyUI-IndexTTS-2-Nodes
   ```

3. 安装所需依赖：
   ```bash
   cd ComfyUI-IndexTTS-2-Nodes
   pip install -r requirements.txt
   ```

4. 使用这串命令自动下载所需的模型文件：
   ```bash
   python downloadModels.py
   ```

5. 重新启动ComfyUI，现在你应该能看到节点库里有ComfyUI-IndexTTS-2-Nodes了，开始使用吧！

---

## 🙏 鸣谢

- 感谢 [IndexTTS 原项目](https://github.com/index-tts/index-tts) 提供的强大技术基础。
- 感谢原作者 [chenpipi0817](https://github.com/chenpipi0807) 的原始实现。
- 感谢@SilverRachel指出说明文档里的错误
- 感谢 ComfyUI 社区的持续支持与鼓励。
- 感谢您的使用与反馈！
- 特别鸣谢 **Gemini Pro** 的“巨大”支持（逃 😜）

---

## 📄 许可证

本项目的许可证请参考原始 IndexTTS 项目的许可证。使用时请遵守相应条款。

---

> 如有任何问题或建议，欢迎提交 Issue 或 Pull Request。让我们一起让社区变得更好！
