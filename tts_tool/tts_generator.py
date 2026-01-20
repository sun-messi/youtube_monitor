#!/usr/bin/env python3
"""
TTS 语音生成工具
将翻译后的 Markdown 文件转换成 MP3 音频

使用方法:
    python tts_generator.py input.md
    python tts_generator.py input.md --voice zh-CN-YunxiNeural
    python tts_generator.py input.md -o output.mp3
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("请先安装 edge-tts: pip install edge-tts")
    sys.exit(1)


# 中文语音选项
VOICES = {
    # 女声
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # 温暖，适合新闻/小说
    "xiaoyi": "zh-CN-XiaoyiNeural",      # 活泼，适合卡通/小说
    # 男声
    "yunxi": "zh-CN-YunxiNeural",        # 活泼阳光，适合播客
    "yunyang": "zh-CN-YunyangNeural",    # 专业可靠，新闻主播风
    "yunjian": "zh-CN-YunjianNeural",    # 热情，适合体育解说
    "yunxia": "zh-CN-YunxiaNeural",      # 可爱，适合卡通
}

DEFAULT_VOICE = "zh-CN-YunjianNeural"  # 云健-热情男声


def extract_text_from_markdown(md_path: str) -> str:
    """
    从 Markdown 文件提取纯文本，适合 TTS 朗读

    处理：
    - 去掉 Markdown 格式标记
    - 保留章节结构
    - 去掉表格、链接等
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    result = []
    in_table = False
    skip_sections = {'📹 视频信息', '📑 章节导航表', '🏢 提及的公司', '📺 视频类型判断'}
    current_section = ""
    skip_current = False

    for line in lines:
        stripped = line.strip()

        # 检测章节标题
        if stripped.startswith('## '):
            section_title = stripped[3:].strip()
            current_section = section_title
            skip_current = any(skip in section_title for skip in skip_sections)
            if not skip_current:
                # 添加章节标题作为朗读提示
                result.append(f"\n{section_title}\n")
            continue

        if skip_current:
            continue

        # 跳过表格
        if '|' in stripped and stripped.startswith('|'):
            in_table = True
            continue
        if in_table and not stripped:
            in_table = False
            continue
        if in_table:
            continue

        # 跳过空行和分隔线
        if not stripped or stripped == '---':
            if result and result[-1] != '\n':
                result.append('\n')
            continue

        # 跳过图片和链接行
        if stripped.startswith('![') or stripped.startswith('- **原始链接**'):
            continue

        # 跳过元数据行
        if stripped.startswith('- **') and '**:' in stripped:
            continue

        # 跳过生成时间
        if stripped.startswith('*生成时间'):
            continue

        # 处理标题
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            result.append(f"标题：{title}\n\n")
            continue

        if stripped.startswith('### '):
            subtitle = stripped[4:].strip()
            # 处理章节时间戳格式 (0:00 - 5:00) Title
            subtitle = re.sub(r'\([\d:]+\s*-\s*[\d:]+\)\s*', '', subtitle)
            result.append(f"\n{subtitle}\n")
            continue

        # 处理引用块
        if stripped.startswith('> '):
            quote = stripped[2:].strip()
            result.append(f"引用：{quote}\n")
            continue

        # 处理列表项
        if stripped.startswith('- ') or stripped.startswith('* '):
            item = stripped[2:].strip()
            # 去掉加粗标记
            item = re.sub(r'\*\*([^*]+)\*\*', r'\1', item)
            result.append(f"{item}\n")
            continue

        # 处理普通段落
        # 去掉 Markdown 格式
        text = stripped
        # 去掉时间戳标记 **(0:00 - 1:15)** 格式
        text = re.sub(r'\*\*\([\d:]+\s*-\s*[\d:]+\)\*\*', '', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # 加粗
        text = re.sub(r'\*([^*]+)\*', r'\1', text)       # 斜体
        text = re.sub(r'`([^`]+)`', r'\1', text)         # 代码
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 链接

        if text:
            result.append(f"{text}\n")

    # 合并结果，去掉多余空行
    final_text = ''.join(result)
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)

    return final_text.strip()


async def generate_audio(text: str, output_path: str, voice: str = DEFAULT_VOICE):
    """
    使用 Edge TTS 生成音频

    Args:
        text: 要朗读的文本
        output_path: 输出 MP3 文件路径
        voice: 语音名称
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def process_translation_to_audio(
    md_path: str,
    output_path: str = None,
    voice: str = DEFAULT_VOICE
) -> str:
    """
    将翻译文件转换为音频

    Args:
        md_path: Markdown 文件路径
        output_path: 输出路径（可选，默认在 outputs/ 目录）
        voice: 语音名称

    Returns:
        输出文件路径
    """
    md_path = Path(md_path)

    if not md_path.exists():
        raise FileNotFoundError(f"文件不存在: {md_path}")

    # 提取文本
    print(f"📖 正在提取文本: {md_path.name}")
    text = extract_text_from_markdown(str(md_path))

    if not text:
        raise ValueError("提取的文本为空")

    print(f"📝 文本长度: {len(text)} 字符")

    # 确定输出路径
    if output_path is None:
        # 使用脚本所在目录的 outputs 子目录
        script_dir = Path(__file__).resolve().parent
        output_dir = script_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{md_path.stem}.mp3"
    else:
        output_path = Path(output_path)

    # 生成音频
    print(f"🎙️ 正在生成音频 (语音: {voice})...")
    asyncio.run(generate_audio(text, str(output_path), voice))

    print(f"✅ 完成: {output_path}")
    return str(output_path)


def list_voices():
    """列出可用的中文语音"""
    print("可用的中文语音:")
    print("-" * 40)
    for name, voice_id in VOICES.items():
        print(f"  {name:12} -> {voice_id}")
    print("-" * 40)
    print(f"默认语音: {DEFAULT_VOICE}")


def main():
    parser = argparse.ArgumentParser(
        description="将翻译后的 Markdown 文件转换成 MP3 音频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tts_generator.py input.md
  python tts_generator.py input.md --voice yunxi
  python tts_generator.py input.md -o podcast.mp3
  python tts_generator.py --list-voices
        """
    )
    parser.add_argument("input", nargs="?", help="输入的 Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出的 MP3 文件路径")
    parser.add_argument(
        "-v", "--voice",
        default="yunjian",
        help="语音名称 (xiaoxiao/yunxi/xiaoyi/yunjian 或完整语音ID)，默认 yunjian"
    )
    parser.add_argument("--list-voices", action="store_true", help="列出可用语音")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if not args.input:
        parser.print_help()
        return

    # 解析语音
    voice = VOICES.get(args.voice, args.voice)

    try:
        process_translation_to_audio(args.input, args.output, voice)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
