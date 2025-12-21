"""Tests for core modules (video discovery, content fetching, subtitle processing)."""

import pytest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from utils.time_parser import (
    parse_timestamp,
    format_timestamp,
    parse_iso_date,
    format_iso_date,
    is_recent,
    seconds_to_duration_str,
    duration_str_to_seconds,
    get_time_range,
    overlaps,
    merge_ranges,
)
from utils.srt_parser import (
    SubtitleEntry,
    parse_srt_content,
    merge_subtitle_entries,
    split_by_time,
    extract_text,
    filter_by_duration,
    clean_text,
)
from core.video_discovery import (
    extract_video_id,
    construct_video_url,
    filter_new_videos,
)
from core.subtitle_processor import (
    split_by_chapters,
    get_chapter_text,
    get_time_range as get_entry_time_range,
    validate_subtitles,
    estimate_subtitle_quality,
)


class TestTimeParser:
    """Test time parsing utilities."""

    def test_parse_timestamp_hhmmss(self):
        """Test parsing HH:MM:SS format."""
        assert parse_timestamp("01:23:45") == 5025.0
        assert parse_timestamp("00:05:30") == 330.0

    def test_parse_timestamp_mmss(self):
        """Test parsing MM:SS format."""
        assert parse_timestamp("05:30") == 330.0
        assert parse_timestamp("01:00") == 60.0

    def test_parse_timestamp_with_milliseconds(self):
        """Test parsing with milliseconds."""
        assert parse_timestamp("00:05:30.500") == 330.5
        assert parse_timestamp("00:00:01.250") == 1.25

    def test_parse_timestamp_invalid(self):
        """Test parsing invalid timestamps."""
        assert parse_timestamp("invalid") is None
        assert parse_timestamp("") is None
        assert parse_timestamp("not:a:time") is None

    def test_format_timestamp(self):
        """Test formatting timestamp."""
        assert format_timestamp(5025.0) == "01:23:45"
        assert format_timestamp(330.0) == "05:30"
        assert format_timestamp(60.0) == "01:00"

    def test_format_iso_date(self):
        """Test formatting date."""
        dt = datetime(2025, 12, 21)
        assert format_iso_date(dt) == "2025-12-21"

    def test_parse_iso_date(self):
        """Test parsing ISO date."""
        dt = parse_iso_date("2025-12-21")
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 21

    def test_parse_iso_date_formats(self):
        """Test various ISO date formats."""
        assert parse_iso_date("2025-12-21") is not None
        assert parse_iso_date("20251221") is not None
        assert parse_iso_date("2025-12-21T10:30:00Z") is not None

    def test_is_recent(self):
        """Test checking if date is recent."""
        today = datetime.now().strftime("%Y-%m-%d")
        assert is_recent(today, 24) is True

        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        assert is_recent(old_date, 24) is False

    def test_seconds_to_duration_str(self):
        """Test converting seconds to duration string."""
        assert seconds_to_duration_str(5025) == "1h 23m 45s"
        assert seconds_to_duration_str(330) == "5m 30s"
        assert seconds_to_duration_str(45) == "45s"

    def test_duration_str_to_seconds(self):
        """Test parsing duration string."""
        assert duration_str_to_seconds("1h 23m 45s") == 5025.0
        assert duration_str_to_seconds("05:30") == 330.0
        assert duration_str_to_seconds("5m") == 300.0

    def test_get_time_range(self):
        """Test formatting time range."""
        result = get_time_range(330.0, 645.0)
        assert "05:30" in result
        assert "10:45" in result

    def test_overlaps(self):
        """Test time range overlap detection."""
        assert overlaps(100, 300, 200, 400) is True
        assert overlaps(100, 200, 300, 400) is False
        assert overlaps(0, 100, 100, 200) is False

    def test_merge_ranges(self):
        """Test merging overlapping ranges."""
        ranges = [(100, 300), (200, 400), (500, 600)]
        merged = merge_ranges(ranges)
        assert len(merged) == 2
        assert merged[0] == (100, 400)
        assert merged[1] == (500, 600)


class TestSrtParser:
    """Test SRT parsing utilities."""

    @pytest.fixture
    def sample_srt(self):
        """Create sample SRT content."""
        return """1
00:00:01,000 --> 00:00:05,000
Hello World

2
00:00:06,000 --> 00:00:10,000
This is a test

3
00:00:11,000 --> 00:00:15,000
Subtitle example
"""

    def test_parse_srt_content(self, sample_srt):
        """Test parsing SRT content."""
        entries = parse_srt_content(sample_srt)
        assert len(entries) == 3
        assert entries[0].text == "Hello World"
        assert entries[0].start_sec == 1.0
        assert entries[0].end_sec == 5.0

    def test_parse_srt_with_milliseconds(self):
        """Test parsing SRT with milliseconds."""
        srt = "1\n00:00:01,500 --> 00:00:05,750\nText"
        entries = parse_srt_content(srt)
        assert len(entries) == 1
        assert entries[0].start_sec == 1.5
        assert entries[0].end_sec == 5.75

    def test_merge_subtitle_entries(self):
        """Test merging close entries."""
        entries = [
            SubtitleEntry(1, 0.0, 5.0, "Hello"),
            SubtitleEntry(2, 5.5, 10.0, "World"),
        ]
        merged = merge_subtitle_entries(entries, max_gap_sec=1.0)
        assert len(merged) == 1
        assert "Hello" in merged[0].text
        assert "World" in merged[0].text

    def test_split_by_time(self):
        """Test splitting by time intervals."""
        entries = [
            SubtitleEntry(1, 0.0, 30.0, "Text1"),
            SubtitleEntry(2, 30.0, 60.0, "Text2"),
        ]
        segments = split_by_time(entries, 30.0)
        assert len(segments) >= 1

    def test_extract_text(self):
        """Test extracting text."""
        entries = [
            SubtitleEntry(1, 0.0, 5.0, "Hello"),
            SubtitleEntry(2, 5.0, 10.0, "World"),
        ]
        text = extract_text(entries)
        assert "Hello" in text
        assert "World" in text

    def test_filter_by_duration(self):
        """Test filtering by duration."""
        entries = [
            SubtitleEntry(1, 0.0, 0.3, "Short"),
            SubtitleEntry(2, 0.3, 2.0, "Long"),
        ]
        filtered = filter_by_duration(entries, min_sec=0.5)
        assert len(filtered) == 1
        assert filtered[0].text == "Long"

    def test_clean_text(self):
        """Test text cleaning."""
        assert clean_text("<i>Hello</i> world") == "Hello world"
        assert clean_text("Text  with   spaces") == "Text with spaces"


class TestVideoDiscovery:
    """Test video discovery utilities."""

    def test_extract_video_id_full_url(self):
        """Test extracting ID from full URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short_url(self):
        """Test extracting ID from short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_direct(self):
        """Test extracting direct video ID."""
        video_id = extract_video_id("dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_invalid(self):
        """Test extracting from invalid URL."""
        assert extract_video_id("not-a-url") is None
        assert extract_video_id("https://google.com") is None

    def test_construct_video_url(self):
        """Test constructing video URL."""
        url = construct_video_url("dQw4w9WgXcQ")
        assert "youtube.com" in url
        assert "dQw4w9WgXcQ" in url

    def test_filter_new_videos_empty_archive(self):
        """Test filtering with empty archive."""
        from infrastructure.archive import Archive

        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Archive(os.path.join(tmpdir, "archive.json"))
            new = filter_new_videos(["id1", "id2"], archive)
            assert len(new) == 2

    def test_filter_new_videos_with_processed(self):
        """Test filtering with processed videos."""
        from infrastructure.archive import Archive

        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Archive(os.path.join(tmpdir, "archive.json"))
            archive.mark_processed("id1", "Video 1", "/path/1.md")
            new = filter_new_videos(["id1", "id2"], archive)
            assert len(new) == 1
            assert "id2" in new


class TestSubtitleProcessor:
    """Test subtitle processing."""

    @pytest.fixture
    def sample_entries(self):
        """Create sample subtitle entries."""
        return [
            SubtitleEntry(1, 0.0, 30.0, "Introduction"),
            SubtitleEntry(2, 30.0, 60.0, "Main Content"),
            SubtitleEntry(3, 60.0, 90.0, "Conclusion"),
        ]

    def test_split_by_chapters(self, sample_entries):
        """Test splitting by chapters."""
        chapters = [(0.0, "Intro"), (30.0, "Main"), (60.0, "Conclusion")]
        result = split_by_chapters(sample_entries, chapters)
        assert len(result) > 0

    def test_get_chapter_text(self, sample_entries):
        """Test getting chapter text."""
        text = get_chapter_text(sample_entries)
        assert "Introduction" in text
        assert "Main Content" in text

    def test_get_time_range(self, sample_entries):
        """Test getting time range."""
        start, end = get_entry_time_range(sample_entries)
        assert start == 0.0
        assert end == 90.0

    def test_validate_subtitles(self, sample_entries):
        """Test subtitle validation."""
        valid, issues = validate_subtitles(sample_entries)
        assert valid is True
        assert len(issues) == 0

    def test_validate_subtitles_empty(self):
        """Test validation of empty subtitles."""
        valid, issues = validate_subtitles([])
        assert valid is False
        assert len(issues) > 0

    def test_validate_subtitles_overlapping(self):
        """Test validation of overlapping entries."""
        entries = [
            SubtitleEntry(1, 0.0, 50.0, "Text1"),
            SubtitleEntry(2, 30.0, 60.0, "Text2"),
        ]
        valid, issues = validate_subtitles(entries)
        assert valid is False
        assert any("Overlapping" in issue for issue in issues)

    def test_estimate_subtitle_quality(self, sample_entries):
        """Test subtitle quality estimation."""
        metrics = estimate_subtitle_quality(sample_entries)
        assert metrics["entry_count"] == 3
        assert metrics["coverage_percent"] > 0
        assert metrics["avg_entry_duration_sec"] > 0

    def test_estimate_subtitle_quality_empty(self):
        """Test quality estimation for empty."""
        metrics = estimate_subtitle_quality([])
        assert metrics["entry_count"] == 0


class TestIntegration:
    """Integration tests for Phase 2."""

    def test_complete_subtitle_workflow(self):
        """Test complete subtitle processing workflow."""
        # Create sample SRT
        srt_content = """1
00:00:01,000 --> 00:00:05,000
Hello World

2
00:00:06,000 --> 00:00:10,000
This is a test
"""

        # Parse
        entries = parse_srt_content(srt_content)
        assert len(entries) == 2

        # Filter
        filtered = filter_by_duration(entries, min_sec=0.5)
        assert len(filtered) == 2

        # Merge
        merged = merge_subtitle_entries(filtered)
        assert len(merged) > 0

        # Validate
        valid, issues = validate_subtitles(merged)
        assert valid is True

        # Get metrics
        metrics = estimate_subtitle_quality(merged)
        assert metrics["entry_count"] > 0

    def test_time_and_subtitle_integration(self):
        """Test integration of time and subtitle modules."""
        # Parse timestamp
        start = parse_timestamp("00:05:30")
        end = parse_timestamp("00:10:45")

        # Create entry
        entry = SubtitleEntry(1, start, end, "Test")
        assert entry.duration_sec == pytest.approx(315.0)

        # Format back
        formatted_start = format_timestamp(start)
        assert "05:30" in formatted_start

    def test_video_and_subtitle_integration(self):
        """Test integration of video discovery and subtitle processing."""
        # Extract video ID
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)

        # Construct URL back
        reconstructed = construct_video_url(video_id)
        assert video_id in reconstructed

        # Create archive and filter
        from infrastructure.archive import Archive

        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Archive(os.path.join(tmpdir, "archive.json"))
            archive.mark_processed(video_id, "Test Video", "/path/test.md")

            # Filter
            new = filter_new_videos([video_id, "other_id"], archive)
            assert video_id not in new
            assert "other_id" in new
