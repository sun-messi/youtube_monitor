# TTS 语音生成工具

将翻译后的 Markdown 文件转换成 MP3 音频，方便当播客听。

## 安装依赖

```bash
pip install edge-tts
```

## 使用方法

```bash
# 基本使用
python tts_generator.py ../ai_output/summary/Y_Combinator/The_Truth_About_The_AI_Bubble_translate.md

# 指定语音（男声）
python tts_generator.py input.md --voice yunxi

# 指定输出文件
python tts_generator.py input.md -o podcast.mp3

# 查看可用语音
python tts_generator.py --list-voices
```

## 可用语音

### 女声
| 名称 | 语音ID | 特点 |
|------|--------|------|
| xiaoxiao | zh-CN-XiaoxiaoNeural | 温暖，适合新闻/小说（默认） |
| xiaoyi | zh-CN-XiaoyiNeural | 活泼，适合卡通/小说 |

### 男声
| 名称 | 语音ID | 特点 |
|------|--------|------|
| yunxi | zh-CN-YunxiNeural | 活泼阳光，适合播客 |
| yunyang | zh-CN-YunyangNeural | 专业可靠，新闻主播风 |
| yunjian | zh-CN-YunjianNeural | 热情，适合体育解说 |
| yunxia | zh-CN-YunxiaNeural | 可爱，适合卡通 |

## 输出

音频文件默认保存在 `outputs/` 目录下，文件名与输入文件相同（.mp3 扩展名）。

## 技术说明

- 使用 Edge TTS（微软免费 API）
- 自动提取 Markdown 中的正文内容
- 去掉表格、链接、元数据等非正文内容
- 保留章节结构作为朗读提示
