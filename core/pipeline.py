"""High-level orchestrators that combine the core building blocks.

These are the functions the API and CLI call. Each returns plain dicts/paths
so they are easy to serialize.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Optional

from . import captions, downloader, moments, renderer, transcriber
from .config import get_settings


def youtube_download(url: str, start: Optional[float] = None,
                     end: Optional[float] = None) -> dict:
    """Feature 2: download a full video or a trimmed range."""
    result = downloader.download(url, start, end)
    return {
        "title": result.title,
        "duration": result.duration,
        "file": str(result.path),
    }


def youtube_to_shorts(url: str, count: int = 3, aspect: str = "9:16",
                      platform: str = "youtube", niche: Optional[str] = None) -> dict:
    """Feature 1: link -> transcribe -> pick moments -> 9:16 + captions + copy."""
    settings = get_settings()
    out_dir = settings.subdir("shorts")

    dl = downloader.download(url)
    tr = transcriber.transcribe(dl.path)
    picks = moments.find_moments(tr, count=count)

    shorts: list[dict] = []
    for i, m in enumerate(picks):
        clip = renderer.trim(dl.path, m.start, m.end,
                             out_dir / f"{dl.path.stem}-m{i}.mp4")
        vertical = renderer.to_vertical(clip, aspect)
        text = _segment_text(tr, m.start, m.end)
        copy = captions.generate_copy(text, platform=platform, niche=niche)
        shorts.append({
            "file": str(vertical),
            "start": m.start,
            "end": m.end,
            "reason": m.reason,
            "copy": asdict(copy),
        })
    return {"source": dl.title, "shorts": shorts}


def media_prompt_to_short(media_dir: Path, prompt: str, duration: float = 30.0,
                          aspect: str = "9:16", platform: str = "instagram",
                          niche: Optional[str] = None,
                          music: Optional[Path] = None) -> dict:
    """Feature 3: user media + prompt -> finished short + copy."""
    from . import director

    settings = get_settings()
    out_dir = settings.subdir("reels")
    media_files = [str(p) for p in sorted(media_dir.iterdir())
                   if p.suffix.lower() in _MEDIA_EXT]
    if not media_files:
        raise ValueError("No supported media files found in the upload folder.")

    plan = director.plan_edit(media_files, prompt, duration, aspect)
    out_path = out_dir / "reel.mp4"
    director.render_plan(plan, media_dir, out_path, music)
    copy = captions.generate_copy(prompt, platform=platform, niche=niche)
    return {
        "file": str(out_path),
        "plan": {"duration": plan.duration, "aspect": plan.aspect,
                 "scenes": [asdict(s) for s in plan.scenes]},
        "copy": asdict(copy),
    }


_MEDIA_EXT = {".mp4", ".mov", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp"}


def _segment_text(tr: transcriber.Transcript, start: float, end: float) -> str:
    return " ".join(
        s.text for s in tr.segments if s.start >= start - 1 and s.end <= end + 1
    )
