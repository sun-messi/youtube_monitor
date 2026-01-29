#!/usr/bin/env python3
"""
STT Pipeline - 音频/字幕文件翻译工具
将音频或 SRT 字幕文件通过翻译 pipeline 生成中文翻译

使用方法:
    python stt_pipeline.py input.mp3 --title "Video Title" --channel "Channel"
    python stt_pipeline.py input.srt --title "Video Title" --channel "Channel"
    python stt_pipeline.py input.mp3 --title "Video Title" --channel "Channel" --whisper-model large
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.webm', '.mp4'}


def transcribe_audio(audio_path: str, model_name: str = "medium", language: str = "en") -> str:
    """
    用 Whisper 将音频转录为 SRT 文件

    Args:
        audio_path: 音频文件路径
        model_name: Whisper 模型名称
        language: 音频语言

    Returns:
        生成的 SRT 文件路径
    """
    try:
        import whisper
    except ImportError:
        print("请先安装 openai-whisper: pip install openai-whisper")
        sys.exit(1)

    audio_path = Path(audio_path)
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    srt_path = output_dir / f"{audio_path.stem}.srt"

    logger.info(f"加载 Whisper 模型: {model_name}")
    model = whisper.load_model(model_name)

    logger.info(f"转录中: {audio_path.name} (语言: {language})")
    result = model.transcribe(str(audio_path), language=language, verbose=False)

    # 生成 SRT
    srt_lines = []
    for i, segment in enumerate(result["segments"], 1):
        start = _format_srt_timestamp(segment["start"])
        end = _format_srt_timestamp(segment["end"])
        text = segment["text"].strip()
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")

    srt_content = "\n".join(srt_lines)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    logger.info(f"转录完成: {srt_path} ({len(result['segments'])} 个片段)")
    return str(srt_path)


def run_translate_pipeline(
    srt_path: str,
    title: str,
    channel: str,
    video_url: str = "",
    upload_date: str = "",
) -> str:
    """
    调用现有翻译 pipeline (stages 3-7) 处理 SRT 文件

    Args:
        srt_path: SRT 字幕文件路径
        title: 视频/音频标题
        channel: 频道名称
        video_url: 原始链接（可选）
        upload_date: 发布日期 YYYYMMDD（可选）

    Returns:
        输出 Markdown 文件路径
    """
    from core.subtitle_processor import process_subtitle_file
    from core.ai_analyzer import analyze_video, parse_chapters_from_summary, detect_video_type, extract_speakers
    from core.translator import translate_chapters
    from core.output_generator import generate_markdown, save_output
    from utils.srt_parser import parse_srt
    from main import load_config

    config = load_config()
    prompts_dir = PROJECT_ROOT / "prompts"
    prompt_summary = prompts_dir / "yt-summary.md"
    prompt_translate = prompts_dir / "yt-translate.md"

    if not upload_date:
        upload_date = datetime.now().strftime("%Y%m%d")

    # 读取 raw SRT
    with open(srt_path, 'r', encoding='utf-8') as f:
        raw_srt = f.read()

    srt_entries = parse_srt(raw_srt)

    # Stage 3: 字幕处理
    logger.info("Stage 3: 处理字幕...")
    subtitle_data = process_subtitle_file(
        srt_path,
        title=title,
        channel=channel,
        video_url=video_url,
        merge_interval=config.subtitle_merge_interval
    )

    if not subtitle_data:
        raise RuntimeError("字幕处理失败")

    # 保存 clean 字幕
    output_dir = Path(config.output_dir)
    from core.output_generator import sanitize_filename
    clean_dir = output_dir / "clean" / sanitize_filename(channel)
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_file = clean_dir / f"{sanitize_filename(title)}.txt"
    with open(clean_file, "w", encoding="utf-8") as f:
        f.write(subtitle_data.with_metadata)

    logger.info(f"Stage 3 完成: {len(srt_entries)} 条字幕")

    # Stage 4: AI 分析
    logger.info("Stage 4: AI 分析...")
    model_summary = getattr(config, 'claude_model_summary', None) or getattr(config, 'claude_model', 'claude-opus-4-20250514')
    model_translate = getattr(config, 'claude_model_translate', None) or getattr(config, 'claude_model', 'claude-sonnet-4-20250514')

    analysis_result = analyze_video(
        subtitle_text=subtitle_data.with_metadata,
        prompt_file=prompt_summary,
        timeout=config.claude_timeout_seconds,
        model=model_summary,
        use_agent=False
    )

    if not analysis_result:
        raise RuntimeError("AI 分析失败")

    summary = analysis_result.raw_markdown
    chapters = parse_chapters_from_summary(summary)
    video_type = detect_video_type(summary)
    speakers = extract_speakers(summary)

    if not chapters:
        logger.warning("未找到章节，使用 fallback")
        from core.subtitle_processor import get_duration_from_entries
        duration_sec = get_duration_from_entries(srt_entries)
        interval = getattr(config, 'fallback_chapter_interval', 300)
        chapters = [(i, f"Part {i // interval + 1}") for i in range(0, duration_sec, interval)] or [(0, "完整内容")]

    logger.info(f"Stage 4 完成: {len(chapters)} 个章节, 类型: {video_type}")

    # Stage 5: 翻译
    logger.info(f"Stage 5: 翻译 {len(chapters)} 个章节...")
    translations, failed_chapters = translate_chapters(
        summary=summary,
        chapters=chapters,
        raw_srt=raw_srt,
        video_type=video_type,
        speakers=speakers,
        prompt_file=prompt_translate,
        timeout=config.claude_timeout_seconds,
        model=model_translate,
        context_lines=config.context_lines,
        max_retries=config.translation_max_retries,
        retry_delay=config.translation_retry_delay,
        use_agent=False
    )

    logger.info(f"Stage 5 完成: {len(translations)}/{len(chapters)} 章节翻译成功")

    # Stage 6: 生成 Markdown
    logger.info("Stage 6: 生成 Markdown...")
    from core.subtitle_processor import get_duration_from_entries
    duration_sec = get_duration_from_entries(srt_entries)

    markdown_content = generate_markdown(
        title=title,
        channel=channel,
        upload_date=upload_date,
        video_url=video_url,
        duration_sec=duration_sec,
        summary=summary,
        translations=translations,
        failed_chapters=failed_chapters
    )

    # Stage 7: 保存
    logger.info("Stage 7: 保存输出...")
    output_path = save_output(
        markdown_content,
        title=title,
        channel=channel,
        output_dir=config.output_dir,
        filename_max_length=config.filename_max_length
    )

    logger.info(f"完成! 输出: {output_path}")
    return output_path


def _format_srt_timestamp(seconds: float) -> str:
    """秒数 → SRT 时间戳"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main():
    parser = argparse.ArgumentParser(
        description="音频/字幕文件 → 中文翻译 (STT + Translation Pipeline)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 音频文件（自动 Whisper 转录 + 翻译）
  python stt_pipeline.py audio.mp3 --title "Tempus AI" --channel "JPMorgan Healthcare"

  # SRT 字幕文件（直接翻译）
  python stt_pipeline.py subtitle.srt --title "Tempus AI" --channel "JPMorgan Healthcare"

  # 指定 Whisper 模型和语言
  python stt_pipeline.py audio.mp3 --title "Title" --channel "Channel" --whisper-model large --language en

  # 提供原始链接
  python stt_pipeline.py audio.mp3 --title "Title" --channel "Channel" --url "https://example.com/video"
        """
    )
    parser.add_argument("input", help="输入文件路径 (mp3/wav/srt/...)")
    parser.add_argument("--title", required=True, help="视频/音频标题")
    parser.add_argument("--channel", required=True, help="频道名称")
    parser.add_argument("--url", default="", help="原始链接（可选）")
    parser.add_argument("--date", default="", help="发布日期 YYYYMMDD（可选，默认今天）")
    parser.add_argument(
        "--whisper-model", default="medium",
        help="Whisper 模型 (tiny/base/small/medium/large)，默认 medium"
    )
    parser.add_argument(
        "--language", default="en",
        help="音频语言，默认 en"
    )
    parser.add_argument(
        "--transcribe-only", action="store_true",
        help="只做语音转录，不翻译"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    try:
        # 判断输入类型
        if input_path.suffix.lower() in AUDIO_EXTENSIONS:
            # 音频文件 → 先转录
            print(f"🎙️ 检测到音频文件，先用 Whisper 转录...")
            srt_path = transcribe_audio(str(input_path), args.whisper_model, args.language)

            if args.transcribe_only:
                print(f"✅ 转录完成: {srt_path}")
                return
        elif input_path.suffix.lower() == '.srt':
            srt_path = str(input_path)
        else:
            print(f"不支持的文件格式: {input_path.suffix}")
            sys.exit(1)

        # 运行翻译 pipeline
        print(f"🔄 开始翻译 pipeline...")
        output_path = run_translate_pipeline(
            srt_path=srt_path,
            title=args.title,
            channel=args.channel,
            video_url=args.url,
            upload_date=args.date,
        )

        print(f"✅ 完成! 输出: {output_path}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        logger.exception("Pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
