"""Time parsing and manipulation utilities."""

from datetime import datetime, timedelta
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str: str) -> Optional[float]:
    """
    Parse timestamp string to seconds.

    Supports formats: "HH:MM:SS", "MM:SS", "00:05:30.500"

    Args:
        timestamp_str: Timestamp string

    Returns:
        Total seconds as float, or None if invalid

    Examples:
        >>> parse_timestamp("01:23:45")
        5025.0
        >>> parse_timestamp("05:30")
        330.0
        >>> parse_timestamp("00:05:30.500")
        330.5
    """
    if not timestamp_str:
        return None

    try:
        timestamp_str = timestamp_str.strip()

        # Handle milliseconds
        milliseconds = 0.0
        if "." in timestamp_str:
            timestamp_str, ms_str = timestamp_str.rsplit(".", 1)
            milliseconds = int(ms_str[:3]) / 1000.0

        parts = timestamp_str.split(":")
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds + milliseconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds + milliseconds
        else:
            logger.warning(f"Invalid timestamp format: {timestamp_str}")
            return None

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return None


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to timestamp string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted timestamp "HH:MM:SS" or "MM:SS" if less than 1 hour

    Examples:
        >>> format_timestamp(5025.0)
        '01:23:45'
        >>> format_timestamp(330.0)
        '05:30'
    """
    if seconds < 0:
        logger.warning(f"Negative seconds: {seconds}")
        seconds = 0

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """
    Parse ISO format date string.

    Supports: "2025-12-21", "20251221", "2025-12-21T10:30:00Z"

    Args:
        date_str: Date string in ISO format

    Returns:
        datetime object or None if invalid

    Examples:
        >>> parse_iso_date("2025-12-21")
        datetime.datetime(2025, 12, 21, 0, 0)
        >>> parse_iso_date("20251221")
        datetime.datetime(2025, 12, 21, 0, 0)
    """
    if not date_str:
        return None

    try:
        date_str = date_str.strip()

        # Try different formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y%m%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def format_iso_date(dt: datetime) -> str:
    """
    Format datetime to ISO format string.

    Args:
        dt: datetime object

    Returns:
        ISO format string "YYYY-MM-DD"

    Examples:
        >>> format_iso_date(datetime(2025, 12, 21))
        '2025-12-21'
    """
    return dt.strftime("%Y-%m-%d")


def is_recent(
    upload_date_str: str, lookback_hours: int, reference_time: Optional[datetime] = None
) -> bool:
    """
    Check if video was uploaded within lookback period.

    Args:
        upload_date_str: Upload date string (ISO format)
        lookback_hours: How many hours to look back
        reference_time: Reference time for calculation (defaults to now)

    Returns:
        True if video is within lookback period

    Examples:
        >>> is_recent("2025-12-21", 24)
        True
    """
    if reference_time is None:
        reference_time = datetime.now()

    upload_dt = parse_iso_date(upload_date_str)
    if not upload_dt:
        return False

    cutoff_time = reference_time - timedelta(hours=lookback_hours)
    return upload_dt >= cutoff_time


def seconds_to_duration_str(seconds: float) -> str:
    """
    Convert seconds to human-readable duration string.

    Args:
        seconds: Duration in seconds

    Returns:
        Duration string like "1h 23m 45s"

    Examples:
        >>> seconds_to_duration_str(5025)
        '1h 23m 45s'
        >>> seconds_to_duration_str(330)
        '5m 30s'
    """
    if seconds < 0:
        return "0s"

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def duration_str_to_seconds(duration_str: str) -> Optional[float]:
    """
    Parse duration string to seconds.

    Supports formats: "1h 23m 45s", "05:30", "5m", "45s"

    Args:
        duration_str: Duration string

    Returns:
        Total seconds or None if invalid

    Examples:
        >>> duration_str_to_seconds("1h 23m 45s")
        5025.0
        >>> duration_str_to_seconds("05:30")
        330.0
        >>> duration_str_to_seconds("5m")
        300.0
    """
    if not duration_str:
        return None

    try:
        duration_str = duration_str.strip().lower()

        # Try timestamp format first
        if ":" in duration_str:
            return parse_timestamp(duration_str)

        # Try human-readable format
        total = 0.0
        pattern = r"(\d+(?:\.\d+)?)\s*([smhd])"

        matches = re.findall(pattern, duration_str)
        if not matches:
            return None

        for value_str, unit in matches:
            value = float(value_str)
            if unit == "s":
                total += value
            elif unit == "m":
                total += value * 60
            elif unit == "h":
                total += value * 3600
            elif unit == "d":
                total += value * 86400

        return total if total > 0 else None

    except Exception as e:
        logger.warning(f"Failed to parse duration '{duration_str}': {e}")
        return None


def get_time_range(start_sec: float, end_sec: float) -> str:
    """
    Get formatted time range string.

    Args:
        start_sec: Start time in seconds
        end_sec: End time in seconds

    Returns:
        Formatted range like "00:05:30 - 00:10:45"

    Examples:
        >>> get_time_range(330.0, 645.0)
        '00:05:30 - 00:10:45'
    """
    start_str = format_timestamp(start_sec)
    end_str = format_timestamp(end_sec)
    return f"{start_str} - {end_str}"


def overlaps(
    start1: float, end1: float, start2: float, end2: float
) -> bool:
    """
    Check if two time ranges overlap.

    Args:
        start1: Start of first range (seconds)
        end1: End of first range (seconds)
        start2: Start of second range (seconds)
        end2: End of second range (seconds)

    Returns:
        True if ranges overlap

    Examples:
        >>> overlaps(100, 300, 200, 400)
        True
        >>> overlaps(100, 200, 300, 400)
        False
    """
    return start1 < end2 and start2 < end1


def merge_ranges(ranges: list[Tuple[float, float]]) -> list[Tuple[float, float]]:
    """
    Merge overlapping time ranges.

    Args:
        ranges: List of (start, end) tuples

    Returns:
        Merged list of non-overlapping ranges

    Examples:
        >>> merge_ranges([(100, 300), (200, 400), (500, 600)])
        [(100, 400), (500, 600)]
    """
    if not ranges:
        return []

    # Sort by start time
    sorted_ranges = sorted(ranges, key=lambda x: x[0])

    merged = [sorted_ranges[0]]
    for current_start, current_end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]

        if current_start <= last_end:
            # Overlap - merge
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            # No overlap - add as new range
            merged.append((current_start, current_end))

    return merged
