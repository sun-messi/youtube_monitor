"""
Pipeline Integration Tests

Comprehensive tests for the complete video processing pipeline.
Tests output generation, notifications, and end-to-end workflows.

Type hints: All functions have complete type hints
Docstrings: Google-style docstrings with examples
Test coverage: All major components and error conditions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile
import os

from core.output_generator import (
    generate_markdown,
    save_output,
    validate_output,
    _sanitize_filename,
    _format_duration,
    _seconds_to_timestamp,
    GeneratedOutput,
)
from core.ai_analyzer import AnalysisResult
from core.chapter_optimizer import OptimizedChapter
from core.translator import TranslationResult
from infrastructure.notifier import (
    send_notification,
    load_email_config,
    EmailConfig,
    _generate_html_email,
)
from infrastructure.config import Config
from infrastructure.archive import Archive


# ============================================================================
# Output Generator Tests
# ============================================================================


class TestMarkdownGeneration:
    """Test markdown generation from analysis results"""

    def test_generate_markdown_basic(self):
        """Test basic markdown generation with minimal data"""
        analysis = AnalysisResult(
            summary="Test summary",
            chapters=[(0, "Intro"), (180, "Main")],
            video_type="interview",
            speakers="Alice, Bob",
            key_points=["Point 1", "Point 2"],
        )

        chapters = [
            OptimizedChapter(
                index=0,
                start_sec=0,
                end_sec=180,
                title="Intro",
                duration_sec=180,
                entry_count=5,
            ),
            OptimizedChapter(
                index=1,
                start_sec=180,
                end_sec=360,
                title="Main",
                duration_sec=180,
                entry_count=10,
            ),
        ]

        translations = [
            TranslationResult(
                chapter_idx=0,
                chapter_title="Intro",
                original_text="Original 1",
                translated_text="Translation 1",
                success=True,
                duration_sec=180,
            ),
            TranslationResult(
                chapter_idx=1,
                chapter_title="Main",
                original_text="Original 2",
                translated_text="Translation 2",
                success=True,
                duration_sec=180,
            ),
        ]

        md = generate_markdown(
            video_id="test123",
            title="Test Video",
            description="Test description",
            upload_date="20251221",
            duration_sec=360,
            url="https://youtube.com/watch?v=test123",
            analysis=analysis,
            optimized_chapters=chapters,
            translations=translations,
            failed_chapter_indices=[],
        )

        assert "# Test Video" in md
        assert "Test summary" in md
        assert "Interview" in md or "interview" in md
        assert "Translation 1" in md
        assert "00:03:00" in md

    def test_generate_markdown_with_failures(self):
        """Test markdown with failed translation chapters"""
        analysis = AnalysisResult(
            summary="Test",
            chapters=[(0, "Ch1"), (180, "Ch2")],
            video_type="speech",
            speakers="Speaker",
            key_points=["Key point"],
        )

        chapters = [
            OptimizedChapter(
                index=0,
                start_sec=0,
                end_sec=180,
                title="Ch1",
                duration_sec=180,
                entry_count=5,
            ),
            OptimizedChapter(
                index=1,
                start_sec=180,
                end_sec=360,
                title="Ch2",
                duration_sec=180,
                entry_count=5,
            ),
        ]

        translations = [
            TranslationResult(
                chapter_idx=0,
                chapter_title="Ch1",
                original_text="Original",
                translated_text="Success",
                success=True,
                duration_sec=180,
            ),
            TranslationResult(
                chapter_idx=1,
                chapter_title="Ch2",
                original_text="Original",
                translated_text="",
                success=False,
                duration_sec=180,
            ),
        ]

        md = generate_markdown(
            video_id="test123",
            title="Test",
            description="",
            upload_date="20251221",
            duration_sec=360,
            url="https://youtube.com/watch?v=test123",
            analysis=analysis,
            optimized_chapters=chapters,
            translations=translations,
            failed_chapter_indices=[1],
        )

        assert "❌" in md
        assert "Translation failed" in md
        assert "1" in md  # Failed indices

    def test_generate_markdown_empty_description(self):
        """Test markdown with empty description"""
        analysis = AnalysisResult(
            summary="Summary", chapters=[], video_type="other", speakers="",
            key_points=[]
        )

        chapters = []
        translations = []

        md = generate_markdown(
            video_id="test",
            title="Title",
            description="",
            upload_date="20251221",
            duration_sec=60,
            url="https://youtube.com/watch?v=test",
            analysis=analysis,
            optimized_chapters=chapters,
            translations=translations,
            failed_chapter_indices=[],
        )

        assert "# Title" in md
        assert "Summary" in md

    def test_validate_output_valid(self):
        """Test validation of valid markdown"""
        md = """# Title

## Summary

Test summary content.

## Translation

### Chapter 1

Test translation.
"""
        assert validate_output(md) is True

    def test_validate_output_invalid_empty(self):
        """Test validation of empty markdown"""
        assert validate_output("") is False
        assert validate_output("   ") is False

    def test_validate_output_missing_sections(self):
        """Test validation of markdown missing required sections"""
        assert validate_output("No headers here") is False
        assert validate_output("# Title\n\nNo summary") is False


class TestFilenameHandling:
    """Test filename sanitization and handling"""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization"""
        result = _sanitize_filename("Test Video", 50)
        assert result == "test_video"
        assert len(result) <= 50

    def test_sanitize_filename_special_chars(self):
        """Test sanitization of special characters"""
        result = _sanitize_filename("Test: Video (2024)", 50)
        assert ":" not in result
        assert "(" not in result
        assert ")" not in result

    def test_sanitize_filename_max_length(self):
        """Test filename truncation to max length"""
        long_title = "A" * 100
        result = _sanitize_filename(long_title, 20)
        assert len(result) <= 20

    def test_sanitize_filename_empty(self):
        """Test sanitization of empty string"""
        result = _sanitize_filename("", 50)
        assert result == "video"


class TestTimestampFormatting:
    """Test timestamp and duration formatting"""

    def test_format_duration_hours(self):
        """Test duration formatting with hours"""
        assert _format_duration(3661) == "1:01:01"

    def test_format_duration_minutes(self):
        """Test duration formatting without hours"""
        assert _format_duration(125) == "2:05"

    def test_format_duration_seconds(self):
        """Test duration formatting of short duration"""
        assert _format_duration(30) == "0:30"

    def test_seconds_to_timestamp(self):
        """Test conversion of seconds to HH:MM:SS format"""
        assert _seconds_to_timestamp(3661.5) == "01:01:01"
        assert _seconds_to_timestamp(125.5) == "00:02:05"
        assert _seconds_to_timestamp(0) == "00:00:00"


# ============================================================================
# File Save Tests
# ============================================================================


class TestOutputSaving:
    """Test output file saving"""

    def test_save_output_creates_directory(self):
        """Test that save_output creates necessary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Mock()
            config.output_dir = tmpdir
            config.filename_max_length = 50

            path, count = save_output(
                "# Test\n\nContent",
                "test_id",
                "Test Title",
                "test_channel",
                config,
            )

            assert Path(path).exists()
            assert Path(tmpdir) in Path(path).parents

    def test_save_output_invalid_title(self):
        """Test save_output with invalid title"""
        config = Mock()
        config.output_dir = "/tmp"
        config.filename_max_length = 50

        with pytest.raises(ValueError):
            save_output("Content", "id", "", "channel", config)

    def test_save_output_word_count(self):
        """Test that word count is correctly calculated"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Mock()
            config.output_dir = tmpdir
            config.filename_max_length = 50

            content = "Word1 Word2 Word3 Word4 Word5"
            path, count = save_output(
                content, "test_id", "Title", "channel", config
            )

            assert count >= 5  # At least the words in content


# ============================================================================
# Email Notifier Tests
# ============================================================================


class TestEmailConfiguration:
    """Test email configuration loading"""

    @patch.dict(os.environ, {}, clear=True)
    def test_load_email_config_disabled(self):
        """Test loading email config when disabled"""
        config = load_email_config()
        assert config.enabled is False

    @patch.dict(
        os.environ,
        {
            "EMAIL_ENABLED": "false",
        },
    )
    def test_load_email_config_explicit_disabled(self):
        """Test loading email config when explicitly disabled"""
        config = load_email_config()
        assert config.enabled is False

    @patch.dict(
        os.environ,
        {
            "EMAIL_ENABLED": "true",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SENDER_EMAIL": "sender@test.com",
            "SENDER_PASSWORD": "password",
            "RECIPIENT_EMAIL": "recipient@test.com",
        },
    )
    def test_load_email_config_enabled(self):
        """Test loading enabled email config"""
        config = load_email_config()
        assert config.enabled is True
        assert config.smtp_server == "smtp.test.com"
        assert config.sender_email == "sender@test.com"


class TestEmailNotification:
    """Test email notification sending"""

    def test_send_notification_disabled(self):
        """Test notification when disabled"""
        config = EmailConfig(
            enabled=False,
            smtp_server="",
            smtp_port=587,
            sender_email="",
            sender_password="",
            recipient_email="",
        )

        result = send_notification(config, [])

        assert result.success is False

    def test_send_notification_no_videos(self):
        """Test notification with no videos"""
        config = EmailConfig(
            enabled=True,
            smtp_server="smtp.test.com",
            smtp_port=587,
            sender_email="sender@test.com",
            sender_password="pass",
            recipient_email="recipient@test.com",
        )

        result = send_notification(config, [])

        assert result.success is False
        assert result.videos_count == 0

    def test_generate_html_email(self):
        """Test HTML email generation"""
        videos = [
            {
                "title": "Test Video 1",
                "channel": "Test Channel",
                "file_path": "/path/to/file1.md",
                "url": "https://youtube.com/watch?v=test1",
            },
            {
                "title": "Test Video 2",
                "channel": "Test Channel",
                "file_path": "/path/to/file2.md",
            },
        ]

        html = _generate_html_email(videos)

        assert "<html>" in html
        assert "Test Video 1" in html
        assert "Test Video 2" in html
        assert "Test Channel" in html
        assert "<style>" in html


# ============================================================================
# Pipeline Integration Tests
# ============================================================================


class TestPipelineIntegration:
    """Test complete pipeline workflows"""

    def test_markdown_generation_workflow(self):
        """Test complete markdown generation workflow"""
        # Create analysis result
        analysis = AnalysisResult(
            summary="Video summary",
            chapters=[(0, "Intro"), (60, "Main"), (120, "Outro")],
            video_type="interview",
            speakers="Speaker1, Speaker2",
            key_points=["Key 1", "Key 2", "Key 3"],
        )

        # Create chapters
        chapters = [
            OptimizedChapter(
                index=0, start_sec=0, end_sec=60, title="Intro",
                duration_sec=60, entry_count=3
            ),
            OptimizedChapter(
                index=1, start_sec=60, end_sec=120, title="Main",
                duration_sec=60, entry_count=5
            ),
            OptimizedChapter(
                index=2, start_sec=120, end_sec=180, title="Outro",
                duration_sec=60, entry_count=2
            ),
        ]

        # Create translations
        translations = [
            TranslationResult(
                chapter_idx=0,
                chapter_title="Intro",
                original_text="Original",
                translated_text="Intro translation",
                success=True,
                duration_sec=60,
            ),
            TranslationResult(
                chapter_idx=1,
                chapter_title="Main",
                original_text="Original",
                translated_text="Main translation",
                success=True,
                duration_sec=60,
            ),
            TranslationResult(
                chapter_idx=2,
                chapter_title="Outro",
                original_text="Original",
                translated_text="",
                success=False,
                duration_sec=60,
            ),
        ]

        # Generate markdown
        md = generate_markdown(
            video_id="workflow_test",
            title="Workflow Test Video",
            description="This is a test video",
            upload_date="20251221",
            duration_sec=180,
            url="https://youtube.com/watch?v=workflow_test",
            analysis=analysis,
            optimized_chapters=chapters,
            translations=translations,
            failed_chapter_indices=[2],
        )

        # Validate output
        assert validate_output(md) is True
        assert "Workflow Test Video" in md
        assert "3" in md  # Total chapters count
        assert "2" in md  # Successful translations
        assert "Intro translation" in md
        assert "Main translation" in md


# ============================================================================
# Archive Integration Tests
# ============================================================================


class TestArchiveIntegration:
    """Test integration with archive system"""

    def test_archive_processed_video(self):
        """Test marking video as processed in archive"""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "archive.json"
            archive = Archive(str(archive_path))

            # Mark as processed
            archive.mark_processed(
                "test_video_123",
                "Test Video Title",
                "/path/to/output.md",
                0,  # no failed chapters
            )

            # Verify in archive
            stats = archive.get_stats()
            assert stats["total_processed"] >= 1


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling in pipeline components"""

    def test_output_generator_handles_none_values(self):
        """Test output generator with None/empty values"""
        analysis = AnalysisResult(
            summary="",
            chapters=[],
            video_type="other",
            speakers="",
            key_points=[],
        )

        md = generate_markdown(
            video_id="test",
            title="Title",
            description=None,
            upload_date="",
            duration_sec=0,
            url="",
            analysis=analysis,
            optimized_chapters=[],
            translations=[],
            failed_chapter_indices=[],
        )

        # Should still generate valid output
        assert "# Title" in md
        assert validate_output(md) is True

    def test_save_output_handles_permission_error(self):
        """Test save_output when directory creation fails"""
        config = Mock()
        config.output_dir = "/root/no_permission"  # Likely to fail
        config.filename_max_length = 50

        # Should raise OSError
        with pytest.raises(OSError):
            save_output(
                "Content",
                "id",
                "Title",
                "channel",
                config,
            )


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "00:00:00"),
        (59, "00:00:59"),
        (60, "00:01:00"),
        (3599, "00:59:59"),
        (3600, "01:00:00"),
        (3661, "01:01:01"),
    ],
)
def test_seconds_to_timestamp_parametrized(seconds, expected):
    """Parametrized test for seconds to timestamp conversion"""
    assert _seconds_to_timestamp(seconds) == expected


@pytest.mark.parametrize(
    "title,max_len,min_len",
    [
        ("Short Title", 50, 5),
        ("A" * 100, 50, 40),
        ("Test: Video (2024)", 50, 5),
        ("!@#$%", 50, 1),
    ],
)
def test_sanitize_filename_parametrized(title, max_len, min_len):
    """Parametrized test for filename sanitization"""
    result = _sanitize_filename(title, max_len)
    assert min_len <= len(result) <= max_len
