# ComfyUI IndexTTS 2

> 本项目基于B站开源项目进行二次开发，仅用于开源社区内的交流与学习，严禁用于任何非法目的以及与侵犯版权相关的任何行为。

## 免责声明

本项目所有个人使用行为与开发者本人及本项目本身均无任何关联。开发者对于项目使用者的行为不承担任何责任，使用者应自行承担使用过程中可能产生的所有风险和法律责任。请广大使用者在遵守法律法规及相关规定的前提下，合理、合法地使用本项目，维护开源社区的良好秩序与健康发展。

感谢您的理解与支持！

---

## 📌 项目简介

本插件是 [ComfyUI-Index-TTS](https://github.com/chenpipi0807/ComfyUI-Index-TTS) 的二次开发版本，主要改进如下：

- **全面拥抱 IndexTTS 2**：移除旧版 IndexTTS 支持，专注于更大、更好、更强的 IndexTTS 2。
- **节点合并优化**：将三种情感控制方式合并为一个节点，同时移除多余的 cache control 节点，让工作流画布更加简洁清爽。
- **保留核心功能**：保留所有常用核心功能，满足日常语音合成需求。

---


## 🔧 安装与使用

1. **下载插件**  
   将本仓库的 ZIP 文件解压到 ComfyUI 的 `custom_nodes` 目录下。

2. **安装依赖**  
   在 ComfyUI 的虚拟环境中安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. **下载模型**  
   在虚拟环境中运行模型下载脚本：
   ```bash
   python downloadModels.py
   ```

4. **启动 ComfyUI**  
   正常启动 ComfyUI，即可在节点列表中看到新的 IndexTTS 2 节点，开始使用！

---

## 🙏 鸣谢

- 感谢 [IndexTTS 原项目](https://github.com/index-tts/index-tts) 提供的强大技术基础。
- 感谢原作者 [chenpipi0817](https://github.com/chenpipi0807) 的原始实现。
- 感谢 ComfyUI 社区的持续支持与鼓励。
- 感谢您的使用与反馈！
- 特别鸣谢 **Gemini Pro** 的“巨大”支持（逃 😜）

---

## 📄 许可证

本项目的许可证请参考原始 IndexTTS 项目的许可证。使用时请遵守相应条款。

---

> 如有任何问题或建议，欢迎提交 Issue 或 Pull Request。让我们一起让社区变得更好！
