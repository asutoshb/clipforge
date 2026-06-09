"""Feature 3: turn user media + a prompt into a finished short.

The LLM acts as an editor and returns an *edit plan* (structured timeline).
The renderer then executes that plan deterministically. v1 assembles clips and
photos in order with simple effects; vision tagging is a future upgrade.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import llm
from .renderer import ASPECTS, _run

SYSTEM = (
    "You are an expert short-form video editor. You arrange the user's own "
    "photos and video clips into a punchy reel that matches their prompt."
)


@dataclass
class Scene:
    source: str
    length: float
    effect: str = "none"
    caption: str = ""


@dataclass
class EditPlan:
    duration: float
    aspect: str
    scenes: list[Scene] = field(default_factory=list)


def plan_edit(media_files: list[str], prompt: str, duration: float = 30.0,
              aspect: str = "9:16") -> EditPlan:
    """Ask the LLM for an edit plan; fall back to an even split if unavailable."""
    listing = "\n".join(f"- {Path(m).name}" for m in media_files)
    ask = (
        f"User prompt: {prompt}\n"
        f"Target duration: {duration:.0f}s. Aspect: {aspect}.\n"
        f"Available media files (use only these names):\n{listing}\n\n"
        'Return JSON: {"scenes": [{"source": filename, "length": seconds, '
        '"effect": one of [none, zoom_in, ken_burns, fade], "caption": text}]}'
    )
    try:
        data = llm.complete_json(ask, SYSTEM)
        scenes = [
            Scene(s["source"], float(s.get("length", 3)),
                  s.get("effect", "none"), s.get("caption", ""))
            for s in data.get("scenes", [])
            if s.get("source") in {Path(m).name for m in media_files}
        ]
        if scenes:
            return EditPlan(duration, aspect, scenes)
    except llm.LLMError:
        pass
    return _even_plan(media_files, duration, aspect)


def _even_plan(media_files: list[str], duration: float, aspect: str) -> EditPlan:
    n = max(len(media_files), 1)
    per = duration / n
    scenes = [Scene(Path(m).name, per, "ken_burns") for m in media_files]
    return EditPlan(duration, aspect, scenes)


def render_plan(plan: EditPlan, media_dir: Path, out_path: Path,
                music: Path | None = None) -> Path:
    """Render an edit plan to a video using ffmpeg concat of per-scene clips."""
    w, h = ASPECTS.get(plan.aspect, ASPECTS["9:16"])
    tmp_dir = out_path.parent / f"{out_path.stem}_scenes"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []

    for i, sc in enumerate(plan.scenes):
        src = media_dir / sc.source
        part = tmp_dir / f"scene_{i:03d}.mp4"
        is_image = src.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        cmd = ["ffmpeg", "-y"]
        if is_image:
            cmd += ["-loop", "1", "-t", str(sc.length), "-i", str(src)]
        else:
            cmd += ["-t", str(sc.length), "-i", str(src)]
        cmd += ["-vf", vf, "-r", "30", "-pix_fmt", "yuv420p",
                "-c:v", "libx264", "-an", str(part)]
        _run(cmd)
        parts.append(part)

    concat_file = tmp_dir / "concat.txt"
    concat_file.write_text("\n".join(f"file '{p.resolve()}'" for p in parts))
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
           "-i", str(concat_file)]
    if music and music.exists():
        cmd += ["-i", str(music), "-shortest", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)]
    _run(cmd)
    return out_path
