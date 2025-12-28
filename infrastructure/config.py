"""Configuration management for YouTube Monitor & Translator system."""

from dataclasses import dataclass
from typing import List, Dict, Any
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChannelConfig:
    """YouTube channel configuration."""

    name: str
    handle: str
    url: str
    channel_id: str


@dataclass
class Config:
    """System configuration data class."""

    # Video discovery
    lookback_hours: int
    min_duration_minutes: int
    subtitle_language: str

    # Subtitle processing
    subtitle_merge_interval: int

    # AI configuration
    claude_model: str
    claude_timeout_seconds: int

    # Chapter optimization
    min_chapter_duration: int
    max_chapter_duration: int

    # Translation configuration
    context_lines: int
    translation_max_tokens: int
    translation_max_retries: int
    translation_retry_delay: int

    # Output configuration
    output_dir: str
    filename_max_length: int
    archive_file: str

    # Email notification
    email_enabled: bool

    # Scheduling
    check_interval_hours: int

    # Agent configuration
    use_agent: bool
    agent_name: str

    # Review configuration
    review_enabled: bool
    review_remove_ai_garbage: bool

    # Channel list
    channels: List[ChannelConfig]


def load_config(
    config_path: str = "config_ai.json", channels_path: str = "channels.json"
) -> Config:
    """
    Load configuration from JSON files.

    Args:
        config_path: Path to config_ai.json
        channels_path: Path to channels.json

    Returns:
        Config object with all settings

    Raises:
        FileNotFoundError: If config files not found
        json.JSONDecodeError: If JSON is invalid
        ValueError: If required fields are missing
    """
    logger.debug(f"Loading config from {config_path}")

    # Load main configuration
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {config_path}: {e}")
        raise

    # Load channels configuration
    try:
        with open(channels_path, "r", encoding="utf-8") as f:
            channels_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Channels file not found: {channels_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {channels_path}: {e}")
        raise

    # Parse channels
    channels = []
    for ch in channels_data.get("channels", []):
        try:
            channels.append(
                ChannelConfig(
                    name=ch["name"],
                    handle=ch["handle"],
                    url=ch["url"],
                    channel_id=ch["channel_id"],
                )
            )
        except KeyError as e:
            logger.warning(f"Skipping invalid channel config: missing {e}")
            continue

    if not channels:
        logger.warning("No valid channels found in channels.json")

    # Create Config object
    try:
        config = Config(
            lookback_hours=config_data["lookback_hours"],
            min_duration_minutes=config_data["min_duration_minutes"],
            subtitle_language=config_data["subtitle_language"],
            subtitle_merge_interval=config_data["subtitle_merge_interval"],
            claude_model=config_data["claude_model"],
            claude_timeout_seconds=config_data["claude_timeout_seconds"],
            min_chapter_duration=config_data["min_chapter_duration"],
            max_chapter_duration=config_data["max_chapter_duration"],
            context_lines=config_data["context_lines"],
            translation_max_tokens=config_data["translation_max_tokens"],
            translation_max_retries=config_data["translation_max_retries"],
            translation_retry_delay=config_data["translation_retry_delay"],
            output_dir=config_data["output_dir"],
            filename_max_length=config_data["filename_max_length"],
            archive_file=config_data["archive_file"],
            email_enabled=config_data.get("email_enabled", False),
            check_interval_hours=config_data.get("check_interval_hours", 0),
            use_agent=config_data.get("use_agent", False),
            agent_name=config_data.get("agent_name", "tech-investment-analyst"),
            review_enabled=config_data.get("review_enabled", False),
            review_remove_ai_garbage=config_data.get("review_remove_ai_garbage", False),
            channels=channels,
        )

        logger.info(
            f"Config loaded: {len(channels)} channels, "
            f"model={config.claude_model}, "
            f"use_agent={config.use_agent}"
        )
        return config

    except KeyError as e:
        logger.error(f"Missing required config field: {e}")
        raise ValueError(f"Missing required config field: {e}")


def validate_config(config: Config) -> bool:
    """
    Validate configuration values.

    Args:
        config: Config object to validate

    Returns:
        True if all values are valid

    Raises:
        ValueError: If any value is invalid
    """
    errors = []

    # Validate numeric fields
    if config.lookback_hours <= 0:
        errors.append("lookback_hours must be positive")

    if config.min_duration_minutes <= 0:
        errors.append("min_duration_minutes must be positive")

    if config.subtitle_merge_interval <= 0:
        errors.append("subtitle_merge_interval must be positive")

    if config.claude_timeout_seconds <= 0:
        errors.append("claude_timeout_seconds must be positive")


    if config.min_chapter_duration <= 0:
        errors.append("min_chapter_duration must be positive")

    if config.max_chapter_duration <= config.min_chapter_duration:
        errors.append(
            "max_chapter_duration must be greater than min_chapter_duration"
        )

    if config.context_lines < 0:
        errors.append("context_lines must be non-negative")

    if config.translation_max_tokens <= 0:
        errors.append("translation_max_tokens must be positive")

    if config.translation_max_retries < 0:
        errors.append("translation_max_retries must be non-negative")

    if config.translation_retry_delay < 0:
        errors.append("translation_retry_delay must be non-negative")

    if config.filename_max_length <= 0:
        errors.append("filename_max_length must be positive")

    if config.check_interval_hours < 0:
        errors.append("check_interval_hours must be non-negative")

    # Validate string fields
    if not config.subtitle_language:
        errors.append("subtitle_language must not be empty")

    if not config.claude_model:
        errors.append("claude_model must not be empty")


    if not config.output_dir:
        errors.append("output_dir must not be empty")

    if not config.archive_file:
        errors.append("archive_file must not be empty")

    # Validate channels
    if not config.channels:
        errors.append("At least one channel must be configured")

    if errors:
        error_msg = "Config validation failed: " + "; ".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug("Config validation passed")
    return True
