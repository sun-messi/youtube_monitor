"""Utility functions and helpers."""

from .srt_parser import (
    SubtitleEntry,
    parse_srt,
    parse_srt_full,
    parse_srt_file,
    parse_srt_content,
    merge_by_sentence,
    format_time,
    format_timestamp,
    format_time_range,
    clean_subtitle,
    get_segment_text,
    get_last_lines,
    parse_timestamp_to_seconds,
    extract_text,
    clean_text,
    get_text_for_time_range,
)

__all__ = [
    # srt_parser
    "SubtitleEntry",
    "parse_srt",
    "parse_srt_full",
    "parse_srt_file",
    "parse_srt_content",
    "merge_by_sentence",
    "format_time",
    "format_timestamp",
    "format_time_range",
    "clean_subtitle",
    "get_segment_text",
    "get_last_lines",
    "parse_timestamp_to_seconds",
    "extract_text",
    "clean_text",
    "get_text_for_time_range",
]
