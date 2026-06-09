"""ffmpeg-based rendering helpers shared by all features.

Capabilities:
    trim          cut a clip to a start..end range (Feature 2)
    to_vertical   reframe to 9:16 (center crop for v1; face-track later)
    burn_captions burn an .srt subtitle file into a video (Feature 1)
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

ASPECTS = {
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "16:9": (1920, 1080),
}


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr[-1500:]}")


def trim(src: Path, start: float, end: float, dst: Optional[Path] = None) -> Path:
    """Cut src to the given second range and re-encode for clean cuts."""
    dst = dst or src.with_name(f"{src.stem}-clip{src.suffix}")
    _run([
        "ffmpeg", "-y",
        "-ss", str(start), "-to", str(end),
        "-i", str(src),
        "-c:v", "libx264", "-c:a", "aac",
        str(dst),
    ])
    return dst


def to_vertical(src: Path, aspect: str = "9:16", dst: Optional[Path] = None) -> Path:
    """Reframe a video to a target aspect via scale + center crop (v1)."""
    w, h = ASPECTS.get(aspect, ASPECTS["9:16"])
    dst = dst or src.with_name(f"{src.stem}-{aspect.replace(':', 'x')}{src.suffix}")
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}"
    )
    _run([
        "ffmpeg", "-y",
        "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-c:a", "aac",
        str(dst),
    ])
    return dst


def burn_captions(src: Path, srt_path: Path, dst: Optional[Path] = None) -> Path:
    """Burn subtitles into the video (hardcoded captions for shorts)."""
    dst = dst or src.with_name(f"{src.stem}-captioned{src.suffix}")
    style = "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,Outline=2,Bold=1"
    _run([
        "ffmpeg", "-y",
        "-i", str(src),
        "-vf", f"subtitles={srt_path}:force_style='{style}'",
        "-c:v", "libx264", "-c:a", "aac",
        str(dst),
    ])
    return dst


def ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
