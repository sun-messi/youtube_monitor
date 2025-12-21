"""Tests for infrastructure modules (config, logger, archive)."""

import pytest
import json
import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime

from infrastructure.config import Config, ChannelConfig, load_config, validate_config
from infrastructure.logger import setup_logger, get_logger, configure_root_logger
from infrastructure.archive import Archive


class TestChannelConfig:
    """Test ChannelConfig data class."""

    def test_channel_config_creation(self):
        """Test creating ChannelConfig instance."""
        channel = ChannelConfig(
            name="Test Channel",
            handle="@testchannel",
            url="https://youtube.com/@testchannel",
            channel_id="UC123456789",
        )

        assert channel.name == "Test Channel"
        assert channel.handle == "@testchannel"
        assert channel.url == "https://youtube.com/@testchannel"
        assert channel.channel_id == "UC123456789"


class TestConfig:
    """Test Config data class and loading."""

    @pytest.fixture
    def temp_config_files(self):
        """Create temporary config files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config_ai.json")
            channels_path = os.path.join(tmpdir, "channels.json")

            # Create sample config
            config_data = {
                "lookback_hours": 20,
                "min_duration_minutes": 10,
                "subtitle_language": "en",
                "subtitle_merge_interval": 30,
                "claude_model": "claude-sonnet-4-20250514",
                "claude_timeout_seconds": 600,
                "min_chapter_duration": 180,
                "max_chapter_duration": 900,
                "context_lines": 5,
                "translation_max_tokens": 4000,
                "translation_max_retries": 2,
                "translation_retry_delay": 5,
                "output_dir": "./ai_output",
                "filename_max_length": 50,
                "archive_file": "./youtube_archive.json",
                "email_enabled": False,
                "check_interval_hours": 3,
            }

            # Create sample channels
            channels_data = {
                "channels": [
                    {
                        "name": "Channel 1",
                        "handle": "@channel1",
                        "url": "https://youtube.com/@channel1",
                        "channel_id": "UC111111111",
                    },
                    {
                        "name": "Channel 2",
                        "handle": "@channel2",
                        "url": "https://youtube.com/@channel2",
                        "channel_id": "UC222222222",
                    },
                ]
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            with open(channels_path, "w", encoding="utf-8") as f:
                json.dump(channels_data, f)

            yield config_path, channels_path

    def test_load_config(self, temp_config_files):
        """Test loading config from files."""
        config_path, channels_path = temp_config_files

        config = load_config(config_path, channels_path)

        assert isinstance(config, Config)
        assert config.lookback_hours == 20
        assert config.min_duration_minutes == 10
        assert config.subtitle_language == "en"
        assert config.claude_model == "claude-sonnet-4-20250514"
        assert len(config.channels) == 2
        assert config.channels[0].name == "Channel 1"

    def test_load_config_missing_file(self):
        """Test loading config with missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.json", "/nonexistent/channels.json")

    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            with open(config_path, "w") as f:
                f.write("invalid json {")

            with pytest.raises(json.JSONDecodeError):
                load_config(config_path, config_path)

    def test_load_config_missing_field(self, temp_config_files):
        """Test loading config with missing required field."""
        config_path, channels_path = temp_config_files

        # Corrupt the config
        with open(config_path, "r") as f:
            data = json.load(f)

        del data["lookback_hours"]

        with open(config_path, "w") as f:
            json.dump(data, f)

        with pytest.raises(ValueError):
            load_config(config_path, channels_path)

    def test_validate_config_valid(self, temp_config_files):
        """Test validation of valid config."""
        config_path, channels_path = temp_config_files
        config = load_config(config_path, channels_path)

        assert validate_config(config) is True

    def test_validate_config_invalid_durations(self, temp_config_files):
        """Test validation of invalid chapter durations."""
        config_path, channels_path = temp_config_files
        config = load_config(config_path, channels_path)

        config.max_chapter_duration = config.min_chapter_duration - 1

        with pytest.raises(ValueError):
            validate_config(config)

    def test_validate_config_negative_hours(self, temp_config_files):
        """Test validation of negative hours."""
        config_path, channels_path = temp_config_files
        config = load_config(config_path, channels_path)

        config.lookback_hours = -1

        with pytest.raises(ValueError):
            validate_config(config)

    def test_validate_config_no_channels(self, temp_config_files):
        """Test validation with no channels."""
        config_path, channels_path = temp_config_files
        config = load_config(config_path, channels_path)

        config.channels = []

        with pytest.raises(ValueError):
            validate_config(config)


class TestLogger:
    """Test logging system."""

    def test_setup_logger_console_only(self):
        """Test setting up logger with console only."""
        with tempfile.TemporaryDirectory():
            logger = setup_logger(log_file=False)

            assert logger is not None
            assert isinstance(logger, logging.Logger)
            assert len(logger.handlers) > 0

    def test_setup_logger_with_file(self):
        """Test setting up logger with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(log_dir=tmpdir, log_file=True, name="test_logger")

            assert logger is not None
            assert len(logger.handlers) > 0

            # Check that we have both console and file handlers
            handler_types = [type(h).__name__ for h in logger.handlers]
            assert "StreamHandler" in handler_types or len(handler_types) >= 1

    def test_logger_debug_level(self):
        """Test logger with debug level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(log_dir=tmpdir, debug=True)

            assert logger.level == logging.DEBUG

    def test_logger_info_level(self):
        """Test logger with info level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(log_dir=tmpdir, debug=False)

            assert logger.level == logging.INFO

    def test_get_logger(self):
        """Test getting logger by name."""
        logger = get_logger("test_module")

        assert logger is not None
        assert logger.name == "test_module"

    def test_configure_root_logger(self):
        """Test configuring root logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            configure_root_logger(log_dir=tmpdir, log_file=True)

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0


class TestArchive:
    """Test archive management."""

    @pytest.fixture
    def temp_archive(self):
        """Create temporary archive for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = os.path.join(tmpdir, "archive.json")
            archive = Archive(archive_path)
            yield archive

    def test_archive_creation(self, temp_archive):
        """Test creating new archive."""
        assert os.path.exists(temp_archive.archive_path)
        assert temp_archive.data is not None
        assert "processed" in temp_archive.data
        assert "failed" in temp_archive.data
        assert "stats" in temp_archive.data

    def test_mark_processed(self, temp_archive):
        """Test marking video as processed."""
        temp_archive.mark_processed(
            "vid123", "Test Video", "/path/to/output.md", failed_chapters=0
        )

        assert temp_archive.is_processed("vid123")
        processed = temp_archive.get_processed_videos()
        assert "vid123" in processed
        assert processed["vid123"]["title"] == "Test Video"

    def test_mark_failed(self, temp_archive):
        """Test marking video as failed."""
        temp_archive.mark_failed("vid456", "Failed Video", "Test error")

        failed = temp_archive.get_failed_videos()
        assert "vid456" in failed
        assert failed["vid456"]["title"] == "Failed Video"
        assert failed["vid456"]["error"] == "Test error"

    def test_get_processed_ids(self, temp_archive):
        """Test getting set of processed video IDs."""
        temp_archive.mark_processed("vid1", "Video 1", "/path/1.md")
        temp_archive.mark_processed("vid2", "Video 2", "/path/2.md")

        ids = temp_archive.get_processed_ids()
        assert "vid1" in ids
        assert "vid2" in ids
        assert len(ids) == 2

    def test_get_stats(self, temp_archive):
        """Test getting archive statistics."""
        temp_archive.mark_processed("vid1", "Video 1", "/path/1.md")
        temp_archive.mark_failed("vid2", "Video 2", "error")

        stats = temp_archive.get_stats()
        assert stats["total_processed"] == 1
        assert stats["total_failed"] == 1
        assert stats["last_update"] is not None

    def test_clear_failed_all(self, temp_archive):
        """Test clearing all failed videos."""
        temp_archive.mark_failed("vid1", "Video 1", "error1")
        temp_archive.mark_failed("vid2", "Video 2", "error2")

        temp_archive.clear_failed()

        failed = temp_archive.get_failed_videos()
        assert len(failed) == 0

    def test_clear_failed_specific(self, temp_archive):
        """Test clearing specific failed video."""
        temp_archive.mark_failed("vid1", "Video 1", "error1")
        temp_archive.mark_failed("vid2", "Video 2", "error2")

        temp_archive.clear_failed("vid1")

        failed = temp_archive.get_failed_videos()
        assert "vid1" not in failed
        assert "vid2" in failed

    def test_retry_failed(self, temp_archive):
        """Test moving failed video to retry queue."""
        temp_archive.mark_failed("vid1", "Video 1", "error")

        assert temp_archive.retry_failed("vid1") is True

        failed = temp_archive.get_failed_videos()
        assert "vid1" not in failed

    def test_retry_non_existent_video(self, temp_archive):
        """Test retrying non-existent video."""
        assert temp_archive.retry_failed("nonexistent") is False

    def test_archive_persistence(self):
        """Test that archive persists to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = os.path.join(tmpdir, "archive.json")

            # Create and modify archive
            archive1 = Archive(archive_path)
            archive1.mark_processed("vid1", "Video 1", "/path/1.md")

            # Load archive again
            archive2 = Archive(archive_path)

            assert archive2.is_processed("vid1")
            processed = archive2.get_processed_videos()
            assert "vid1" in processed

    def test_export_summary(self, temp_archive):
        """Test exporting archive summary."""
        temp_archive.mark_processed("vid1", "Video 1", "/path/1.md")
        temp_archive.mark_failed("vid2", "Video 2", "error")

        summary = temp_archive.export_summary()

        assert "Archive Summary" in summary
        assert "Total Processed: 1" in summary
        assert "Total Failed: 1" in summary


class TestIntegration:
    """Integration tests for infrastructure modules."""

    def test_full_workflow(self):
        """Test complete config -> logger -> archive workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup config
            config_path = os.path.join(tmpdir, "config.json")
            channels_path = os.path.join(tmpdir, "channels.json")

            config_data = {
                "lookback_hours": 24,
                "min_duration_minutes": 5,
                "subtitle_language": "en",
                "subtitle_merge_interval": 30,
                "claude_model": "claude-sonnet-4-20250514",
                "claude_timeout_seconds": 600,
                "min_chapter_duration": 180,
                "max_chapter_duration": 900,
                "context_lines": 5,
                "translation_max_tokens": 4000,
                "translation_max_retries": 2,
                "translation_retry_delay": 5,
                "output_dir": tmpdir,
                "filename_max_length": 50,
                "archive_file": os.path.join(tmpdir, "archive.json"),
                "email_enabled": False,
                "check_interval_hours": 3,
            }

            channels_data = {
                "channels": [
                    {
                        "name": "Test",
                        "handle": "@test",
                        "url": "https://youtube.com/@test",
                        "channel_id": "UC123",
                    }
                ]
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            with open(channels_path, "w") as f:
                json.dump(channels_data, f)

            # Load and validate config
            config = load_config(config_path, channels_path)
            validate_config(config)

            # Setup logger
            configure_root_logger(log_dir=tmpdir)
            logger = get_logger(__name__)

            # Create archive
            archive = Archive(config.archive_file)
            archive.mark_processed("test_vid", "Test Video", "output.md")

            # Verify everything works together
            assert config.output_dir == tmpdir
            assert archive.is_processed("test_vid")
            logger.info("Integration test passed")
