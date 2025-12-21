"""
Video content fetching using yt-dlp.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py
"""

import subprocess
import json
import os
import re
import glob
import logging
from typing import Optional, Tuple, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Video metadata from yt-dlp."""
    video_id: str
    title: str
    channel: str
    upload_date: str  # YYYYMMDD
    duration_sec: int
    description: str
    url: str


def get_video_info(youtube_url: str) -> Tuple[str, str, str]:
    """
    Get video title, channel name, and upload date.

    Args:
        youtube_url: YouTube video URL or video ID

    Returns:
        Tuple of (channel, title, upload_date)
    """
    # Ensure it's a full URL
    if not youtube_url.startswith("http"):
        youtube_url = f"https://www.youtube.com/watch?v={youtube_url}"

    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s\n%(channel)s\n%(upload_date)s", youtube_url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            title = lines[0] if len(lines) > 0 else ""
            channel = lines[1] if len(lines) > 1 else ""
            upload_date = lines[2] if len(lines) > 2 else ""  # Format: YYYYMMDD
            return channel, title, upload_date
        return "", "", ""
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return "", "", ""


def fetch_video_info(video_id: str) -> Optional[VideoMetadata]:
    """
    Get video metadata using yt-dlp.

    Args:
        video_id: YouTube video ID

    Returns:
        VideoMetadata object or None if failed
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        logger.debug(f"Fetching metadata for {video_id}")

        # Use yt-dlp to extract metadata (JSON format for complete info)
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-warnings",
            "--quiet",
            url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            # Fallback to simpler method
            channel, title, upload_date = get_video_info(video_id)
            if title:
                return VideoMetadata(
                    video_id=video_id,
                    title=title,
                    channel=channel,
                    upload_date=upload_date,
                    duration_sec=0,
                    description="",
                    url=url,
                )
            logger.warning(f"yt-dlp failed for {video_id}: {result.stderr}")
            return None

        data = json.loads(result.stdout)

        metadata = VideoMetadata(
            video_id=video_id,
            title=data.get("title", "Unknown"),
            channel=data.get("channel", data.get("uploader", "Unknown")),
            upload_date=data.get("upload_date", ""),
            duration_sec=data.get("duration", 0),
            description=data.get("description", ""),
            url=url,
        )

        logger.debug(f"Got metadata: {metadata.title[:50]}... ({metadata.duration_sec}s)")
        return metadata

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout fetching metadata for {video_id}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response for {video_id}: {e}")
        # Fallback to simpler method
        channel, title, upload_date = get_video_info(video_id)
        if title:
            return VideoMetadata(
                video_id=video_id,
                title=title,
                channel=channel,
                upload_date=upload_date,
                duration_sec=0,
                description="",
                url=f"https://www.youtube.com/watch?v={video_id}",
            )
        return None
    except Exception as e:
        logger.error(f"Failed to get video info for {video_id}: {e}")
        return None


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """
    Clean filename, remove illegal characters including Unicode quotes.

    Args:
        title: Original title
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove ASCII and Unicode problematic characters (including smart quotes)
    title = re.sub(r'[<>:"/\\|?*""''`'']', '', title)
    title = title.replace(' ', '_')
    if len(title) > max_length:
        title = title[:max_length]
    return title


def download_subtitle(youtube_url: str, output_dir: Path, language: str = "en") -> Tuple[Optional[str], Optional[str]]:
    """
    Download YouTube subtitle.

    Args:
        youtube_url: YouTube video URL or video ID
        output_dir: Directory to save subtitle
        language: Subtitle language code

    Returns:
        (srt_file_path, raw_srt_text) or (None, None) if failed
    """
    # Ensure it's a full URL
    if not youtube_url.startswith("http"):
        video_id = youtube_url
        youtube_url = f"https://www.youtube.com/watch?v={youtube_url}"
    else:
        video_id = youtube_url.split("v=")[-1].split("&")[0] if "v=" in youtube_url else youtube_url

    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_template = str(output_dir / video_id)

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", language,
        "--sub-format", "srt",
        "--convert-subs", "srt",
        "-o", temp_template,
        youtube_url
    ]

    logger.info(f"Downloading subtitle...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            logger.warning(f"yt-dlp error: {result.stderr}")
            return None, None

        # Find the downloaded file
        possible_files = [
            output_dir / f"{video_id}.{language}.srt",
            output_dir / f"{video_id}.srt",
        ]

        srt_file = None
        for f in possible_files:
            if f.exists():
                srt_file = f
                break

        if not srt_file:
            # Try glob
            matches = glob.glob(str(output_dir / f"{video_id}*.srt"))
            if matches:
                srt_file = Path(matches[0])

        if not srt_file:
            logger.warning("No subtitle file found")
            return None, None

        with open(srt_file, "r", encoding="utf-8") as f:
            raw_srt = f.read()

        logger.info(f"Subtitle downloaded: {srt_file.name}")
        return str(srt_file), raw_srt

    except subprocess.TimeoutExpired:
        logger.error("Subtitle download timed out")
        return None, None
    except Exception as e:
        logger.error(f"Subtitle download error: {e}")
        return None, None


def download_subtitles(
    video_id: str, language: str = "en", output_dir: str = "downloads"
) -> Optional[str]:
    """
    Download subtitles for video using yt-dlp (compatibility wrapper).

    Args:
        video_id: YouTube video ID
        language: Subtitle language code
        output_dir: Directory to save subtitles

    Returns:
        Path to downloaded subtitle file or None if failed
    """
    srt_path, _ = download_subtitle(video_id, Path(output_dir), language)
    return srt_path


def check_video_availability(video_id: str) -> bool:
    """
    Check if video is available and downloadable.

    Args:
        video_id: YouTube video ID

    Returns:
        True if video is available
    """
    metadata = fetch_video_info(video_id)
    if metadata is None:
        logger.warning(f"Video {video_id} is not available")
        return False

    logger.debug(f"Video {video_id} is available")
    return True


def verify_subtitle_file(file_path: str) -> bool:
    """
    Verify subtitle file is valid and readable.

    Args:
        file_path: Path to subtitle file

    Returns:
        True if valid
    """
    if not os.path.exists(file_path):
        logger.warning(f"Subtitle file not found: {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(1000)  # Read first 1KB

        if not content:
            logger.warning(f"Subtitle file is empty: {file_path}")
            return False

        logger.debug(f"Subtitle file is valid: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to verify subtitle file: {e}")
        return False


def get_video_duration_from_srt(srt_entries: List[Tuple[int, int, str]]) -> int:
    """
    Get video duration from SRT entries.

    Args:
        srt_entries: List of (start_sec, end_sec, text) tuples

    Returns:
        Duration in seconds
    """
    if not srt_entries:
        return 0
    return srt_entries[-1][1]  # end time of last entry
