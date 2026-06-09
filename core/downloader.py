"""Video download via yt-dlp (open-source). Powers Features 1 & 2.

Note on rights: only download content you own, Creative Commons, or otherwise
have permission to use. Respect each platform's Terms of Service.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from slugify import slugify

from .config import get_settings


@dataclass
class DownloadResult:
    path: Path
    title: str
    duration: Optional[float]
    source_url: str


def _ydl_opts(out_template: str, section: Optional[str] = None) -> dict:
    clients = [c.strip() for c in get_settings().youtube_player_client.split(",") if c.strip()]
    opts = {
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # Avoid YouTube SABR 403s by selecting a client that returns real URLs.
        "extractor_args": {"youtube": {"player_client": clients}},
    }
    if section:
        # download only a time range, e.g. "*00:01:10-00:01:40"
        opts["download_ranges"] = _range_func(section)
        opts["force_keyframes_at_cuts"] = True
    return opts


def _range_func(section: str):
    from yt_dlp.utils import download_range_func

    raw = section.lstrip("*")
    start, _, end = raw.partition("-")
    return download_range_func(None, [(_to_seconds(start), _to_seconds(end))])


def _to_seconds(stamp: str) -> float:
    parts = [float(p) for p in stamp.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def download(url: str, start: Optional[float] = None, end: Optional[float] = None) -> DownloadResult:
    """Download a video (optionally only the start..end second range)."""
    import yt_dlp

    settings = get_settings()
    out_dir = settings.subdir("downloads")
    out_template = str(out_dir / "%(id)s.%(ext)s")

    section = None
    if start is not None and end is not None:
        section = f"*{_fmt(start)}-{_fmt(end)}"

    with yt_dlp.YoutubeDL(_ydl_opts(out_template, section)) as ydl:
        info = ydl.extract_info(url, download=True)

    video_id = info["id"]
    produced = next(out_dir.glob(f"{video_id}.*"), None)
    if produced is None:
        raise FileNotFoundError("Download finished but output file was not found.")

    # Give the file a human-friendly name
    nice = out_dir / f"{slugify(info.get('title', video_id))[:60]}-{video_id}{produced.suffix}"
    produced.rename(nice)

    return DownloadResult(
        path=nice,
        title=info.get("title", video_id),
        duration=info.get("duration"),
        source_url=url,
    )


def _fmt(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
