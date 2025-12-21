"""Chapter optimization and adjustment."""

import logging
from typing import List, Tuple
from dataclasses import dataclass
from core.ai_analyzer import ChapterInfo
from utils.srt_parser import SubtitleEntry

logger = logging.getLogger(__name__)


@dataclass
class OptimizedChapter:
    """Optimized chapter information."""

    index: int
    start_sec: float
    end_sec: float
    title: str
    duration_sec: float
    entry_count: int


def optimize_chapters(
    chapters: List[ChapterInfo],
    subtitle_entries: List[SubtitleEntry],
    min_duration: int = 180,
    max_duration: int = 900,
) -> List[OptimizedChapter]:
    """
    Optimize chapters by merging/splitting.

    Args:
        chapters: Original chapters from AI analysis
        subtitle_entries: Subtitle entries for timing
        min_duration: Minimum chapter duration (seconds)
        max_duration: Maximum chapter duration (seconds)

    Returns:
        List of optimized chapters

    Raises:
        ValueError: If parameters invalid
    """
    if min_duration <= 0 or max_duration <= 0:
        raise ValueError("Duration values must be positive")

    if min_duration > max_duration:
        raise ValueError("min_duration must be <= max_duration")

    if not chapters:
        logger.warning("No chapters to optimize")
        return []

    if not subtitle_entries:
        logger.warning("No subtitle entries for optimization")
        return []

    logger.info(f"Optimizing {len(chapters)} chapters")

    # Get total duration
    total_duration = subtitle_entries[-1].end_sec - subtitle_entries[0].start_sec

    # Create working chapter list with end times
    chapters_with_times = _add_end_times(chapters, total_duration)

    # Merge chapters below minimum duration
    merged = _merge_short_chapters(chapters_with_times, min_duration)

    # Split chapters above maximum duration
    split = _split_long_chapters(merged, max_duration)

    # Convert to OptimizedChapter
    optimized = []
    for i, (ch, end_time) in enumerate(split):
        # Count entries in this chapter
        entry_count = sum(
            1
            for e in subtitle_entries
            if e.start_sec >= ch.start_sec and e.end_sec <= end_time
        )

        optimized.append(
            OptimizedChapter(
                index=i,
                start_sec=ch.start_sec,
                end_sec=end_time,
                title=ch.title,
                duration_sec=end_time - ch.start_sec,
                entry_count=entry_count,
            )
        )

    logger.info(f"Optimized to {len(optimized)} chapters")
    return optimized


def _add_end_times(
    chapters: List[ChapterInfo], total_duration: float
) -> List[Tuple[ChapterInfo, float]]:
    """Add end times to chapters."""
    chapters_with_times = []

    for i, ch in enumerate(chapters):
        # End time is start of next chapter or total duration
        if i + 1 < len(chapters):
            end_time = chapters[i + 1].start_sec
        else:
            end_time = total_duration

        chapters_with_times.append((ch, end_time))

    return chapters_with_times


def _merge_short_chapters(
    chapters: List[Tuple[ChapterInfo, float]], min_duration: int
) -> List[Tuple[ChapterInfo, float]]:
    """Merge chapters that are shorter than minimum duration."""
    merged = []

    i = 0
    while i < len(chapters):
        ch, end_time = chapters[i]
        duration = end_time - ch.start_sec

        if duration >= min_duration:
            # Keep this chapter
            merged.append((ch, end_time))
            i += 1
        else:
            # Merge with next chapter
            if i + 1 < len(chapters):
                next_ch, next_end = chapters[i + 1]
                # Combine titles
                combined_title = f"{ch.title} & {next_ch.title}"
                combined_ch = ChapterInfo(start_sec=ch.start_sec, title=combined_title)
                merged.append((combined_ch, next_end))
                i += 2
            else:
                # Last chapter, keep as-is
                merged.append((ch, end_time))
                i += 1

        logger.debug(f"Merged short chapter: {ch.title} -> {duration}s")

    return merged


def _split_long_chapters(
    chapters: List[Tuple[ChapterInfo, float]], max_duration: int
) -> List[Tuple[ChapterInfo, float]]:
    """Split chapters that exceed maximum duration."""
    split = []

    for ch, end_time in chapters:
        duration = end_time - ch.start_sec

        if duration <= max_duration:
            split.append((ch, end_time))
        else:
            # Need to split this chapter
            num_parts = int((duration + max_duration - 1) / max_duration)
            part_duration = duration / num_parts

            for part_idx in range(num_parts):
                part_start = ch.start_sec + part_idx * part_duration
                if part_idx == num_parts - 1:
                    part_end = end_time
                else:
                    part_end = part_start + part_duration

                part_title = f"{ch.title} (Part {part_idx + 1}/{num_parts})"
                part_ch = ChapterInfo(start_sec=part_start, title=part_title)
                split.append((part_ch, part_end))

            logger.debug(f"Split long chapter: {ch.title} -> {num_parts} parts")

    return split


def validate_optimized_chapters(
    chapters: List[OptimizedChapter], min_duration: int = 180, max_duration: int = 900
) -> Tuple[bool, List[str]]:
    """
    Validate optimized chapters.

    Args:
        chapters: List of optimized chapters
        min_duration: Minimum expected duration
        max_duration: Maximum expected duration

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    if not chapters:
        issues.append("No chapters")
        return False, issues

    # Check for gaps and overlaps
    for i, ch in enumerate(chapters[:-1]):
        next_ch = chapters[i + 1]
        if ch.end_sec > next_ch.start_sec:
            issues.append(f"Overlapping chapters {i} and {i+1}")
        elif ch.end_sec < next_ch.start_sec:
            issues.append(f"Gap between chapters {i} and {i+1}")

    # Check durations
    for i, ch in enumerate(chapters):
        if ch.duration_sec < min_duration:
            issues.append(f"Chapter {i} too short: {ch.duration_sec}s")
        if ch.duration_sec > max_duration:
            issues.append(f"Chapter {i} too long: {ch.duration_sec}s")

    # Check titles
    for i, ch in enumerate(chapters):
        if not ch.title or len(ch.title.strip()) == 0:
            issues.append(f"Chapter {i} has empty title")

    is_valid = len(issues) == 0

    if not is_valid:
        logger.warning(f"Optimized chapter validation issues: {issues}")

    return is_valid, issues


def get_chapter_boundaries(
    chapters: List[OptimizedChapter],
) -> List[Tuple[float, float, str]]:
    """
    Get chapter start/end times and titles.

    Args:
        chapters: List of optimized chapters

    Returns:
        List of (start_sec, end_sec, title) tuples
    """
    return [(ch.start_sec, ch.end_sec, ch.title) for ch in chapters]


def estimate_chapter_quality(
    chapters: List[OptimizedChapter],
) -> dict:
    """
    Estimate quality metrics for chapters.

    Args:
        chapters: List of optimized chapters

    Returns:
        Quality metrics dictionary
    """
    if not chapters:
        return {
            "total_chapters": 0,
            "avg_duration_sec": 0.0,
            "total_duration_sec": 0.0,
            "duration_std_dev": 0.0,
            "avg_entries_per_chapter": 0.0,
        }

    durations = [ch.duration_sec for ch in chapters]
    entry_counts = [ch.entry_count for ch in chapters]

    avg_duration = sum(durations) / len(durations) if durations else 0
    total_duration = sum(durations)
    avg_entries = sum(entry_counts) / len(entry_counts) if entry_counts else 0

    # Calculate standard deviation
    variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
    std_dev = variance ** 0.5

    return {
        "total_chapters": len(chapters),
        "avg_duration_sec": avg_duration,
        "total_duration_sec": total_duration,
        "duration_std_dev": std_dev,
        "avg_entries_per_chapter": avg_entries,
        "min_duration_sec": min(durations),
        "max_duration_sec": max(durations),
    }
