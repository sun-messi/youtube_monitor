"""
AI video analysis using Claude CLI.

Supports two modes:
1. Direct Claude CLI call (default)
2. Agent-based call using tech-investment-analyst (for specialized analysis)

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py
"""

import logging
import os
import re
import subprocess
import tempfile
from typing import List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from core.agent_caller import call_agent, call_agent_with_file, AGENT_TECH_INVESTMENT

logger = logging.getLogger(__name__)


def get_claude_cli_path() -> Path:
    """
    Find the latest Claude CLI binary from VSCode extensions.

    Returns:
        Path to the Claude CLI binary
    """
    extensions_dir = Path.home() / ".vscode-server/extensions"

    if not extensions_dir.exists():
        # Fallback if extensions directory doesn't exist
        return Path.home() / ".vscode-server/extensions/anthropic.claude-code-2.0.72-linux-x64/resources/native-binary/claude"

    # Find all claude-code extensions and get the latest one
    try:
        claude_extensions = sorted([d for d in extensions_dir.iterdir() if d.name.startswith("anthropic.claude-code-")])
        if claude_extensions:
            latest = claude_extensions[-1]  # Get the last (newest) version
            return latest / "resources/native-binary/claude"
    except Exception:
        pass  # If any error occurs, fall back to known version

    # Fallback to known version
    return Path.home() / ".vscode-server/extensions/anthropic.claude-code-2.0.72-linux-x64/resources/native-binary/claude"


# Claude CLI path
CLAUDE_CLI = get_claude_cli_path()


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
    thinking_budget: int = 0
) -> str:
    """
    Call Claude CLI with a local prompt file.

    Args:
        prompt_file: Path to prompt file (e.g., PROMPT_SUMMARY)
        input_content: Content to append to the prompt
        timeout: Timeout in seconds
        model: Claude model to use
        thinking_budget: Token budget for extended thinking (0 = disabled)

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

    # Write to temp file for Claude CLI
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
        tmp.write(full_prompt)
        tmp_path = tmp.name

    thinking_info = f", thinking: {thinking_budget}" if thinking_budget > 0 else ""
    logger.info(f"Calling Claude CLI with prompt: {prompt_file.name}" + (f" (model: {model}{thinking_info})" if model else ""))

    try:
        # Pass the full prompt directly to Claude CLI
        cmd = [
            str(CLAUDE_CLI),
            "-p", full_prompt,
            "--output-format", "text"
        ]
        if model:
            cmd.extend(["--model", model])
        # Note: --thinking-budget is not supported by Claude CLI, skipping

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            return ""

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.error(f"Claude CLI timeout after {timeout}s")
        return ""
    except FileNotFoundError:
        logger.error("Claude CLI not found. Make sure 'claude' is installed and in PATH.")
        return ""
    except Exception as e:
        logger.error(f"Claude CLI error: {e}")
        return ""
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


def generate_summary(
    clean_file: Path,
    prompt_file: Path,
    timeout: int = 300,
    model: str = None
) -> str:
    """
    Generate AI summary using Claude CLI.

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

    return call_claude_with_prompt(prompt_file, subtitle_content, timeout, model)


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
    thinking_budget: int = 0,
    use_agent: bool = False,
    agent_name: str = AGENT_TECH_INVESTMENT
) -> Optional[AnalysisResult]:
    """
    Analyze video content using Claude CLI.

    Args:
        subtitle_text: Subtitle content (with metadata header)
        prompt_file: Path to yt-summary.md prompt
        timeout: Timeout in seconds
        model: Claude model to use
        thinking_budget: Token budget for extended thinking (0 = disabled)
        use_agent: If True, use specialized agent for analysis
        agent_name: Agent name to use (default: tech-investment-analyst)

    Returns:
        AnalysisResult or None if failed
    """
    try:
        thinking_info = f" with thinking budget {thinking_budget}" if thinking_budget > 0 else ""
        logger.info(f"Analyzing video content {'with agent ' + agent_name if use_agent else 'with Claude CLI'}{thinking_info}")

        # Use agent-based analysis
        if use_agent:
            if prompt_file and prompt_file.exists():
                summary = call_agent_with_file(agent_name, prompt_file, subtitle_text, timeout)
            else:
                summary = call_agent(agent_name, _build_analysis_prompt(subtitle_text), timeout)
        # Use direct Claude CLI call
        elif prompt_file and prompt_file.exists():
            summary = call_claude_with_prompt(prompt_file, subtitle_text, timeout, model, thinking_budget)
        else:
            # Direct prompt if no file provided
            summary = _call_claude_direct(subtitle_text, timeout, model)

        if not summary:
            logger.error("No response from Claude CLI")
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


def _build_analysis_prompt(subtitle_text: str) -> str:
    """Build the analysis prompt for agent-based or direct calls."""
    return f"""你是一个专业的视频内容分析专家。请分析以下 YouTube 视频字幕，完成以下任务：

1. **生成视频摘要**（200-300 字，中文，清晰简洁）
2. **提取/生成章节时间轴**（表格格式：| 时间 | 标题 | 概括 |）
3. **检测视频类型**（访谈对话/演讲独白/教程操作/新闻播报）
4. **提取说话人信息**（如果是访谈或多人对话）
5. **提取核心要点**（TL;DR 列表）

字幕内容：

{subtitle_text}

请用 Markdown 格式输出。"""


def _call_claude_direct(
    subtitle_text: str,
    timeout: int = 300,
    model: str = None
) -> str:
    """
    Call Claude CLI directly with a prompt (no file).

    Args:
        subtitle_text: Subtitle content
        timeout: Timeout in seconds
        model: Claude model to use

    Returns:
        Claude's response
    """
    prompt = _build_analysis_prompt(subtitle_text)

    try:
        cmd = [
            str(CLAUDE_CLI),
            "-p", prompt,
            "--output-format", "text"
        ]
        if model:
            cmd.extend(["--model", model])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            return ""

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.error(f"Claude CLI timeout after {timeout}s")
        return ""
    except Exception as e:
        logger.error(f"Claude CLI error: {e}")
        return ""


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
