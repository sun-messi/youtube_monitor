"""
Pipeline Module - Orchestrates the complete video processing workflow.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime
import logging
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of processing a single video."""
    video_id: str
    success: bool
    title: str
    channel: str
    output_path: Optional[str]
    error: Optional[str]
    stage_failed: Optional[str]
    processing_time: float


def process_video(
    video_id: str,
    config,
    archive,
    prompts_dir: Optional[Path] = None,
    skip_filters: bool = False,
    channel_config: Optional['ChannelConfig'] = None
) -> PipelineResult:
    """
    Process a single video through the complete pipeline.

    Stages:
    1. Fetch video info (metadata)
    2. Download subtitles
    3. Process subtitles
    4. Analyze with Claude CLI (summary, chapters)
    5. Translate chapters
    6. Generate markdown output
    7. Archive result

    Args:
        video_id: YouTube video ID
        config: Config object with system settings
        archive: Archive object for tracking processed videos
        prompts_dir: Path to prompts directory (default: ./prompts)
        skip_filters: If True, skip duration and date filters (for --video mode)

    Returns:
        PipelineResult with processing outcome
    """
    from core.content_fetcher import fetch_video_info, download_subtitle, sanitize_filename
    from core.subtitle_processor import process_subtitle_file, check_minimum_duration, get_duration_from_entries
    from core.ai_analyzer import generate_summary, analyze_video, parse_chapters_from_summary, detect_video_type, extract_speakers
    from core.translator import translate_chapters
    from core.output_generator import generate_markdown, save_output
    from utils.srt_parser import parse_srt

    start_time = datetime.now()

    # Default prompts directory
    if prompts_dir is None:
        prompts_dir = Path("./prompts")

    # 🎯 Prompt selection logic based on channel tags
    is_academic = False
    use_agent_override = None

    # Check if academic channel (handle both ChannelConfig objects and dicts)
    def check_is_academic(cfg):
        if cfg is None:
            return False
        if hasattr(cfg, 'is_academic'):
            return cfg.is_academic()
        # It's a dict
        tags = cfg.get('tags', []) or []
        return 'academic' in tags

    if channel_config and check_is_academic(channel_config):
        # Academic channel: use academic prompts, force disable agent
        prompt_summary = prompts_dir / "yt-summary-academic.md"
        prompt_translate = prompts_dir / "yt-translate-academic.md"
        is_academic = True
        use_agent_override = False  # Force disable agent for academic content
        tags = channel_config.tags if hasattr(channel_config, 'tags') else channel_config.get('tags', [])
        logger.info(f"[{video_id}] 检测到学术频道 tags={tags}，使用学术 prompts")
    else:
        # Default: use investment/general prompts
        prompt_summary = prompts_dir / "yt-summary.md"
        prompt_translate = prompts_dir / "yt-translate.md"

    # Fallback mechanism: if prompt file doesn't exist, use default
    if not prompt_summary.exists():
        logger.warning(f"Prompt not found: {prompt_summary}, falling back to default")
        prompt_summary = prompts_dir / "yt-summary.md"
    if not prompt_translate.exists():
        logger.warning(f"Prompt not found: {prompt_translate}, falling back to default")
        prompt_translate = prompts_dir / "yt-translate.md"

    logger.info(f"[{video_id}] Starting pipeline processing...")

    try:
        # Stage 1: Fetch video info
        logger.info(f"[{video_id}] Stage 1: Fetching video information...")
        video_info = fetch_video_info(video_id)
        if not video_info:
            return _create_failed_result(video_id, "Failed to fetch video info", "video_info", start_time)

        logger.info(f"[{video_id}] ✓ Got video: {video_info.title}")

        # Stage 2: Download subtitles
        logger.info(f"[{video_id}] Stage 2: Downloading subtitles...")
        output_dir = Path(config.output_dir)
        srt_dir = output_dir / "srt" / sanitize_filename(video_info.channel)
        srt_path, raw_srt = download_subtitle(video_id, srt_dir, config.subtitle_language)

        if not srt_path or not raw_srt:
            return _create_failed_result(video_id, "Failed to download subtitles", "subtitle_download", start_time, video_info.title)

        logger.info(f"[{video_id}] ✓ Downloaded subtitles: {srt_path}")

        # Check minimum duration (skip if skip_filters is True)
        srt_entries = parse_srt(raw_srt)
        is_long_enough, duration_str = check_minimum_duration(srt_entries, config.min_duration_minutes)

        if not is_long_enough and not skip_filters:
            logger.info(f"[{video_id}] Skipping: duration {duration_str} < minimum {config.min_duration_minutes} min")
            archive.mark_skipped(video_id, video_info.title, f"Duration too short: {duration_str}")
            return PipelineResult(
                video_id=video_id,
                success=True,  # Not a failure, just skipped
                title=video_info.title,
                channel=video_info.channel,
                output_path=None,
                error=f"Skipped: duration too short ({duration_str})",
                stage_failed=None,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        elif not is_long_enough and skip_filters:
            logger.info(f"[{video_id}] Duration {duration_str} < minimum, but skip_filters=True, continuing...")

        # Stage 3: Process subtitles
        logger.info(f"[{video_id}] Stage 3: Processing subtitles...")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        subtitle_data = process_subtitle_file(
            srt_path,
            title=video_info.title,
            channel=video_info.channel,
            video_url=video_url,
            merge_interval=config.subtitle_merge_interval
        )

        if not subtitle_data:
            return _create_failed_result(video_id, "Failed to process subtitles", "subtitle_processing", start_time, video_info.title)

        # Save clean subtitle
        clean_dir = output_dir / "clean" / sanitize_filename(video_info.channel)
        clean_dir.mkdir(parents=True, exist_ok=True)
        clean_file = clean_dir / f"{sanitize_filename(video_info.title)}.txt"
        with open(clean_file, "w", encoding="utf-8") as f:
            f.write(subtitle_data.with_metadata)

        logger.info(f"[{video_id}] ✓ Processed subtitles ({len(srt_entries)} entries)")

        # Stage 4: AI Analysis
        # Academic content overrides agent setting
        use_agent = use_agent_override if use_agent_override is not None else getattr(config, 'use_agent', False)
        agent_name = getattr(config, 'agent_name', 'tech-investment-analyst')

        if use_agent:
            logger.info(f"[{video_id}] Stage 4: Analyzing video with Agent '{agent_name}'...")
        else:
            mode = "Academic Mode" if is_academic else "Standard Mode"
            logger.info(f"[{video_id}] Stage 4: Analyzing video with Claude CLI ({mode})...")

        # Read subtitle content for analysis
        with open(clean_file, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()

        # Get model configs (support both old and new config format)
        model_summary = getattr(config, 'claude_model_summary', None) or getattr(config, 'claude_model', 'claude-opus-4-20250514')
        model_translate = getattr(config, 'claude_model_translate', None) or getattr(config, 'claude_model', 'claude-sonnet-4-20250514')

        # Use analyze_video which supports agent mode
        analysis_result = analyze_video(
            subtitle_text=subtitle_content,
            prompt_file=prompt_summary,
            timeout=config.claude_timeout_seconds,
            model=model_summary,
            use_agent=use_agent,
            agent_name=agent_name
        )

        if not analysis_result:
            # Fallback to direct generate_summary if analyze_video fails
            logger.warning(f"[{video_id}] analyze_video failed, trying generate_summary...")
            summary = generate_summary(
                clean_file,
                prompt_summary,
                timeout=config.claude_timeout_seconds,
                model=model_summary
            )
        else:
            summary = analysis_result.raw_markdown

        if not summary:
            return _create_failed_result(video_id, "Failed to generate summary", "ai_analysis", start_time, video_info.title)

        # Parse results from summary
        chapters = parse_chapters_from_summary(summary)
        video_type = detect_video_type(summary)
        speakers = extract_speakers(summary)

        # Fallback chapters if none found
        if not chapters:
            logger.warning(f"[{video_id}] No chapters found, using fallback")
            duration_sec = get_duration_from_entries(srt_entries)
            interval = config.fallback_chapter_interval
            chapters = [(0, "完整视频")]
            if duration_sec > interval:
                chapters = []
                for i in range(0, duration_sec, interval):
                    chapters.append((i, f"Part {i // interval + 1}"))

        logger.info(f"[{video_id}] ✓ Analysis complete ({len(chapters)} chapters, type: {video_type})")

        # Stage 5: Translation
        if use_agent:
            logger.info(f"[{video_id}] Stage 5: Translating {len(chapters)} chapters with Agent '{agent_name}'...")
        else:
            logger.info(f"[{video_id}] Stage 5: Translating {len(chapters)} chapters...")

        translations, failed_chapters = translate_chapters(
            summary=summary,
            chapters=chapters,
            raw_srt=raw_srt,
            video_type=video_type,
            speakers=speakers,
            prompt_file=prompt_translate,
            timeout=config.claude_timeout_seconds,
            model=model_translate,
            context_lines=config.context_lines,
            max_retries=config.translation_max_retries,
            retry_delay=config.translation_retry_delay,
            use_agent=use_agent,
            agent_name=agent_name
        )

        logger.info(f"[{video_id}] ✓ Translation complete ({len(translations)}/{len(chapters)} successful)")

        # Stage 6: Generate Markdown
        logger.info(f"[{video_id}] Stage 6: Generating markdown output...")

        duration_sec = get_duration_from_entries(srt_entries)
        markdown_content = generate_markdown(
            title=video_info.title,
            channel=video_info.channel,
            upload_date=video_info.upload_date,
            video_url=video_url,
            duration_sec=duration_sec,
            summary=summary,
            translations=translations,
            failed_chapters=failed_chapters
        )

        # Stage 6.5: Review and restructure (optional)
        review_enabled = getattr(config, 'review_enabled', False)
        if review_enabled:
            logger.info(f"[{video_id}] Stage 6.5: Reviewing and restructuring...")
            from core.reviewer import review_content

            remove_garbage = getattr(config, 'review_remove_ai_garbage', False)
            reviewed_content = review_content(
                markdown_content,
                restructure=True,
                remove_garbage=remove_garbage,
                timeout=120
            )

            if reviewed_content:
                markdown_content = reviewed_content
                logger.info(f"[{video_id}] ✓ Review complete")
            else:
                logger.warning(f"[{video_id}] Review failed, using original content")

        # Stage 7: Save output
        logger.info(f"[{video_id}] Stage 7: Saving output file...")

        output_path = save_output(
            markdown_content,
            title=video_info.title,
            channel=video_info.channel,
            output_dir=config.output_dir,
            filename_max_length=config.filename_max_length
        )

        logger.info(f"[{video_id}] ✓ Saved to {output_path}")

        # Stage 8: Archive
        logger.info(f"[{video_id}] Stage 8: Archiving result...")
        archive.mark_processed(video_id, video_info.title, output_path, len(failed_chapters))

        # Success
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{video_id}] ✅ COMPLETE - {video_info.title} ({elapsed:.1f}s)")

        return PipelineResult(
            video_id=video_id,
            success=True,
            title=video_info.title,
            channel=video_info.channel,
            output_path=output_path,
            error=None,
            stage_failed=None,
            processing_time=elapsed
        )

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{video_id}] ❌ Unexpected error: {e}\n{traceback.format_exc()}")
        return PipelineResult(
            video_id=video_id,
            success=False,
            title="Unknown",
            channel="Unknown",
            output_path=None,
            error=str(e),
            stage_failed="unknown",
            processing_time=elapsed
        )


def run_pipeline(
    config,
    archive,
    channels: Optional[List[dict]] = None,
    email_enabled: bool = False
) -> Tuple[List[PipelineResult], List[PipelineResult]]:
    """
    Run the complete pipeline for all configured channels.

    Args:
        config: Config object
        archive: Archive object
        channels: List of channel dicts (uses config.channels if None)
        email_enabled: Whether to send email notifications

    Returns:
        Tuple of (successful_results, failed_results)
    """
    from core.video_discovery import fetch_channel_videos_rss, filter_new_videos_rss
    from infrastructure.notifier import send_update_email

    successful = []
    failed = []

    target_channels = channels if channels else config.channels
    channels_file = Path("channels.json")

    logger.info(f"Processing {len(target_channels)} channel(s)...")

    for channel in target_channels:
        # Handle both ChannelConfig objects and dicts
        if hasattr(channel, 'name'):
            # It's a ChannelConfig object
            channel_name = channel.name
            channel_id = channel.channel_id
            channel_dict = {
                "name": channel.name,
                "handle": channel.handle,
                "url": channel.url,
                "channel_id": channel.channel_id,
                "tags": getattr(channel, 'tags', None)
            }
            channel_config = channel
        else:
            # It's a dict
            channel_name = channel.get("name", "Unknown")
            channel_id = channel.get("channel_id")
            channel_dict = channel
            channel_config = channel  # Use the dict directly

        logger.info(f"Checking channel: {channel_name}")

        try:
            # Fetch new videos from RSS
            videos = fetch_channel_videos_rss(channel_dict, config.lookback_hours, channels_file)
            new_videos = filter_new_videos_rss(videos, archive)

            logger.info(f"Found {len(new_videos)}/{len(videos)} new videos")

            # Process each video
            for video in new_videos:
                result = process_video(
                    video.video_id,
                    config,
                    archive,
                    channel_config=channel_config
                )
                if result.success and result.output_path:
                    successful.append(result)
                elif not result.success:
                    failed.append(result)
                # If success but no output_path, it was skipped

        except Exception as e:
            logger.error(f"Failed to process channel {channel_name}: {e}")

    # Send email notification if enabled (only for videos processed in this run)
    if email_enabled and successful:
        video_infos = [{
            "file_path": r.output_path,
            "channel": r.channel,
            "title": r.title,
            "url": f"https://www.youtube.com/watch?v={r.video_id}"
        } for r in successful if r.output_path]

        if video_infos:
            send_update_email(video_infos)

    # Print summary
    print_summary(successful, failed)

    return successful, failed


def run_loop(config_path: str = "config_ai.json", archive_path: str = None, email_enabled: bool = True) -> None:
    """
    Run the pipeline in continuous loop mode.
    Reloads config and channels on each iteration to pick up changes.

    Args:
        config_path: Path to config file (reloaded each iteration)
        archive_path: Path to archive file (uses config value if None)
        email_enabled: Whether to send email notifications
    """
    import time
    import json
    from main import load_config, load_archive

    logger.info("Starting continuous loop mode...")

    while True:
        try:
            # Reload config and channels each iteration
            logger.info("Reloading config and channels...")
            config = load_config()

            # Use provided archive path or from config
            actual_archive_path = archive_path or config.archive_file
            archive = load_archive(actual_archive_path)

            interval_hours = getattr(config, 'check_interval_hours', 3)
            logger.info(f"Config loaded: {len(config.channels)} channels, interval={interval_hours}h")

            # Run pipeline with fresh config
            run_pipeline(config, archive, email_enabled=email_enabled)

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            interval_hours = 3  # Default fallback

        if interval_hours == 0:
            break

        logger.info(f"Sleeping for {interval_hours} hours...")
        time.sleep(interval_hours * 3600)


def print_summary(
    successful: List[PipelineResult],
    failed: List[PipelineResult]
) -> None:
    """Print processing summary to logger."""
    total = len(successful) + len(failed)
    elapsed_total = sum(r.processing_time for r in successful + failed)

    logger.info("")
    logger.info("=" * 60)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total videos: {total}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total time: {elapsed_total:.1f}s")

    if successful:
        logger.info("")
        logger.info("✅ SUCCESSFUL:")
        for result in successful:
            logger.info(f"  • {result.title} - {result.processing_time:.1f}s")

    if failed:
        logger.info("")
        logger.info("❌ FAILED:")
        for result in failed:
            logger.info(f"  • {result.title} - {result.stage_failed}: {result.error}")

    logger.info("=" * 60)


def _create_failed_result(
    video_id: str,
    error: str,
    stage: str,
    start_time: datetime,
    title: str = "Unknown",
    channel: str = "Unknown"
) -> PipelineResult:
    """Create a failed PipelineResult."""
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.error(f"[{video_id}] Failed at {stage}: {error}")

    return PipelineResult(
        video_id=video_id,
        success=False,
        title=title,
        channel=channel,
        output_path=None,
        error=error,
        stage_failed=stage,
        processing_time=elapsed
    )
