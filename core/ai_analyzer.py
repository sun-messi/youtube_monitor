"""
AI video analysis using AI CLI.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py
"""

import logging
import os
import re
import tempfile
from typing import Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from core.ai_client import run_ai_prompt

logger = logging.getLogger(__name__)


@dataclass
class ChapterInfo:
    """Video chapter information."""
    start_sec: int
    title: str


@dataclass
class AnalysisResult:
    """AI analysis result."""
    summary: str
    chapters: List[Tuple[int, str]]  # (start_sec, title)
    video_type: str  # 'interview', 'speech', 'other'
    speakers: str
    key_points: List[str]
    raw_markdown: str  # Raw markdown output from Claude


def call_claude_with_prompt(
    prompt_file: Path,
    input_content: str,
    timeout: int = 300,
    model: str = None,
    config: Any = None
) -> str:
    """
    Call AI CLI with a local prompt file.

    Args:
        prompt_file: Path to prompt file (e.g., PROMPT_SUMMARY)
        input_content: Content to append to the prompt
        timeout: Timeout in seconds
        model: Claude model to use

    Returns:
        Claude's output text
    """
    # Read prompt template
    if not prompt_file.exists():
        logger.error(f"Prompt file not found: {prompt_file}")
        return ""

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Replace $ARGUMENTS placeholder or append content
    if "$ARGUMENTS" in prompt_template:
        full_prompt = prompt_template.replace("$ARGUMENTS", input_content)
    else:
        full_prompt = f"{prompt_template}\n\n---\n\n{input_content}"

    # Write to temp file for AI CLI
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
        tmp.write(full_prompt)
        tmp_path = tmp.name

    logger.info(
        f"Calling AI CLI with prompt: {prompt_file.name}"
        + (f" (model: {model})" if model else "")
    )

    try:
        result = run_ai_prompt(full_prompt, config, timeout=timeout, model=model)
        return result.strip() if result else ""
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def generate_summary(
    clean_file: Path,
    prompt_file: Path,
    timeout: int = 300,
    model: str = None,
    config: Any = None
) -> str:
    """
    Generate AI summary using AI CLI.

    Args:
        clean_file: Path to cleaned subtitle file
        prompt_file: Path to yt-summary.md prompt
        timeout: Timeout in seconds
        model: Claude model to use

    Returns:
        Summary markdown text
    """
    logger.info(f"Generating summary for: {clean_file.name}")

    # Read the cleaned subtitle content
    with open(clean_file, "r", encoding="utf-8") as f:
        subtitle_content = f.read()

    return call_claude_with_prompt(prompt_file, subtitle_content, timeout, model, config=config)


def parse_chapters_from_summary(summary: str) -> List[Tuple[int, str]]:
    """
    Extract chapters from summary markdown.

    Args:
        summary: Summary markdown text

    Returns:
        List of (seconds, title) tuples
    """
    chapters = []

    # Pattern 1: Table rows: | 00:00 | Title | ... | or | 1:23:45 | Title | ... |
    table_pattern = r'\|\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*\|\s*([^|]+)\s*\|'
    matches = re.findall(table_pattern, summary)

    for match in matches:
        if match[2]:  # HH:MM:SS format
            seconds = int(match[0]) * 3600 + int(match[1]) * 60 + int(match[2])
        else:  # MM:SS format
            seconds = int(match[0]) * 60 + int(match[1])
        title = match[3].strip()
        chapters.append((seconds, title))

    # Pattern 2: List format variations:
    # - **00:00-01:30**: Title  or  - **00:00-01:30**：Title  or  - **00:00** - Title
    if not chapters:
        list_patterns = [
            r'-\s*\*\*(\d{1,2}):(\d{2})(?::(\d{2}))?(?:-[^*]+)?\*\*[：:]\s*(.+)',  # with colon
            r'-\s*\*\*(\d{1,2}):(\d{2})(?::(\d{2}))?\*\*\s*[-–—]\s*(.+)',  # with dash separator
        ]

        for pattern in list_patterns:
            matches = re.findall(pattern, summary)
            if matches:
                for match in matches:
                    if match[2]:  # HH:MM:SS format
                        seconds = int(match[0]) * 3600 + int(match[1]) * 60 + int(match[2])
                    else:  # MM:SS format
                        seconds = int(match[0]) * 60 + int(match[1])
                    title = match[3].strip()
                    chapters.append((seconds, title))
                break

    return chapters


def detect_video_type(summary: str) -> str:
    """
    Detect video type from summary.

    Args:
        summary: Summary markdown text

    Returns:
        Video type string
    """
    summary_lower = summary.lower()

    if "访谈对话" in summary or "interview" in summary_lower:
        return "访谈对话"
    elif "演讲独白" in summary or "speech" in summary_lower or "presentation" in summary_lower:
        return "演讲独白"
    elif "教程操作" in summary or "tutorial" in summary_lower:
        return "教程操作"
    elif "新闻播报" in summary or "news" in summary_lower:
        return "新闻播报"

    return "访谈对话"


def extract_speakers(summary: str) -> str:
    """
    Extract speaker section from summary.

    Args:
        summary: Summary markdown text

    Returns:
        Speaker information string
    """
    pattern = r'### 👤 主要人物.*?(?=###|\Z)'
    match = re.search(pattern, summary, re.DOTALL)
    if match:
        return match.group(0).strip()

    table_pattern = r'\| 人物 \| 角色.*?\n(?:\|.*?\n)+'
    table_match = re.search(table_pattern, summary)
    if table_match:
        return table_match.group(0).strip()

    return "（未识别到人物信息）"


def extract_intro(summary: str) -> str:
    """
    Extract intro section from summary.

    Args:
        summary: Summary markdown text

    Returns:
        Intro text
    """
    pattern = r'### 📋 开头.*?>\s*(.+?)(?=\n\n|\n###|\Z)'
    match = re.search(pattern, summary, re.DOTALL)
    if match:
        intro = match.group(1).strip()
        intro = re.sub(r'\n>\s*', ' ', intro)
        return intro
    return ""


def analyze_video(
    subtitle_text: str,
    prompt_file: Optional[Path] = None,
    timeout: int = 300,
    model: str = None,
    config: Any = None
) -> Optional[AnalysisResult]:
    """
    Analyze video content using AI CLI.

    Args:
        subtitle_text: Subtitle content (with metadata header)
        prompt_file: Path to yt-summary.md prompt
        timeout: Timeout in seconds
        model: Claude model to use

    Returns:
        AnalysisResult or None if failed
    """
    try:
        logger.info("Analyzing video content with AI CLI")

        # Use provided prompt or default
        if prompt_file and prompt_file.exists():
            summary = call_claude_with_prompt(prompt_file, subtitle_text, timeout, model, config=config)
        else:
            # Direct prompt if no file provided
            summary = _call_claude_direct(subtitle_text, timeout, model, config=config)

        if not summary:
            logger.error("No response from AI CLI")
            return None

        # Parse results from markdown
        chapters = parse_chapters_from_summary(summary)
        video_type = detect_video_type(summary)
        speakers = extract_speakers(summary)

        # Extract key points (look for bullet points in TL;DR section)
        key_points = []
        tldr_match = re.search(r'### .*?TL;DR.*?\n(.*?)(?=###|\Z)', summary, re.DOTALL | re.IGNORECASE)
        if tldr_match:
            bullets = re.findall(r'[-*]\s*(.+)', tldr_match.group(1))
            key_points = [b.strip() for b in bullets[:5]]

        result = AnalysisResult(
            summary=summary,
            chapters=chapters,
            video_type=video_type,
            speakers=speakers,
            key_points=key_points,
            raw_markdown=summary
        )

        logger.info(f"Analysis complete: {len(chapters)} chapters found")
        return result

    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        return None


def _call_claude_direct(
    subtitle_text: str,
    timeout: int = 300,
    model: str = None,
    config: Any = None
) -> str:
    """
    Call AI CLI directly with a prompt (no file).

    Args:
        subtitle_text: Subtitle content
        timeout: Timeout in seconds
        model: Claude model to use

    Returns:
        Claude's response
    """
    prompt = f"""你是一个专业的视频内容分析专家。请分析以下 YouTube 视频字幕，完成以下任务：

1. **生成视频摘要**（200-300 字，中文，清晰简洁）
2. **提取/生成章节时间轴**（表格格式：| 时间 | 标题 | 概括 |）
3. **检测视频类型**（访谈对话/演讲独白/教程操作/新闻播报）
4. **提取说话人信息**（如果是访谈或多人对话）
5. **提取核心要点**（TL;DR 列表）

字幕内容：

{subtitle_text}

请用 Markdown 格式输出。"""

    result = run_ai_prompt(prompt, config, timeout=timeout, model=model)
    return result.strip() if result else ""


def validate_analysis(analysis: AnalysisResult) -> Tuple[bool, List[str]]:
    """
    Validate analysis result.

    Args:
        analysis: AnalysisResult to validate

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    # Check summary
    if not analysis.summary or len(analysis.summary.strip()) == 0:
        issues.append("Empty summary")

    if len(analysis.summary) > 50000:
        issues.append("Summary too long")

    # Check chapters
    if not analysis.chapters:
        issues.append("No chapters found")

    # Check chapter order
    for i in range(len(analysis.chapters) - 1):
        if analysis.chapters[i][0] >= analysis.chapters[i + 1][0]:
            issues.append(f"Chapters out of order at index {i}")

    is_valid = len(issues) == 0

    if not is_valid:
        logger.warning(f"Analysis validation issues: {issues}")

    return is_valid, issues


def generate_fallback_chapters(total_duration_sec: int, interval_sec: int = 900) -> List[Tuple[int, str]]:
    """
    Generate fallback chapters based on time intervals.

    Args:
        total_duration_sec: Total video duration in seconds
        interval_sec: Interval between chapters (default 15 minutes)

    Returns:
        List of (seconds, title) tuples
    """
    chapters = []
    for i in range(0, total_duration_sec, interval_sec):
        part_num = i // interval_sec + 1
        chapters.append((i, f"Part {part_num}"))
    return chapters
