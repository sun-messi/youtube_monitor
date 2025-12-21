"""
Output Generator Module.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py

Generates Markdown documents from video analysis and translation results.
"""

from typing import List, Optional, Tuple
from datetime import datetime
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """
    Clean filename, remove illegal characters including Unicode quotes.

    Args:
        title: Original title
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove ASCII and Unicode problematic characters (including smart quotes)
    title = re.sub(r'[<>:"/\\|?*""''`'']', '', title)
    title = title.replace(' ', '_')
    if len(title) > max_length:
        title = title[:max_length]
    return title or "video"


def format_duration(seconds: int) -> str:
    """
    Format seconds to readable duration string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration (e.g., "1:23:45" or "23:45")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def generate_markdown(
    title: str,
    channel: str,
    upload_date: str,
    video_url: str,
    duration_sec: int,
    summary: str,
    translations: List[str],
    failed_chapters: Optional[List[dict]] = None,
    ai_provider: str = "claude"
) -> str:
    """
    Generate complete markdown document.

    Args:
        title: Video title
        channel: Channel name
        upload_date: Upload date (YYYYMMDD format)
        video_url: Original YouTube URL
        duration_sec: Video duration in seconds
        summary: AI generated summary markdown
        translations: List of translated chapter markdown strings
        failed_chapters: List of failed chapter dicts with index, title, error

    Returns:
        Complete markdown document
    """
    lines = []

    # Header
    lines.append(f"# {title}")
    lines.append("")

    # Metadata section
    lines.append("## 📹 视频信息")
    lines.append("")
    lines.append(f"- **频道**: {channel}")

    # Format upload date
    if upload_date and len(upload_date) == 8:
        formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    else:
        formatted_date = upload_date or "未知"

    lines.append(f"- **发布日期**: {formatted_date}")
    lines.append(f"- **时长**: {format_duration(duration_sec)}")
    lines.append(f"- **原始链接**: [{video_url}]({video_url})")
    lines.append("")

    # Summary section (AI generated)
    lines.append("---")
    lines.append("")
    lines.append(summary)
    lines.append("")

    # Translation section
    lines.append("---")
    lines.append("")
    lines.append("## 📝 完整翻译")
    lines.append("")

    if translations:
        for translation in translations:
            lines.append(translation)
            lines.append("")
    else:
        lines.append("⚠️ 没有可用的翻译内容。")
        lines.append("")

    # Processing log
    if failed_chapters:
        lines.append("---")
        lines.append("")
        lines.append("## ⚠️ 处理日志")
        lines.append("")
        lines.append(f"- 失败章节数: {len(failed_chapters)}")
        lines.append("")
        for fc in failed_chapters:
            lines.append(f"  - 章节 {fc.get('index', '?')}: {fc.get('title', '未知')} - {fc.get('error', '未知错误')}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    provider_label = "Claude CLI" if ai_provider == "claude" else "OpenAI CLI"
    lines.append(f"*由 YouTube Monitor & Translator ({provider_label}) 生成*")

    return "\n".join(lines)


def save_output(
    markdown_content: str,
    title: str,
    channel: str,
    output_dir: str,
    filename_max_length: int = 50
) -> str:
    """
    Save markdown content to file.

    Args:
        markdown_content: Complete markdown content
        title: Video title (for filename)
        channel: Channel name (for directory)
        output_dir: Base output directory
        filename_max_length: Max length for filename

    Returns:
        Path to saved file
    """
    # Create output directory structure
    output_path = Path(output_dir) / "summary" / sanitize_filename(channel)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_title = sanitize_filename(title, filename_max_length)
    filename = f"{safe_title}_translate.md"
    file_path = output_path / filename

    # Handle filename conflicts
    if file_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}_translate.md"
        file_path = output_path / filename

    # Write file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(f"Output saved to: {file_path}")
    return str(file_path)


def combine_summary_and_translation(
    summary: str,
    translations: List[str],
    title: str,
    channel: str,
    upload_date: str,
    video_url: str,
    duration_sec: int,
    failed_chapters: Optional[List[dict]] = None,
    ai_provider: str = "claude"
) -> str:
    """
    Combine summary and translations into a single markdown document.

    This is a convenience wrapper around generate_markdown.

    Args:
        summary: AI generated summary markdown
        translations: List of chapter translation strings
        title: Video title
        channel: Channel name
        upload_date: Upload date (YYYYMMDD)
        video_url: YouTube URL
        duration_sec: Video duration
        failed_chapters: Failed chapter info

    Returns:
        Complete markdown document
    """
    return generate_markdown(
        title=title,
        channel=channel,
        upload_date=upload_date,
        video_url=video_url,
        duration_sec=duration_sec,
        summary=summary,
        translations=translations,
        failed_chapters=failed_chapters,
        ai_provider=ai_provider
    )


def validate_output(markdown_content: str) -> Tuple[bool, List[str]]:
    """
    Validate generated markdown content.

    Args:
        markdown_content: Markdown content to validate

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    if not markdown_content or not markdown_content.strip():
        issues.append("Markdown content is empty")
        return False, issues

    # Check for title
    if not re.search(r"^# ", markdown_content, re.MULTILINE):
        issues.append("Missing main title (# header)")

    # Check for summary section
    if "摘要" not in markdown_content and "TL;DR" not in markdown_content:
        issues.append("Missing summary section")

    # Check for translation section
    if "翻译" not in markdown_content and "Translation" not in markdown_content:
        issues.append("Missing translation section")

    is_valid = len(issues) == 0

    if not is_valid:
        logger.warning(f"Output validation issues: {issues}")

    return is_valid, issues


def get_word_count(text: str) -> int:
    """
    Get word count for text (supports Chinese and English).

    Args:
        text: Text to count

    Returns:
        Word/character count
    """
    # For Chinese, count characters; for English, count words
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + english_words


def extract_summary_section(markdown_content: str) -> str:
    """
    Extract just the summary section from full markdown.

    Args:
        markdown_content: Full markdown document

    Returns:
        Summary section text
    """
    # Try to find TL;DR or Summary section
    patterns = [
        r'### .*?TL;DR.*?\n(.*?)(?=###|\n---|\Z)',
        r'## .*?摘要.*?\n(.*?)(?=##|\n---|\Z)',
        r'## .*?Summary.*?\n(.*?)(?=##|\n---|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""
