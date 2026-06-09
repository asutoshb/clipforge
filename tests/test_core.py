"""Unit tests for ClipForge core functions.

All tests are pure-Python and require no network / ffmpeg / LLM.
Run with: pytest tests/test_core.py -v
"""
import json
import pytest


# ---------------------------------------------------------------------------
# captions._fallback
# ---------------------------------------------------------------------------
from core.captions import _fallback, CopyResult


class TestFallback:
    def test_returns_copy_result(self):
        r = _fallback("great running tips", "youtube")
        assert isinstance(r, CopyResult)

    def test_titles_not_empty(self):
        r = _fallback("some content", "instagram")
        assert len(r.titles) >= 1

    def test_titles_include_snippet(self):
        r = _fallback("AI built this editor", "youtube")
        assert any("AI built this editor" in t for t in r.titles)

    def test_caption_not_empty(self):
        r = _fallback("content", "linkedin")
        assert r.caption.strip() != ""

    def test_youtube_hashtags(self):
        r = _fallback("x", "youtube")
        assert "shorts" in r.hashtags

    def test_instagram_hashtags(self):
        r = _fallback("x", "instagram")
        assert "reels" in r.hashtags

    def test_linkedin_hashtags(self):
        r = _fallback("x", "linkedin")
        assert "growth" in r.hashtags

    def test_unknown_platform_gets_default(self):
        r = _fallback("x", "tiktok")
        assert isinstance(r.hashtags, list)

    def test_empty_context_still_works(self):
        r = _fallback("", "youtube")
        # snippet falls back to "New video"
        assert "New video" in r.titles[0] or r.titles[0] != ""

    def test_long_context_truncated(self):
        long_ctx = "word " * 500
        r = _fallback(long_ctx, "youtube")
        # snippet max 60 chars → title should not be >80 chars (emoji adds a bit)
        assert len(r.titles[0]) < 120


# ---------------------------------------------------------------------------
# downloader._to_seconds
# ---------------------------------------------------------------------------
from core.downloader import _to_seconds


class TestToSeconds:
    def test_seconds_only(self):
        assert _to_seconds("45") == 45.0

    def test_mm_ss(self):
        assert _to_seconds("1:30") == 90.0

    def test_hh_mm_ss(self):
        assert _to_seconds("01:30:45") == 5445.0

    def test_zero(self):
        assert _to_seconds("0") == 0.0

    def test_fractional_seconds(self):
        assert _to_seconds("0:00:01.5") == pytest.approx(1.5)

    def test_full_hour(self):
        assert _to_seconds("1:00:00") == 3600.0


# ---------------------------------------------------------------------------
# director._even_plan
# ---------------------------------------------------------------------------
from core.director import _even_plan, EditPlan, Scene


class TestEvenPlan:
    def test_returns_edit_plan(self):
        plan = _even_plan(["a.mp4", "b.mp4"], 20.0, "9:16")
        assert isinstance(plan, EditPlan)

    def test_correct_scene_count(self):
        plan = _even_plan(["a.mp4", "b.mp4", "c.mp4"], 30.0, "9:16")
        assert len(plan.scenes) == 3

    def test_even_duration_split(self):
        plan = _even_plan(["x.mp4", "y.mp4"], 20.0, "9:16")
        for sc in plan.scenes:
            assert sc.length == pytest.approx(10.0)

    def test_single_file(self):
        plan = _even_plan(["only.mp4"], 15.0, "16:9")
        assert len(plan.scenes) == 1
        assert plan.scenes[0].length == pytest.approx(15.0)

    def test_empty_list_does_not_crash(self):
        # n = max(0, 1) = 1; no scenes produced but should not raise
        plan = _even_plan([], 10.0, "9:16")
        assert isinstance(plan, EditPlan)

    def test_aspect_propagated(self):
        plan = _even_plan(["a.mp4"], 5.0, "16:9")
        assert plan.aspect == "16:9"

    def test_duration_propagated(self):
        plan = _even_plan(["a.mp4", "b.mp4"], 42.0, "9:16")
        assert plan.duration == pytest.approx(42.0)

    def test_scene_effect_is_ken_burns(self):
        plan = _even_plan(["a.mp4"], 5.0, "9:16")
        assert plan.scenes[0].effect == "ken_burns"


# ---------------------------------------------------------------------------
# llm._extract_json
# ---------------------------------------------------------------------------
from core.llm import _extract_json, LLMError


class TestExtractJson:
    def test_plain_object(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_plain_array(self):
        assert _extract_json('[1, 2, 3]') == [1, 2, 3]

    def test_strips_code_fence(self):
        raw = "```json\n{\"x\": 42}\n```"
        assert _extract_json(raw) == {"x": 42}

    def test_strips_generic_fence(self):
        raw = "```\n{\"y\": true}\n```"
        assert _extract_json(raw) == {"y": True}

    def test_text_before_json(self):
        raw = "Here is the JSON: {\"z\": \"hello\"}"
        assert _extract_json(raw) == {"z": "hello"}

    def test_no_json_raises(self):
        with pytest.raises(LLMError):
            _extract_json("no json here at all")

    def test_nested_object(self):
        data = {"titles": ["a", "b"], "caption": "hi", "hashtags": ["x"]}
        assert _extract_json(json.dumps(data)) == data
