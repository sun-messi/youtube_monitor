"""Archive management for processed videos."""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set

logger = logging.getLogger(__name__)


@staticmethod
def _ensure_dict_structure(data: Dict) -> Dict:
    """Ensure archive data has required structure."""
    if "processed" not in data:
        data["processed"] = {}
    if "failed" not in data:
        data["failed"] = {}
    if "stats" not in data:
        data["stats"] = {
            "total_processed": 0,
            "total_failed": 0,
            "last_update": None,
        }
    return data


class Archive:
    """Manage archive of processed videos."""

    def __init__(self, archive_path: str = "youtube_archive.json"):
        """
        Initialize archive manager.

        Args:
            archive_path: Path to archive JSON file
        """
        self.archive_path = archive_path
        self._load()

    def _load(self) -> None:
        """Load archive from file or create new one."""
        if os.path.exists(self.archive_path):
            try:
                with open(self.archive_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    self.data = _ensure_dict_structure(self.data)
                logger.debug(f"Archive loaded: {self.archive_path}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid archive file, creating new one: {e}")
                self.data = {
                    "processed": {},
                    "failed": {},
                    "stats": {
                        "total_processed": 0,
                        "total_failed": 0,
                        "last_update": None,
                    },
                }
        else:
            logger.info(f"Creating new archive: {self.archive_path}")
            self.data = {
                "processed": {},
                "failed": {},
                "stats": {
                    "total_processed": 0,
                    "total_failed": 0,
                    "last_update": None,
                },
            }
            self._save()

    def _save(self) -> None:
        """Save archive to file."""
        try:
            with open(self.archive_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Archive saved: {self.archive_path}")
        except Exception as e:
            logger.error(f"Failed to save archive: {e}")
            raise

    def is_processed(self, video_id: str) -> bool:
        """
        Check if video was already processed.

        Args:
            video_id: YouTube video ID

        Returns:
            True if video is in processed list
        """
        return video_id in self.data["processed"]

    def mark_processed(
        self,
        video_id: str,
        title: str,
        output_path: str,
        failed_chapters: int = 0,
    ) -> None:
        """
        Mark video as successfully processed.

        Args:
            video_id: YouTube video ID
            title: Video title
            output_path: Path to generated markdown file
            failed_chapters: Number of failed translation chapters
        """
        self.data["processed"][video_id] = {
            "title": title,
            "output_path": output_path,
            "processed_at": datetime.now().isoformat(),
            "failed_chapters": failed_chapters,
        }

        # Update stats
        self.data["stats"]["total_processed"] = len(self.data["processed"])
        self.data["stats"]["last_update"] = datetime.now().isoformat()

        self._save()
        logger.info(f"Video marked as processed: {video_id} ({title})")

    def mark_failed(
        self, video_id: str, title: str, error: str, channel: Optional[str] = None
    ) -> None:
        """
        Mark video as failed.

        Args:
            video_id: YouTube video ID
            title: Video title
            error: Error message
            channel: Channel name (optional)
        """
        self.data["failed"][video_id] = {
            "title": title,
            "error": error,
            "channel": channel,
            "failed_at": datetime.now().isoformat(),
        }

        # Update stats
        self.data["stats"]["total_failed"] = len(self.data["failed"])
        self.data["stats"]["last_update"] = datetime.now().isoformat()

        self._save()
        logger.warning(f"Video marked as failed: {video_id} ({title}): {error}")

    def get_processed_videos(self) -> Dict[str, Dict]:
        """
        Get all processed videos.

        Returns:
            Dictionary of processed videos with metadata
        """
        return self.data["processed"]

    def get_failed_videos(self) -> Dict[str, Dict]:
        """
        Get all failed videos.

        Returns:
            Dictionary of failed videos with error info
        """
        return self.data["failed"]

    def get_processed_ids(self) -> Set[str]:
        """
        Get set of all processed video IDs.

        Returns:
            Set of video IDs
        """
        return set(self.data["processed"].keys())

    def get_stats(self) -> Dict:
        """
        Get archive statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_processed": len(self.data["processed"]),
            "total_failed": len(self.data["failed"]),
            "last_update": self.data["stats"]["last_update"],
        }

    def clear_failed(self, video_id: Optional[str] = None) -> None:
        """
        Clear failed videos from archive.

        Args:
            video_id: Specific video ID to clear, or None to clear all
        """
        if video_id:
            if video_id in self.data["failed"]:
                del self.data["failed"][video_id]
                logger.info(f"Cleared failed video: {video_id}")
        else:
            self.data["failed"] = {}
            logger.info("Cleared all failed videos")

        self.data["stats"]["total_failed"] = len(self.data["failed"])
        self._save()

    def retry_failed(self, video_id: str) -> bool:
        """
        Move video from failed to available for reprocessing.

        Args:
            video_id: YouTube video ID

        Returns:
            True if video was in failed list and removed
        """
        if video_id in self.data["failed"]:
            del self.data["failed"][video_id]
            self.data["stats"]["total_failed"] = len(self.data["failed"])
            self._save()
            logger.info(f"Video moved to retry queue: {video_id}")
            return True
        return False

    def export_summary(self) -> str:
        """
        Export archive summary as formatted string.

        Returns:
            Formatted summary text
        """
        stats = self.get_stats()
        summary = f"""
=== Archive Summary ===
Total Processed: {stats['total_processed']}
Total Failed: {stats['total_failed']}
Last Update: {stats['last_update']}

Processed Videos: {len(self.get_processed_videos())}
Failed Videos: {len(self.get_failed_videos())}
"""
        return summary
