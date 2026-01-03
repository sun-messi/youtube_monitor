#!/usr/bin/env python3
"""
Main Entry Point - YouTube Monitor & Translator.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py

Automated YouTube video monitoring and translation system.
Supports single-video, batch, and continuous monitoring modes.
"""

import argparse
import sys
import logging
import time
from pathlib import Path
from typing import List, Optional

# Log file path
LOG_FILE = Path("/home/sunj11/projects/youtube-monitor-translator/output.log")

# Setup logging to both console and file
def setup_logging():
    """Configure logging to output to both console and file."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)

    # File handler (append mode)
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)

    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()


def load_config():
    """Load configuration from config_ai.json."""
    import json
    from dataclasses import dataclass, field
    from typing import List

    @dataclass
    class Config:
        lookback_hours: int = 20
        min_duration_minutes: int = 10
        subtitle_language: str = "en"
        subtitle_merge_interval: int = 30
        claude_model: str = "claude-sonnet-4-20250514"
        claude_timeout_seconds: int = 600
        min_chapter_duration: int = 180
        max_chapter_duration: int = 900
        context_lines: int = 5
        translation_max_tokens: int = 4000
        translation_max_retries: int = 2
        translation_retry_delay: int = 5
        output_dir: str = "./ai_output"
        filename_max_length: int = 50
        archive_file: str = "./youtube_archive.json"
        email_enabled: bool = False
        check_interval_hours: int = 3
        channels: List = field(default_factory=list)
        # Review module config
        review_enabled: bool = True
        review_remove_ai_garbage: bool = True

    try:
        with open("config_ai.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        logger.warning("config_ai.json not found, using defaults")
        config_data = {}

    try:
        with open("channels.json", "r", encoding="utf-8") as f:
            channels_data = json.load(f)
            config_data['channels'] = channels_data.get('channels', [])
    except FileNotFoundError:
        logger.warning("channels.json not found")
        config_data['channels'] = []

    return Config(**{k: v for k, v in config_data.items() if hasattr(Config, k) or k == 'channels'})


def load_archive(archive_file: str):
    """Load or create archive for tracking processed videos."""
    import json
    from dataclasses import dataclass
    from datetime import datetime

    @dataclass
    class Archive:
        file_path: str
        data: dict = None

        def __post_init__(self):
            self.data = self._load()

        def _load(self):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:  # Empty file
                        return {}
                    return json.loads(content)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

        def _save(self):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

        def is_processed(self, video_id: str) -> bool:
            return video_id in self.data

        def mark_processed(self, video_id: str, title: str, output_path: str, failed_count: int = 0):
            self.data[video_id] = {
                "title": title,
                "output_file": output_path,
                "processed_at": datetime.now().isoformat(),
                "failed_chapters": failed_count
            }
            self._save()

        def mark_skipped(self, video_id: str, title: str, reason: str):
            self.data[video_id] = {
                "title": title,
                "skipped": True,
                "skip_reason": reason,
                "processed_at": datetime.now().isoformat()
            }
            self._save()

        def get_processed_ids(self):
            return set(self.data.keys())

    return Archive(archive_file)


def process_single_video(video_id: str, config, archive) -> int:
    """
    Process a single video (skips duration and date filters).

    Args:
        video_id: YouTube video ID
        config: Config object
        archive: Archive object

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from core.pipeline import process_video
    from infrastructure.notifier import send_update_email

    logger.info(f"Processing single video: {video_id}")
    logger.info(f"(skip_filters=True: ignoring duration/date limits)")
    logger.info("-" * 60)

    result = process_video(video_id, config, archive, skip_filters=True)

    if result.success:
        if result.output_path:
            logger.info(f"Video processed successfully")
            logger.info(f"   Output: {result.output_path}")
            logger.info(f"   Time: {result.processing_time:.1f}s")

            # Send email notification
            video_info = {
                'file_path': result.output_path,
                'channel': result.channel,
                'title': result.title,
                'url': f'https://www.youtube.com/watch?v={video_id}'
            }
            if send_update_email([video_info]):
                logger.info(f"   Email sent successfully")
            else:
                logger.warning(f"   Email sending failed")
        else:
            logger.info(f"Video skipped: {result.error}")
        return 0
    else:
        logger.error(f"Video processing failed")
        logger.error(f"   Stage: {result.stage_failed}")
        logger.error(f"   Error: {result.error}")
        return 1


def process_batch(config, archive, email_enabled: bool = False) -> int:
    """
    Process all new videos from configured channels.

    Args:
        config: Config object
        archive: Archive object
        email_enabled: Whether to send email notifications

    Returns:
        int: Exit code
    """
    from core.pipeline import run_pipeline

    logger.info("Processing batch of videos")
    logger.info("-" * 60)

    successful, failed = run_pipeline(config, archive, email_enabled=email_enabled)

    return 1 if failed else 0


def run_loop(email_enabled: bool = True) -> int:
    """
    Run continuous monitoring loop.
    Config and channels are reloaded on each iteration.

    Args:
        email_enabled: Whether to send email notifications

    Returns:
        int: Exit code
    """
    from core.pipeline import run_loop as pipeline_loop

    logger.info("Starting continuous monitoring mode")
    logger.info("Config and channels will be reloaded each iteration")
    logger.info("Press Ctrl+C to stop")
    logger.info("-" * 60)

    try:
        pipeline_loop(email_enabled=email_enabled)
        return 0
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error in monitoring loop: {e}")
        return 1


def main() -> int:
    """
    Main entry point with CLI argument parsing.

    Returns:
        int: Exit code
    """
    parser = argparse.ArgumentParser(
        description="YouTube Monitor & Translator - Automated video processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single video
  python main.py --video dQw4w9WgXcQ

  # Process all new videos
  python main.py

  # Continuous monitoring
  python main.py --loop
  nohup python main.py --loop >> output.log 2>&1 &
    # To stop the loop (Linux)
  pkill -f "main.py --loop"

  # With email notification
  python main.py --email
        """,
    )

    parser.add_argument(
        "--video",
        metavar="VIDEO_ID",
        help="Process single video by ID",
    )

    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuous monitoring",
    )

    parser.add_argument(
        "--email",
        action="store_true",
        help="Enable email notifications",
    )

    args = parser.parse_args()

    # Load configuration
    logger.info("YouTube Monitor & Translator")
    logger.info("=" * 60)

    try:
        config = load_config()
        logger.info(f"Loaded config: {len(config.channels)} channels")

        archive = load_archive(config.archive_file)
        logger.info(f"Loaded archive: {len(archive.data)} entries")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return 1

    # Execute appropriate mode
    try:
        if args.video:
            return process_single_video(args.video, config, archive)
        elif args.loop:
            # Loop mode defaults to sending email (use --no-email to disable)
            return run_loop(email_enabled=True)
        else:
            return process_batch(config, archive, email_enabled=args.email)

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
