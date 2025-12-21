"""
Multi-language translation engine using Claude CLI.

Based on working implementation from /home/sunj11/youtube_monitor/process_ai.py
"""

import logging
import subprocess
import time
from typing import List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from core.ai_analyzer import get_claude_cli_path, CLAUDE_CLI
from utils.srt_parser import format_time, get_segment_text, get_last_lines

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Complete translation result for a chapter."""
    chapter_idx: int
    chapter_title: str
    time_range: str
    original_text: str
    translated_text: str
    success: bool
    error_message: Optional[str] = None


def call_claude_translate(
    params: dict,
    prompt_file: Path,
    timeout: int = 300,
    model: str = None
) -> str:
    """
    Call Claude CLI for translation with placeholder replacement.

    Args:
        params: Dict with video_type, speakers, chapter_title, time_range,
                segment_text, previous_original, previous_translation
        prompt_file: Path to yt-translate.md template
        timeout: Timeout in seconds
        model: Claude model to use

    Returns:
        Translated text
    """
    # Read prompt template
    if not prompt_file.exists():
        logger.error(f"Prompt file not found: {prompt_file}")
        return ""

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Replace placeholders with actual values
    prompt = prompt_template
    prompt = prompt.replace("{{VIDEO_TYPE}}", params.get("video_type", ""))
    prompt = prompt.replace("{{SPEAKERS}}", params.get("speakers", ""))
    prompt = prompt.replace("{{CHAPTER_TITLE}}", params.get("chapter_title", ""))
    prompt = prompt.replace("{{TIME_RANGE}}", params.get("time_range", ""))
    prompt = prompt.replace("{{SEGMENT_TEXT}}", params.get("segment_text", ""))
    prompt = prompt.replace("{{PREVIOUS_ORIGINAL}}", params.get("previous_original", ""))
    prompt = prompt.replace("{{PREVIOUS_TRANSLATION}}", params.get("previous_translation", ""))

    logger.info(f"Calling Claude CLI for translation" + (f" (model: {model})" if model else ""))

    try:
        cmd = [
            str(CLAUDE_CLI),
            "-p", prompt,
            "--output-format", "text"
        ]
        if model:
            cmd.extend(["--model", model])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            return ""

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.error(f"Claude CLI timeout after {timeout}s")
        return ""
    except FileNotFoundError:
        logger.error("Claude CLI not found.")
        return ""
    except Exception as e:
        logger.error(f"Claude CLI error: {e}")
        return ""


def translate_chapter(
    chapter_idx: int,
    chapter_title: str,
    time_range: str,
    segment_text: str,
    video_type: str,
    speakers: str,
    previous_original: str,
    previous_translation: str,
    prompt_file: Path,
    timeout: int = 300,
    model: str = None,
    max_retries: int = 2,
    retry_delay: int = 5
) -> TranslationResult:
    """
    Translate a single chapter with retry mechanism.

    Args:
        chapter_idx: Chapter index
        chapter_title: Chapter title
        time_range: Time range string (e.g., "00:00 - 05:30")
        segment_text: Original text to translate
        video_type: Type of video (访谈对话/演讲独白/etc.)
        speakers: Speaker information
        previous_original: Previous chapter original text (for context)
        previous_translation: Previous chapter translation (for context)
        prompt_file: Path to translation prompt template
        timeout: Timeout in seconds
        model: Claude model to use
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        TranslationResult object
    """
    params = {
        "video_type": video_type,
        "speakers": speakers,
        "chapter_title": chapter_title,
        "time_range": time_range,
        "segment_text": segment_text,
        "previous_original": previous_original or "(First segment)",
        "previous_translation": previous_translation or "(First segment)"
    }

    logger.info(f"Translating chapter: {time_range} - {chapter_title}")

    # Retry logic
    for attempt in range(max_retries + 1):
        try:
            translated = call_claude_translate(params, prompt_file, timeout, model)

            if translated:
                return TranslationResult(
                    chapter_idx=chapter_idx,
                    chapter_title=chapter_title,
                    time_range=time_range,
                    original_text=segment_text,
                    translated_text=translated,
                    success=True
                )
            else:
                raise Exception("Empty translation result")

        except Exception as e:
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"Translation attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"Translation failed after {max_retries + 1} attempts: {e}")
                return TranslationResult(
                    chapter_idx=chapter_idx,
                    chapter_title=chapter_title,
                    time_range=time_range,
                    original_text=segment_text,
                    translated_text="",
                    success=False,
                    error_message=str(e)
                )

    # Should not reach here, but just in case
    return TranslationResult(
        chapter_idx=chapter_idx,
        chapter_title=chapter_title,
        time_range=time_range,
        original_text=segment_text,
        translated_text="",
        success=False,
        error_message="Unknown error"
    )


def translate_chapters(
    summary: str,
    chapters: List[Tuple[int, str]],
    raw_srt: str,
    video_type: str,
    speakers: str,
    prompt_file: Path,
    timeout: int = 300,
    model: str = None,
    context_lines: int = 5,
    max_retries: int = 2,
    retry_delay: int = 5
) -> Tuple[List[str], List[dict]]:
    """
    Translate all chapters using Claude CLI.

    Args:
        summary: AI generated summary (not used directly, for reference)
        chapters: List of (start_sec, title) tuples
        raw_srt: Raw SRT text
        video_type: Type of video
        speakers: Speaker information
        prompt_file: Path to translation prompt template
        timeout: Timeout in seconds
        model: Claude model to use
        context_lines: Number of context lines to include
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries

    Returns:
        Tuple of (translations list, failed chapters list)
    """
    from utils.srt_parser import parse_srt_full

    srt_entries = parse_srt_full(raw_srt)
    translations = []
    failed_chapters = []
    previous_original = ""
    previous_translation = ""

    for i, (start_sec, title) in enumerate(chapters):
        end_sec = chapters[i + 1][0] if i + 1 < len(chapters) else None
        time_range = f"{format_time(start_sec)} - {format_time(end_sec) if end_sec else 'End'}"

        # Extract segment text
        segment_text = get_segment_text(srt_entries, start_sec, end_sec)
        if not segment_text.strip():
            logger.warning(f"No text for chapter {i}: {title}")
            continue

        # Translate
        result = translate_chapter(
            chapter_idx=i,
            chapter_title=title,
            time_range=time_range,
            segment_text=segment_text,
            video_type=video_type,
            speakers=speakers,
            previous_original=previous_original,
            previous_translation=previous_translation,
            prompt_file=prompt_file,
            timeout=timeout,
            model=model,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

        if result.success:
            # Update context for next segment
            previous_original = get_last_lines(segment_text, context_lines)
            previous_translation = get_last_lines(result.translated_text, context_lines)

            translations.append(f"### ({time_range}) {title}\n\n{result.translated_text}")
        else:
            failed_chapters.append({
                "index": i,
                "title": title,
                "time_range": time_range,
                "error": result.error_message
            })

    logger.info(f"Translation complete: {len(translations)}/{len(chapters)} successful")
    return translations, failed_chapters


def translate_all_chapters(
    chapters: List[Tuple[int, str]],
    srt_entries: List[Tuple[int, int, str]],
    analysis,
    prompt_file: Path,
    timeout: int = 300,
    model: str = None,
    context_lines: int = 5,
    max_retries: int = 2,
    retry_delay: int = 5
) -> Tuple[List[TranslationResult], List[int]]:
    """
    Translate all chapters and return structured results.

    Args:
        chapters: List of (start_sec, title) tuples
        srt_entries: Parsed SRT entries
        analysis: AnalysisResult with video_type and speakers
        prompt_file: Path to translation prompt
        timeout: Timeout in seconds
        model: Claude model
        context_lines: Context lines for consistency
        max_retries: Retry attempts
        retry_delay: Retry delay

    Returns:
        Tuple of (list of TranslationResult, list of failed chapter indices)
    """
    results = []
    failed_indices = []
    previous_original = ""
    previous_translation = ""

    video_type = analysis.video_type if hasattr(analysis, 'video_type') else "访谈对话"
    speakers = analysis.speakers if hasattr(analysis, 'speakers') else ""

    for i, (start_sec, title) in enumerate(chapters):
        end_sec = chapters[i + 1][0] if i + 1 < len(chapters) else None
        time_range = f"{format_time(start_sec)} - {format_time(end_sec) if end_sec else 'End'}"

        # Extract segment text
        segment_text = get_segment_text(srt_entries, start_sec, end_sec)

        if not segment_text.strip():
            logger.warning(f"No text for chapter {i}: {title}")
            results.append(TranslationResult(
                chapter_idx=i,
                chapter_title=title,
                time_range=time_range,
                original_text="",
                translated_text="",
                success=False,
                error_message="No text found"
            ))
            failed_indices.append(i)
            continue

        # Translate
        result = translate_chapter(
            chapter_idx=i,
            chapter_title=title,
            time_range=time_range,
            segment_text=segment_text,
            video_type=video_type,
            speakers=speakers,
            previous_original=previous_original,
            previous_translation=previous_translation,
            prompt_file=prompt_file,
            timeout=timeout,
            model=model,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

        results.append(result)

        if result.success:
            previous_original = get_last_lines(segment_text, context_lines)
            previous_translation = get_last_lines(result.translated_text, context_lines)
        else:
            failed_indices.append(i)

    logger.info(f"Translation complete: {len(results) - len(failed_indices)}/{len(results)} successful")
    return results, failed_indices


def validate_translation(original: str, translated: str) -> Tuple[bool, List[str]]:
    """
    Validate translation quality.

    Args:
        original: Original text
        translated: Translated text

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    # Check if translation is empty
    if not translated or len(translated.strip()) == 0:
        issues.append("Translation is empty")

    # Check length ratio (shouldn't be drastically different)
    if len(translated) < len(original) * 0.3:
        issues.append("Translation seems too short")

    if len(translated) > len(original) * 3.0:
        issues.append("Translation seems too long")

    # Check for untranslated content (heuristic)
    if original.lower() == translated.lower():
        issues.append("Text was not translated")

    is_valid = len(issues) == 0
    return is_valid, issues


def estimate_translation_quality(results: List[TranslationResult]) -> dict:
    """
    Estimate quality metrics for translations.

    Args:
        results: List of translation results

    Returns:
        Quality metrics dictionary
    """
    if not results:
        return {
            "total_chapters": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0,
            "total_original_chars": 0,
            "total_translated_chars": 0,
        }

    successful = sum(1 for r in results if r.success)
    total_original = sum(len(r.original_text) for r in results)
    total_translated = sum(len(r.translated_text) for r in results)

    return {
        "total_chapters": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "success_rate": successful / len(results) if results else 0.0,
        "total_original_chars": total_original,
        "total_translated_chars": total_translated,
        "char_ratio": total_translated / total_original if total_original > 0 else 0.0,
    }


def combine_translations(results: List[TranslationResult], join_str: str = "\n\n") -> str:
    """
    Combine translated chapters into single document.

    Args:
        results: List of translation results
        join_str: String to join chapters

    Returns:
        Combined translated text
    """
    translations = []
    for r in results:
        if r.success and r.translated_text:
            translations.append(f"### ({r.time_range}) {r.chapter_title}\n\n{r.translated_text}")

    return join_str.join(translations)
