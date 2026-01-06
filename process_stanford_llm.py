#!/usr/bin/env python3
"""
Stanford LLM Course Playlist Processor

Extracts video IDs from Stanford's LLM course playlist and processes them
sequentially using main.py, with 30-minute intervals between videos.

Usage:
    python process_stanford_llm.py
"""

import subprocess
import time
import sys
import logging
from datetime import datetime, timedelta
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PLAYLIST_URL = "https://youtube.com/playlist?list=PLoROMvodv4rOCXd21gf0CF4xr35yINeOy"
WAIT_TIME_MINUTES = 300  # 5 hours = 300 minutes
WAIT_TIME_SECONDS = WAIT_TIME_MINUTES * 60


def extract_video_ids(playlist_url: str) -> List[str]:
    """
    Extract video IDs from YouTube playlist using yt-dlp.

    Args:
        playlist_url: YouTube playlist URL

    Returns:
        List of video IDs in playlist order
    """
    logger.info(f"Extracting video IDs from playlist...")

    try:
        result = subprocess.run(
            [
                'yt-dlp',
                '--flat-playlist',
                '--print', '%(id)s',
                playlist_url
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"yt-dlp failed: {result.stderr}")
            sys.exit(1)

        video_ids = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        logger.info(f"Found {len(video_ids)} videos in playlist")

        return video_ids

    except subprocess.TimeoutExpired:
        logger.error("Playlist extraction timed out")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("yt-dlp not found. Please install: pip install yt-dlp")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def process_video(video_id: str) -> bool:
    """
    Process a single video using main.py.

    Args:
        video_id: YouTube video ID

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing video: {video_id}")
    logger.info(f"  URL: https://www.youtube.com/watch?v={video_id}")

    try:
        result = subprocess.run(
            ['python', 'main.py', '--video', video_id, '--channel', 'academic'],
            capture_output=False,  # Show output in real-time
            text=True
        )

        if result.returncode == 0:
            logger.info(f"✅ Successfully processed: {video_id}")
            return True
        else:
            logger.error(f"❌ Failed to process: {video_id} (exit code: {result.returncode})")
            return False

    except Exception as e:
        logger.error(f"❌ Error processing {video_id}: {e}")
        return False


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Stanford LLM Course Playlist Processor")
    logger.info("=" * 60)
    logger.info(f"Playlist: {PLAYLIST_URL}")
    logger.info(f"Wait time between videos: {WAIT_TIME_MINUTES} minutes (5 hours)")
    logger.info("Starting from: Lecture 3 (skipping Lecture 1 & 2)")
    logger.info("=" * 60)

    # Step 1: Extract video IDs
    video_ids = extract_video_ids(PLAYLIST_URL)

    if not video_ids:
        logger.warning("No videos found in playlist")
        sys.exit(1)

    # Step 2: Process each video (skip first two videos, start from Lecture 3)
    logger.info("⏭️  Skipping first two videos (Lecture 1 & 2)")
    video_ids = video_ids[2:]  # Skip first two videos
    total = len(video_ids)
    successful = 0
    failed = 0

    for i, video_id in enumerate(video_ids, 1):
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Video {i}/{total}: {video_id}")
        logger.info("=" * 60)

        # Process video
        success = process_video(video_id)

        if success:
            successful += 1
        else:
            failed += 1

        # Wait before next video (except for last one)
        if i < total:
            logger.info("")
            logger.info(f"⏳ Waiting {WAIT_TIME_MINUTES} minutes before next video...")
            next_time = datetime.now() + timedelta(minutes=WAIT_TIME_MINUTES)
            logger.info(f"   Next video will start at: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   Press Ctrl+C to stop")

            try:
                time.sleep(WAIT_TIME_SECONDS)
            except KeyboardInterrupt:
                logger.warning("\n⚠️  Process interrupted by user")
                logger.info(f"Progress: {successful} succeeded, {failed} failed, {total - i} remaining")
                sys.exit(0)

    # Step 3: Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total videos: {total}")
    logger.info(f"✅ Successful: {successful}")
    logger.info(f"❌ Failed: {failed}")
    logger.info("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Process interrupted by user")
        sys.exit(0)
