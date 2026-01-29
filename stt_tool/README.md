# STT 语音转文字工具

将音频文件转换为 SRT 字幕文件，使用 OpenAI Whisper 模型。

## 安装依赖

```bash
pip install openai-whisper
```

## 使用方法

```bash
# 基本使用（默认 medium 模型）
python stt_generator.py input.mp3

# 指定模型
python stt_generator.py input.mp3 --model small

# 指定语言（中文）
python stt_generator.py input.mp3 --language zh

# 输出纯文本（而非 SRT）
python stt_generator.py input.mp3 --format txt

# 指定输出文件
python stt_generator.py input.mp3 -o subtitle.srt

# 查看可用模型
python stt_generator.py --list-models
```

## 可用模型

| 名称 | 大小 | 显存需求 | 特点 |
|------|------|---------|------|
| tiny | ~39M | ~1GB | 最快，准确度较低 |
| base | ~74M | ~1GB | 快速，基本准确 |
| small | ~244M | ~2GB | 平衡速度和质量 |
| medium | ~769M | ~5GB | 高质量，适合大多数场景（默认） |
| large | ~1550M | ~10GB | 最高质量 |

## 输出

字幕文件默认保存在 `outputs/` 目录下，文件名与输入文件相同（.srt 扩展名）。

## 技术说明

- 使用 OpenAI Whisper（开源免费）
- 支持 GPU 加速（CUDA）
- 支持多种音频格式（mp3/wav/m4a/flac/...）
- 输出标准 SRT 字幕格式或纯文本
