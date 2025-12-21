"""
Video discovery from YouTube channel RSS feeds.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py
"""

import subprocess
import json
import logging
import re
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

try:
    import feedparser
except ImportError:
    raise ImportError("feedparser not installed. Run: pip install feedparser")

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Basic YouTube video information from RSS feed."""
    video_id: str
    title: str
    published: str
    url: str
    channel: str


def get_channel_id(channel: dict, channels_file: Optional[Path] = None) -> str:
    """
    Get channel ID, extracting via yt-dlp if not cached.

    Args:
        channel: Channel dict with name, url, handle, channel_id
        channels_file: Path to channels.json for caching

    Returns:
        YouTube channel ID string
    """
    if channel.get("channel_id"):
        return channel["channel_id"]

    url = channel.get("url", "")
    if not url:
        return ""

    logger.info(f"Extracting channel ID for: {channel.get('name', url)}")

    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "channel_id", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            channel_id = result.stdout.strip().split('\n')[0]
            # Cache the channel ID
            if channels_file and channel.get("handle"):
                _update_channel_id_cache(channels_file, channel["handle"], channel_id)
            return channel_id
    except Exception as e:
        logger.error(f"Failed to extract channel ID: {e}")

    return ""


def _update_channel_id_cache(channels_file: Path, handle: str, channel_id: str) -> None:
    """Update channel ID in channels.json cache."""
    if not handle or not channel_id:
        return

    try:
        with open(channels_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for ch in data.get("channels", []):
            if ch.get("handle") == handle:
                ch["channel_id"] = channel_id
                break

        with open(channels_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Could not update channel ID cache: {e}")


def get_rss_url(channel: dict, channels_file: Optional[Path] = None) -> str:
    """
    Get RSS feed URL for a channel.

    Args:
        channel: Channel dict
        channels_file: Path to channels.json for ID caching

    Returns:
        RSS feed URL string
    """
    channel_id = get_channel_id(channel, channels_file)
    if channel_id:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    return ""


def get_channel_rss_url(channel_id: str) -> str:
    """
    Get RSS feed URL for YouTube channel by ID.

    Args:
        channel_id: YouTube channel ID

    Returns:
        RSS feed URL
    """
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def fetch_channel_videos_rss(channel: dict, lookback_hours: int,
                              channels_file: Optional[Path] = None) -> List[VideoInfo]:
    """
    Fetch recent videos from channel RSS feed.

    Args:
        channel: Channel dict with name, url, channel_id, etc.
        lookback_hours: Only return videos within this window
        channels_file: Path to channels.json for ID caching

    Returns:
        List of VideoInfo objects
    """
    rss_url = get_rss_url(channel, channels_file)
    if not rss_url:
        logger.warning(f"No RSS URL for channel: {channel.get('name')}")
        return []

    logger.info(f"Fetching RSS: {channel.get('name')}")

    try:
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            logger.warning(f"RSS parse error for {channel.get('name')}: {feed.bozo_exception}")

        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        videos = []

        for entry in feed.entries:
            # Parse published date
            published_str = entry.get('published', '')
            try:
                # Format: 2025-12-15T12:00:00+00:00
                published = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                )
                if published.replace(tzinfo=None) < cutoff:
                    continue
            except Exception:
                pass  # Include if date parsing fails

            # Extract video ID
            video_id = getattr(entry, 'yt_videoid', None)
            if not video_id:
                # Try to extract from link
                link = entry.get('link', '')
                if 'v=' in link:
                    video_id = link.split('v=')[-1].split('&')[0]

            if not video_id:
                continue

            videos.append(VideoInfo(
                video_id=video_id,
                title=entry.get('title', 'Untitled'),
                published=published_str,
                url=f"https://www.youtube.com/watch?v={video_id}",
                channel=channel.get("name", "Unknown")
            ))

        logger.info(f"  Found {len(videos)} videos within lookback window")
        return videos

    except Exception as e:
        logger.error(f"RSS fetch error for {channel.get('name')}: {e}")
        return []


def fetch_channel_videos(channel_id: str, lookback_hours: int = 24) -> List[str]:
    """
    Fetch recent video IDs from YouTube channel RSS feed.

    Args:
        channel_id: YouTube channel ID
        lookback_hours: How many hours to look back

    Returns:
        List of video IDs
    """
    rss_url = get_channel_rss_url(channel_id)

    try:
        logger.info(f"Fetching RSS feed for channel {channel_id}")
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            logger.warning(f"RSS parsing issues for {channel_id}: {feed.bozo_exception}")

        if not feed.entries:
            logger.warning(f"No entries found in feed for {channel_id}")
            return []

        video_ids = []
        cutoff = datetime.now() - timedelta(hours=lookback_hours)

        for entry in feed.entries:
            try:
                # Extract video ID
                video_id = getattr(entry, 'yt_videoid', None)
                if not video_id:
                    video_id = entry.id.split("yt:video:")[-1]

                # Check published date
                published_str = entry.get('published', '')
                try:
                    published = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    )
                    if published.replace(tzinfo=None) < cutoff:
                        logger.debug(f"Skipping old video: {video_id}")
                        continue
                except Exception:
                    pass  # Include if date parsing fails

                video_ids.append(video_id)

            except Exception as e:
                logger.warning(f"Failed to parse RSS entry: {e}")
                continue

        logger.info(f"Found {len(video_ids)} recent videos in {channel_id}")
        return video_ids

    except Exception as e:
        logger.error(f"Failed to fetch RSS feed for {channel_id}: {e}")
        raise


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.

    Args:
        url: YouTube URL or video ID

    Returns:
        Video ID or None if invalid

    Examples:
        >>> extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
    """
    if "v=" in url:
        # https://www.youtube.com/watch?v=VIDEO_ID
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        # https://youtu.be/VIDEO_ID
        return url.split("youtu.be/")[-1].split("?")[0]
    elif re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        # Already a video ID
        return url

    logger.warning(f"Could not extract video ID from: {url}")
    return None


def construct_video_url(video_id: str) -> str:
    """
    Construct YouTube video URL from video ID.

    Args:
        video_id: YouTube video ID

    Returns:
        YouTube URL
    """
    return f"https://www.youtube.com/watch?v={video_id}"


def filter_new_videos(video_ids: List[str], archive) -> List[str]:
    """
    Filter out already-processed videos using archive.

    Args:
        video_ids: List of video IDs to check
        archive: Archive object or dict to check against

    Returns:
        List of new (unprocessed) video IDs
    """
    # Support both Archive object and dict
    if hasattr(archive, 'get_processed_ids'):
        processed = archive.get_processed_ids()
    elif hasattr(archive, 'is_processed'):
        processed = set()
        for vid in video_ids:
            if archive.is_processed(vid):
                processed.add(vid)
    else:
        # Assume dict
        processed = set(archive.keys())

    new_videos = [vid for vid in video_ids if vid not in processed]

    if new_videos:
        logger.info(f"Found {len(new_videos)} new videos (skipped {len(video_ids) - len(new_videos)})")
    else:
        logger.info("No new videos found")

    return new_videos


def filter_new_videos_rss(videos: List[VideoInfo], archive) -> List[VideoInfo]:
    """
    Filter out already-processed videos from VideoInfo list.

    Args:
        videos: List of VideoInfo objects
        archive: Archive object or dict

    Returns:
        List of new VideoInfo objects
    """
    # Support both Archive object and dict
    if hasattr(archive, 'is_processed'):
        new_videos = [v for v in videos if not archive.is_processed(v.video_id)]
    else:
        # Assume dict
        new_videos = [v for v in videos if v.video_id not in archive]

    if new_videos:
        logger.info(f"Found {len(new_videos)} new videos (skipped {len(videos) - len(new_videos)})")
    else:
        logger.info("No new videos found")

    return new_videos


def fetch_and_filter_videos(
    channel_id: str,
    archive,
    lookback_hours: int = 24,
    min_duration_minutes: int = 10,
) -> List[str]:
    """
    Complete video discovery workflow.

    Args:
        channel_id: YouTube channel ID
        archive: Archive object for tracking processed videos
        lookback_hours: How many hours to look back
        min_duration_minutes: Minimum video duration (filtering done later)

    Returns:
        List of unprocessed video IDs
    """
    try:
        # Fetch all recent videos
        all_videos = fetch_channel_videos(channel_id, lookback_hours)

        # Filter new videos
        new_videos = filter_new_videos(all_videos, archive)

        logger.info(
            f"Channel {channel_id}: "
            f"{len(all_videos)} recent, {len(new_videos)} new"
        )

        return new_videos

    except Exception as e:
        logger.error(f"Video discovery failed for {channel_id}: {e}")
        raise
