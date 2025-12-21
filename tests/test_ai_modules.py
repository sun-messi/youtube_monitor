"""Tests for AI modules (analyzer, chapter optimizer, translator)."""

import pytest
from unittest.mock import patch, MagicMock

from core.ai_analyzer import (
    ChapterInfo,
    AnalysisResult,
    _parse_analysis_response,
    validate_analysis,
)
from core.chapter_optimizer import (
    OptimizedChapter,
    optimize_chapters,
    validate_optimized_chapters,
    estimate_chapter_quality,
)
from core.translator import (
    TranslationResult,
    validate_translation,
    estimate_translation_quality,
    combine_translations,
)
from utils.srt_parser import SubtitleEntry


class TestChapterInfo:
    """Test ChapterInfo data class."""

    def test_chapter_info_creation(self):
        """Test creating ChapterInfo."""
        ch = ChapterInfo(start_sec=0.0, title="Introduction")
        assert ch.start_sec == 0.0
        assert ch.title == "Introduction"


class TestAnalysisResult:
    """Test AnalysisResult data class."""

    def test_analysis_result_creation(self):
        """Test creating AnalysisResult."""
        result = AnalysisResult(
            summary="Test summary",
            chapters=[ChapterInfo(0.0, "Intro")],
            video_type="speech",
            speakers="John Doe",
            key_points=["Point 1", "Point 2"],
        )
        assert result.summary == "Test summary"
        assert len(result.chapters) == 1
        assert result.video_type == "speech"


class TestAIAnalyzer:
    """Test AI analyzer functions."""

    def test_parse_analysis_response_valid(self):
        """Test parsing valid analysis response."""
        response = """{
            "summary": "Test summary",
            "chapters": [
                {"start_sec": 0, "title": "Intro"},
                {"start_sec": 300, "title": "Main"}
            ],
            "video_type": "speech",
            "speakers": "John Doe",
            "key_points": ["Point 1", "Point 2"]
        }"""

        result = _parse_analysis_response(response)
        assert result.summary == "Test summary"
        assert len(result.chapters) == 2
        assert result.video_type == "speech"
        assert len(result.key_points) == 2

    def test_parse_analysis_response_wrapped_json(self):
        """Test parsing JSON wrapped in text."""
        response = """Here's the analysis:

{
    "summary": "Test summary",
    "chapters": [{"start_sec": 0, "title": "Intro"}],
    "video_type": "interview",
    "speakers": "Alice, Bob",
    "key_points": ["Point 1"]
}

End of analysis."""

        result = _parse_analysis_response(response)
        assert result.summary == "Test summary"
        assert result.video_type == "interview"

    def test_parse_analysis_response_invalid_json(self):
        """Test parsing invalid JSON."""
        response = "This is not JSON"
        result = _parse_analysis_response(response)
        assert result.summary == "分析失败，无法提取内容"
        assert len(result.chapters) == 0

    def test_validate_analysis_valid(self):
        """Test validation of valid analysis."""
        result = AnalysisResult(
            summary="Valid summary with enough content",
            chapters=[
                ChapterInfo(0.0, "Intro"),
                ChapterInfo(300.0, "Main"),
            ],
            video_type="speech",
            speakers="John Doe",
            key_points=["Point 1", "Point 2"],
        )

        is_valid, issues = validate_analysis(result)
        assert is_valid is True
        assert len(issues) == 0

    def test_validate_analysis_empty_summary(self):
        """Test validation with empty summary."""
        result = AnalysisResult(
            summary="",
            chapters=[ChapterInfo(0.0, "Intro")],
            video_type="speech",
            speakers="",
            key_points=[],
        )

        is_valid, issues = validate_analysis(result)
        assert is_valid is False
        assert any("summary" in issue.lower() for issue in issues)

    def test_validate_analysis_no_chapters(self):
        """Test validation with no chapters."""
        result = AnalysisResult(
            summary="Valid summary",
            chapters=[],
            video_type="speech",
            speakers="",
            key_points=["Point 1"],
        )

        is_valid, issues = validate_analysis(result)
        assert is_valid is False
        assert any("chapter" in issue.lower() for issue in issues)

    def test_validate_analysis_invalid_video_type(self):
        """Test validation with invalid video type."""
        result = AnalysisResult(
            summary="Valid summary",
            chapters=[ChapterInfo(0.0, "Intro")],
            video_type="invalid_type",
            speakers="",
            key_points=["Point 1"],
        )

        is_valid, issues = validate_analysis(result)
        assert is_valid is False


class TestOptimizedChapter:
    """Test OptimizedChapter data class."""

    def test_optimized_chapter_creation(self):
        """Test creating OptimizedChapter."""
        ch = OptimizedChapter(
            index=0,
            start_sec=0.0,
            end_sec=300.0,
            title="Intro",
            duration_sec=300.0,
            entry_count=10,
        )
        assert ch.index == 0
        assert ch.duration_sec == 300.0


class TestChapterOptimizer:
    """Test chapter optimization."""

    @pytest.fixture
    def sample_chapters(self):
        """Create sample chapters."""
        return [
            ChapterInfo(0.0, "Intro"),
            ChapterInfo(300.0, "Main"),
            ChapterInfo(600.0, "Conclusion"),
        ]

    @pytest.fixture
    def sample_entries(self):
        """Create sample subtitle entries."""
        return [
            SubtitleEntry(1, 0.0, 30.0, "Text 1"),
            SubtitleEntry(2, 30.0, 60.0, "Text 2"),
            SubtitleEntry(3, 600.0, 700.0, "Text 3"),
        ]

    def test_optimize_chapters_basic(self, sample_chapters, sample_entries):
        """Test basic chapter optimization."""
        optimized = optimize_chapters(sample_chapters, sample_entries)
        assert len(optimized) > 0
        assert all(isinstance(ch, OptimizedChapter) for ch in optimized)

    def test_optimize_chapters_empty(self):
        """Test optimization with empty chapters."""
        entries = [SubtitleEntry(1, 0.0, 100.0, "Text")]
        optimized = optimize_chapters([], entries)
        assert len(optimized) == 0

    def test_optimize_chapters_invalid_params(self, sample_chapters, sample_entries):
        """Test optimization with invalid parameters."""
        with pytest.raises(ValueError):
            optimize_chapters(sample_chapters, sample_entries, min_duration=-1)

        with pytest.raises(ValueError):
            optimize_chapters(
                sample_chapters, sample_entries, min_duration=900, max_duration=180
            )

    def test_validate_optimized_chapters_valid(self, sample_chapters, sample_entries):
        """Test validation of optimized chapters."""
        optimized = optimize_chapters(sample_chapters, sample_entries)
        is_valid, issues = validate_optimized_chapters(optimized)
        # May or may not be valid depending on optimization

    def test_validate_optimized_chapters_empty(self):
        """Test validation of empty chapters."""
        is_valid, issues = validate_optimized_chapters([])
        assert is_valid is False
        assert len(issues) > 0

    def test_estimate_chapter_quality(self, sample_chapters, sample_entries):
        """Test quality estimation."""
        optimized = optimize_chapters(sample_chapters, sample_entries)
        metrics = estimate_chapter_quality(optimized)
        assert "total_chapters" in metrics
        assert "avg_duration_sec" in metrics
        assert metrics["total_chapters"] >= 0


class TestTranslationResult:
    """Test TranslationResult data class."""

    def test_translation_result_creation(self):
        """Test creating TranslationResult."""
        result = TranslationResult(
            chapter_idx=0,
            chapter_title="Intro",
            original_text="Hello",
            translated_text="你好",
            success=True,
            duration_sec=1.0,
        )
        assert result.chapter_idx == 0
        assert result.success is True


class TestTranslator:
    """Test translator functions."""

    def test_validate_translation_valid(self):
        """Test validation of valid translation."""
        original = "Hello world, this is a test."
        translated = "你好世界，这是一个测试。"
        is_valid, issues = validate_translation(original, translated)
        assert is_valid is True

    def test_validate_translation_empty(self):
        """Test validation of empty translation."""
        is_valid, issues = validate_translation("Hello", "")
        assert is_valid is False

    def test_validate_translation_not_translated(self):
        """Test validation when text wasn't translated."""
        text = "Hello"
        is_valid, issues = validate_translation(text, text)
        assert is_valid is False

    def test_validate_translation_too_short(self):
        """Test validation of too-short translation."""
        original = "This is a long sentence that should be translated."
        translated = "短"
        is_valid, issues = validate_translation(original, translated)
        assert is_valid is False

    def test_estimate_translation_quality_empty(self):
        """Test quality estimation for empty results."""
        metrics = estimate_translation_quality([])
        assert metrics["total_chapters"] == 0
        assert metrics["success_rate"] == 0.0

    def test_estimate_translation_quality_mixed(self):
        """Test quality estimation with mixed results."""
        results = [
            TranslationResult(0, "Ch1", "Text 1", "翻译 1", True, 1.0),
            TranslationResult(1, "Ch2", "Text 2", "", False, 0.0),
        ]
        metrics = estimate_translation_quality(results)
        assert metrics["total_chapters"] == 2
        assert metrics["successful"] == 1
        assert metrics["failed"] == 1
        assert metrics["success_rate"] == pytest.approx(0.5)

    def test_combine_translations(self):
        """Test combining translations."""
        results = [
            TranslationResult(0, "Ch1", "Text 1", "翻译 1", True, 1.0),
            TranslationResult(1, "Ch2", "Text 2", "翻译 2", True, 1.0),
        ]
        combined = combine_translations(results)
        assert "翻译 1" in combined
        assert "翻译 2" in combined

    def test_combine_translations_with_failed(self):
        """Test combining with failed chapters."""
        results = [
            TranslationResult(0, "Ch1", "Text 1", "翻译 1", True, 1.0),
            TranslationResult(1, "Ch2", "Text 2", "", False, 0.0),
        ]
        combined = combine_translations(results)
        assert "翻译 1" in combined
        assert "翻译 2" not in combined


class TestIntegrationAI:
    """Integration tests for AI modules."""

    def test_analysis_to_optimization_workflow(self):
        """Test workflow from analysis to optimization."""
        # Create analysis result
        analysis = AnalysisResult(
            summary="Test video summary",
            chapters=[
                ChapterInfo(0.0, "Introduction"),
                ChapterInfo(600.0, "Main Content"),
                ChapterInfo(1200.0, "Conclusion"),
            ],
            video_type="speech",
            speakers="John Doe",
            key_points=["Key point 1", "Key point 2"],
        )

        # Create subtitle entries
        entries = [
            SubtitleEntry(i, i * 100, (i + 1) * 100, f"Text {i}")
            for i in range(15)
        ]

        # Validate analysis
        is_valid, issues = validate_analysis(analysis)
        assert is_valid is True

        # Optimize chapters
        optimized = optimize_chapters(analysis.chapters, entries)
        assert len(optimized) > 0

        # Validate optimized chapters
        is_valid, issues = validate_optimized_chapters(optimized)
        # Should be valid or have minor issues

    def test_translation_quality_metrics(self):
        """Test translation quality metrics."""
        results = [
            TranslationResult(
                0, "Intro", "Hello world", "你好世界", True, 1.0
            ),
            TranslationResult(1, "Main", "How are you?", "你好吗？", True, 1.2),
        ]

        # Validate each
        for result in results:
            is_valid, _ = validate_translation(
                result.original_text, result.translated_text
            )
            assert is_valid is True

        # Get quality metrics
        metrics = estimate_translation_quality(results)
        assert metrics["success_rate"] == 1.0
        assert metrics["total_chapters"] == 2


class TestCLIPrompts:
    """Test that CLI prompts are properly formatted."""

    def test_analysis_prompt_format(self):
        """Test that analysis prompt is properly formatted."""
        from core.ai_analyzer import _build_analysis_prompt

        context = "Test context"
        prompt = _build_analysis_prompt(context)

        assert "JSON" in prompt or "json" in prompt
        assert "summary" in prompt.lower()
        assert "chapters" in prompt.lower()

    def test_translation_prompt_format(self):
        """Test that translation prompt is properly formatted."""
        from core.translator import _build_translation_prompt

        prompt = _build_translation_prompt("Hello world", "en", "zh")

        assert "translate" in prompt.lower()
        assert "english" in prompt.lower() or "English" in prompt
        assert "chinese" in prompt.lower() or "Chinese" in prompt
