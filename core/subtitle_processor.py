"""
Subtitle processing and cleanup.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py
and /home/sunj11/youtube_monitor/clean_srt.py
"""

import logging
from typing import List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from utils.srt_parser import (
    parse_srt,
    merge_by_sentence,
    format_time,
    clean_subtitle,
    SubtitleEntry,
    parse_srt_content,
    clean_text,
    extract_text,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessedSubtitles:
    """Processed subtitle data."""
    raw_text: str                    # Merged raw text
    entries: List[Tuple[int, int, str]]  # Structured entries (start, end, text)
    with_metadata: str               # Text with video metadata header
    clean_text: str                  # Cleaned/formatted text


def process_subtitle_file(
    file_path: str,
    title: str = "Unknown",
    channel: str = "Unknown",
    video_url: str = "",
    duration_sec: float = 0.0,
    merge_interval: int = 30,
) -> Optional[ProcessedSubtitles]:
    """
    Process subtitle file from SRT.

    Args:
        file_path: Path to .srt file
        title: Video title
        channel: Channel name
        video_url: Original video URL
        duration_sec: Video duration (optional, calculated from entries if 0)
        merge_interval: Interval for merging subtitles

    Returns:
        ProcessedSubtitles object or None if failed
    """
    try:
        logger.info(f"Processing subtitle file: {file_path}")

        # Read raw SRT
        with open(file_path, "r", encoding="utf-8") as f:
            raw_srt = f.read()

        return process_subtitle_text(
            raw_srt, title, channel, video_url, merge_interval
        )

    except FileNotFoundError:
        logger.error(f"Subtitle file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to process subtitles: {e}")
        return None


def process_subtitle_text(
    raw_srt: str,
    title: str = "",
    channel: str = "",
    video_url: str = "",
    merge_interval: int = 30
) -> Optional[ProcessedSubtitles]:
    """
    Process raw SRT text into structured subtitle data.

    Args:
        raw_srt: Raw SRT content
        title: Video title
        channel: Channel name
        video_url: Original video URL
        merge_interval: Seconds between paragraph breaks

    Returns:
        ProcessedSubtitles object or None if failed
    """
    # Parse SRT
    entries = parse_srt(raw_srt)

    if not entries:
        logger.warning("No subtitle entries found")
        return None

    # Clean subtitle (merge by sentence)
    cleaned_text = clean_subtitle(raw_srt, merge_interval)

    # Generate raw merged text
    merged = merge_by_sentence(entries, merge_interval)
    raw_text = '\n\n'.join([text for _, text in merged])

    # Generate text with metadata header
    with_metadata = _inject_metadata(cleaned_text, title, channel, video_url, entries)

    logger.info(f"Processed {len(entries)} subtitle entries")

    return ProcessedSubtitles(
        raw_text=raw_text,
        entries=entries,
        with_metadata=with_metadata,
        clean_text=cleaned_text
    )


def _inject_metadata(
    subtitle_text: str,
    title: str,
    channel: str,
    video_url: str,
    entries: List[Tuple[int, int, str]]
) -> str:
    """
    Inject video metadata into subtitle text header.

    Args:
        subtitle_text: Cleaned subtitle text
        title: Video title
        channel: Channel name
        video_url: Video URL
        entries: SRT entries for duration calculation

    Returns:
        Text with metadata header
    """
    # Calculate duration
    duration_sec = entries[-1][1] if entries else 0
    duration_str = format_time(duration_sec)

    header = f"""===== Video Information =====
Title: {title}
Channel: {channel}
URL: {video_url}
Duration: {duration_str} ({duration_sec}s)
Subtitles: {len(entries)} entries
=============================

"""
    return header + subtitle_text


def save_clean_subtitle(
    subtitle_data: ProcessedSubtitles,
    output_path: Path
) -> str:
    """
    Save cleaned subtitle to file.

    Args:
        subtitle_data: Processed subtitle data
        output_path: Path to save file

    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(subtitle_data.clean_text)

    logger.info(f"Saved clean subtitle to {output_path}")
    return str(output_path)


def get_duration_from_entries(entries: List[Tuple[int, int, str]]) -> int:
    """
    Get video duration from SRT entries.

    Args:
        entries: List of (start_sec, end_sec, text) tuples

    Returns:
        Duration in seconds
    """
    if not entries:
        return 0
    return entries[-1][1]


def check_minimum_duration(entries: List[Tuple[int, int, str]], min_minutes: int) -> Tuple[bool, str]:
    """
    Check if video meets minimum duration requirement.

    Args:
        entries: SRT entries
        min_minutes: Minimum duration in minutes

    Returns:
        (is_long_enough, duration_string)
    """
    duration = get_duration_from_entries(entries)
    min_seconds = min_minutes * 60
    duration_str = f"{duration // 60}:{duration % 60:02d}"
    return duration >= min_seconds, duration_str


def get_segment_text(
    entries: List[Tuple[int, int, str]],
    start_sec: int,
    end_sec: Optional[int] = None
) -> str:
    """
    Extract subtitle text for a time range.

    Args:
        entries: SRT entries
        start_sec: Start time in seconds
        end_sec: End time in seconds (None for till end)

    Returns:
        Combined text for the segment
    """
    texts = []

    for entry_start, entry_end, text in entries:
        if entry_start >= start_sec:
            if end_sec is None or entry_start < end_sec:
                texts.append(text)
            elif entry_start >= end_sec:
                # Extend to sentence boundary
                if texts and not texts[-1].rstrip().endswith(('.', '?', '!')):
                    texts.append(text)
                    if text.rstrip().endswith(('.', '?', '!')):
                        break
                else:
                    break

    return '\n'.join(texts)


def get_context_lines(text: str, n_lines: int = 5) -> str:
    """
    Get last n lines from text for context.

    Args:
        text: Full text
        n_lines: Number of lines to extract

    Returns:
        Last n lines of text
    """
    lines = text.strip().split('\n')
    return '\n'.join(lines[-n_lines:]) if len(lines) >= n_lines else text


def split_by_chapters(
    entries: List[Tuple[int, int, str]],
    chapters: List[Tuple[int, str]]
) -> List[Tuple[str, str, List[Tuple[int, int, str]]]]:
    """
    Split subtitles into chapters.

    Args:
        entries: List of (start_sec, end_sec, text) tuples
        chapters: List of (start_sec, title) tuples

    Returns:
        List of (time_range, chapter_title, entries) tuples
    """
    if not chapters:
        logger.warning("No chapters provided")
        return [("0:00 - End", "Full Video", entries)]

    # Sort chapters by start time
    sorted_chapters = sorted(chapters, key=lambda x: x[0])

    result = []

    for i, (chapter_start, chapter_title) in enumerate(sorted_chapters):
        # Get next chapter start time
        if i + 1 < len(sorted_chapters):
            chapter_end = sorted_chapters[i + 1][0]
        else:
            chapter_end = None

        # Find entries in this chapter range
        chapter_entries = []
        for entry_start, entry_end, text in entries:
            if entry_start >= chapter_start:
                if chapter_end is None or entry_start < chapter_end:
                    chapter_entries.append((entry_start, entry_end, text))

        if chapter_entries:
            time_range = f"{format_time(chapter_start)} - {format_time(chapter_end) if chapter_end else 'End'}"
            result.append((time_range, chapter_title, chapter_entries))
            logger.debug(f"Chapter '{chapter_title}': {len(chapter_entries)} entries")

    logger.info(f"Split {len(entries)} entries into {len(result)} chapters")
    return result


def validate_subtitles(entries: List[Tuple[int, int, str]]) -> Tuple[bool, List[str]]:
    """
    Validate subtitle entries for quality issues.

    Args:
        entries: List of (start_sec, end_sec, text) tuples

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    if not entries:
        issues.append("No subtitle entries found")
        return False, issues

    # Check for empty text
    empty_count = sum(1 for _, _, text in entries if not text.strip())
    if empty_count > 0:
        issues.append(f"{empty_count} entries with empty text")

    # Check for very short entries (< 0.5 seconds)
    short_count = sum(1 for start, end, _ in entries if (end - start) < 0.5)
    if short_count > len(entries) * 0.1:  # More than 10%
        issues.append(f"{short_count} very short entries")

    is_valid = len(issues) == 0

    if is_valid:
        logger.info(f"Subtitle validation passed: {len(entries)} entries")
    else:
        logger.warning(f"Subtitle validation issues: {issues}")

    return is_valid, issues


def estimate_subtitle_quality(entries: List[Tuple[int, int, str]]) -> dict:
    """
    Estimate quality metrics for subtitles.

    Args:
        entries: List of (start_sec, end_sec, text) tuples

    Returns:
        Quality metrics dictionary
    """
    if not entries:
        return {
            "entry_count": 0,
            "total_duration_sec": 0.0,
            "coverage_percent": 0.0,
            "avg_entry_duration_sec": 0.0,
            "total_text_length": 0,
        }

    start_sec = entries[0][0]
    end_sec = entries[-1][1]
    total_video_duration = end_sec - start_sec

    # Calculate covered duration
    covered_duration = sum(end - start for start, end, _ in entries)

    # Calculate total text
    total_text = sum(len(text) for _, _, text in entries)

    return {
        "entry_count": len(entries),
        "total_duration_sec": total_video_duration,
        "covered_duration_sec": covered_duration,
        "coverage_percent": (covered_duration / total_video_duration * 100) if total_video_duration > 0 else 0,
        "avg_entry_duration_sec": covered_duration / len(entries) if entries else 0,
        "total_text_length": total_text,
        "avg_text_per_entry": total_text / len(entries) if entries else 0,
    }
