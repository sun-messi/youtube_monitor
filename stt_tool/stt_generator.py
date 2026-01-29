#!/usr/bin/env python3
"""
STT 语音转文字工具
将音频文件转换为 SRT 字幕文件

使用方法:
    python stt_generator.py input.mp3
    python stt_generator.py input.mp3 --model medium
    python stt_generator.py input.mp3 -o output.srt
"""

import argparse
import sys
from pathlib import Path

try:
    import whisper
except ImportError:
    print("请先安装 openai-whisper: pip install openai-whisper")
    sys.exit(1)


# 模型选项
MODELS = {
    "tiny":   {"desc": "最快，准确度较低，~1GB 显存", "size": "~39M"},
    "base":   {"desc": "快速，基本准确，~1GB 显存", "size": "~74M"},
    "small":  {"desc": "平衡速度和质量，~2GB 显存", "size": "~244M"},
    "medium": {"desc": "高质量，适合大多数场景，~5GB 显存", "size": "~769M"},
    "large":  {"desc": "最高质量，需要较多显存，~10GB 显存", "size": "~1550M"},
}

DEFAULT_MODEL = "medium"
DEFAULT_LANGUAGE = "en"


def format_timestamp(seconds: float) -> str:
    """
    将秒数转换为 SRT 时间戳格式

    Args:
        seconds: 秒数（浮点数）

    Returns:
        SRT 格式时间戳 HH:MM:SS,mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe_to_srt(result: dict) -> str:
    """
    将 Whisper 结果转换为 SRT 格式字符串

    Args:
        result: Whisper transcribe 返回的结果字典

    Returns:
        SRT 格式字符串
    """
    srt_lines = []
    for i, segment in enumerate(result["segments"], 1):
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")
    return "\n".join(srt_lines)


def transcribe_to_txt(result: dict) -> str:
    """
    将 Whisper 结果转换为纯文本

    Args:
        result: Whisper transcribe 返回的结果字典

    Returns:
        纯文本字符串
    """
    return result["text"].strip()


def transcribe_audio(
    audio_path: str,
    output_path: str = None,
    model_name: str = DEFAULT_MODEL,
    language: str = DEFAULT_LANGUAGE,
    output_format: str = "srt",
) -> str:
    """
    将音频文件转录为字幕文件

    Args:
        audio_path: 输入音频文件路径
        output_path: 输出路径（可选，默认在 outputs/ 目录）
        model_name: Whisper 模型名称
        language: 语言代码
        output_format: 输出格式 (srt/txt)

    Returns:
        输出文件路径
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"文件不存在: {audio_path}")

    # 加载模型
    print(f"🔄 正在加载 Whisper 模型: {model_name}")
    model = whisper.load_model(model_name)

    # 转录
    print(f"🎙️ 正在转录: {audio_path.name} (语言: {language})")
    result = model.transcribe(
        str(audio_path),
        language=language,
        verbose=False,
    )

    # 转换格式
    if output_format == "srt":
        content = transcribe_to_srt(result)
        ext = ".srt"
    else:
        content = transcribe_to_txt(result)
        ext = ".txt"

    # 确定输出路径
    if output_path is None:
        script_dir = Path(__file__).resolve().parent
        output_dir = script_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{audio_path.stem}{ext}"
    else:
        output_path = Path(output_path)

    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    segments_count = len(result.get("segments", []))
    print(f"✅ 完成: {output_path}")
    print(f"📊 共 {segments_count} 个片段")

    return str(output_path)


def list_models():
    """列出可用的 Whisper 模型"""
    print("可用的 Whisper 模型:")
    print("-" * 60)
    for name, info in MODELS.items():
        marker = " (默认)" if name == DEFAULT_MODEL else ""
        print(f"  {name:8} [{info['size']:>6}]  {info['desc']}{marker}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="将音频文件转换为 SRT 字幕文件（语音转文字）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stt_generator.py input.mp3
  python stt_generator.py input.mp3 --model medium
  python stt_generator.py input.mp3 --language zh
  python stt_generator.py input.mp3 -o subtitle.srt
  python stt_generator.py input.mp3 --format txt
  python stt_generator.py --list-models
        """,
    )
    parser.add_argument("input", nargs="?", help="输入的音频文件路径 (mp3/wav/m4a/...)")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument(
        "-m", "--model",
        default=DEFAULT_MODEL,
        help=f"Whisper 模型 (tiny/base/small/medium/large)，默认 {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "-l", "--language",
        default=DEFAULT_LANGUAGE,
        help=f"音频语言代码，默认 {DEFAULT_LANGUAGE}",
    )
    parser.add_argument(
        "-f", "--format",
        default="srt",
        choices=["srt", "txt"],
        help="输出格式，默认 srt",
    )
    parser.add_argument("--list-models", action="store_true", help="列出可用模型")

    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    if not args.input:
        parser.print_help()
        return

    try:
        transcribe_audio(
            args.input,
            args.output,
            model_name=args.model,
            language=args.language,
            output_format=args.format,
        )
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
