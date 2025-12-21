"""
SRT subtitle file parsing and processing.

Based on working implementation from /home/sunj11/youtube_monitor/clean_srt.py
"""

import re
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SubtitleEntry:
    """Single subtitle entry."""
    index: int
    start_sec: float
    end_sec: float
    text: str

    @property
    def duration_sec(self) -> float:
        """Get duration of subtitle in seconds."""
        return self.end_sec - self.start_sec

    def __str__(self) -> str:
        """Format as SRT entry."""
        start_ts = format_timestamp(self.start_sec)
        end_ts = format_timestamp(self.end_sec)
        return f"{self.index}\n{start_ts} --> {end_ts}\n{self.text}\n"


def parse_srt(srt_text: str) -> List[Tuple[int, int, str]]:
    """
    Parse SRT into [(start_sec, end_sec, text), ...].

    Args:
        srt_text: Raw SRT content

    Returns:
        List of (start_seconds, end_seconds, text) tuples
    """
    entries = []
    blocks = re.split(r'\n\n+', srt_text.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # Parse timestamp line
        time_match = re.search(
            r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
            lines[1]
        )
        if not time_match:
            continue

        start_sec = (int(time_match.group(1)) * 3600 +
                     int(time_match.group(2)) * 60 +
                     int(time_match.group(3)))
        end_sec = (int(time_match.group(5)) * 3600 +
                   int(time_match.group(6)) * 60 +
                   int(time_match.group(7)))
        text = ' '.join(lines[2:]).strip()

        # Remove HTML tags (like <c>, <font>, etc.)
        text = re.sub(r'<[^>]+>', '', text)

        entries.append((start_sec, end_sec, text))

    return entries


def parse_srt_full(srt_text: str) -> List[Tuple[int, int, str]]:
    """
    Parse SRT into [(start_sec, end_sec, text), ...].

    Alias for parse_srt() for compatibility.
    """
    return parse_srt(srt_text)


def merge_by_sentence(entries: List[Tuple[int, int, str]], interval: int = 30) -> List[Tuple[int, str]]:
    """
    Merge subtitles by sentence and time interval.

    Args:
        entries: List of (start_sec, end_sec, text) tuples
        interval: Maximum interval in seconds before splitting

    Returns:
        List of (start_sec, merged_text) tuples
    """
    if not entries:
        return []

    merged = []
    current_start = entries[0][0]
    current_texts = []
    last_end = entries[0][1]

    for start_sec, end_sec, text in entries:
        # Determine if we need to split
        # 1. Exceeded time interval
        # 2. Previous sentence ends with punctuation and there's a pause
        should_split = False

        if start_sec - current_start >= interval:
            should_split = True
        elif current_texts and current_texts[-1].rstrip().endswith(('.', '?', '!')):
            if start_sec - last_end > 2:  # Pause > 2 seconds
                should_split = True

        if should_split and current_texts:
            merged.append((current_start, ' '.join(current_texts)))
            current_start = start_sec
            current_texts = [text]
        else:
            current_texts.append(text)

        last_end = end_sec

    # Add the last segment
    if current_texts:
        merged.append((current_start, ' '.join(current_texts)))

    return merged


def format_time(seconds: int) -> str:
    """
    Convert seconds to MM:SS or HH:MM:SS format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds is None:
        return "End"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as SRT timestamp (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        SRT formatted timestamp
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_time_range(start_sec: int, end_sec: Optional[int] = None) -> str:
    """
    Format time range as "MM:SS - MM:SS" or "HH:MM:SS - HH:MM:SS".

    Args:
        start_sec: Start time in seconds
        end_sec: End time in seconds (None for "End")

    Returns:
        Formatted time range string
    """
    start_str = format_time(start_sec)
    end_str = format_time(end_sec) if end_sec else "End"
    return f"{start_str} - {end_str}"


def clean_subtitle(raw_srt: str, interval: int = 30) -> str:
    """
    Clean raw SRT into readable format: (MM:SS) text...

    Args:
        raw_srt: Raw SRT subtitle content
        interval: Merge interval in seconds

    Returns:
        Cleaned subtitle text
    """
    entries = parse_srt(raw_srt)
    merged = merge_by_sentence(entries, interval)

    output_lines = []
    for start_sec, text in merged:
        output_lines.append(f"({format_time(start_sec)}) {text}")

    return '\n\n'.join(output_lines)


def get_segment_text(srt_entries: List[Tuple[int, int, str]], start_sec: int, end_sec: Optional[int]) -> str:
    """
    Extract subtitle text for a time range.

    Args:
        srt_entries: List of (start_sec, end_sec, text) tuples
        start_sec: Start time in seconds
        end_sec: End time in seconds (None for till end)

    Returns:
        Combined text for the time range
    """
    texts = []

    for entry_start, entry_end, text in srt_entries:
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


def get_last_lines(text: str, n: int = 5) -> str:
    """
    Get last n lines of text.

    Args:
        text: Input text
        n: Number of lines to get

    Returns:
        Last n lines
    """
    lines = text.strip().split('\n')
    return '\n'.join(lines[-n:]) if len(lines) >= n else text


def parse_srt_file(file_path: str) -> List[SubtitleEntry]:
    """
    Parse SRT subtitle file into SubtitleEntry objects.

    Args:
        file_path: Path to .srt file

    Returns:
        List of SubtitleEntry objects
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return parse_srt_content(content)
    except FileNotFoundError:
        logger.error(f"SRT file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to read SRT file {file_path}: {e}")
        raise


def parse_srt_content(content: str) -> List[SubtitleEntry]:
    """
    Parse SRT content into SubtitleEntry objects.

    Args:
        content: SRT file content

    Returns:
        List of SubtitleEntry objects
    """
    entries = []
    blocks = re.split(r"\n\s*\n", content.strip())
    index = 0

    for block in blocks:
        if not block.strip():
            continue

        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        try:
            # Parse timestamps
            timestamp_line = lines[1].strip()
            match = re.match(
                r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})",
                timestamp_line,
            )

            if not match:
                continue

            start_ts = match.group(1).replace(",", ".")
            end_ts = match.group(2).replace(",", ".")

            start_sec = parse_timestamp_to_seconds(start_ts)
            end_sec = parse_timestamp_to_seconds(end_ts)

            if start_sec is None or end_sec is None:
                continue

            # Parse text (remaining lines)
            text = "\n".join(lines[2:]).strip()
            # Clean HTML tags
            text = re.sub(r'<[^>]+>', '', text)

            index += 1
            entries.append(
                SubtitleEntry(index=index, start_sec=start_sec, end_sec=end_sec, text=text)
            )

        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse subtitle block: {e}")
            continue

    if not entries:
        logger.warning("No valid subtitle entries found")
        return []

    logger.info(f"Parsed {len(entries)} subtitle entries")
    return entries


def parse_timestamp_to_seconds(timestamp: str) -> Optional[float]:
    """
    Parse SRT timestamp to seconds.

    Args:
        timestamp: Timestamp like "00:01:23.456" or "00:01:23,456"

    Returns:
        Seconds as float, or None if invalid
    """
    try:
        timestamp = timestamp.replace(",", ".")
        parts = timestamp.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
    except (ValueError, IndexError):
        pass
    return None


def extract_text(entries: List[SubtitleEntry], join_with: str = " ") -> str:
    """
    Extract all text from subtitle entries.

    Args:
        entries: List of subtitle entries
        join_with: String to join text blocks

    Returns:
        Combined text
    """
    texts = [entry.text for entry in entries]
    return join_with.join(texts)


def clean_text(text: str) -> str:
    """
    Clean subtitle text (remove HTML tags, extra whitespace).

    Args:
        text: Raw subtitle text

    Returns:
        Cleaned text
    """
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Remove common artifacts
    text = text.replace("♪", "").replace("♫", "")

    return text


def get_text_for_time_range(
    entries: List[SubtitleEntry],
    start_sec: float,
    end_sec: float,
    join_with: str = " ",
) -> str:
    """
    Get combined text for subtitle entries within a time range.

    Args:
        entries: List of subtitle entries
        start_sec: Start time in seconds
        end_sec: End time in seconds
        join_with: String to join text blocks

    Returns:
        Combined text for entries in the time range
    """
    matching_entries = []
    for entry in entries:
        # Check if entry overlaps with the time range
        if entry.start_sec < end_sec and entry.end_sec > start_sec:
            matching_entries.append(entry)

    texts = [entry.text for entry in matching_entries]
    return join_with.join(texts)
