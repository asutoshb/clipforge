"""Local speech-to-text via faster-whisper (free, runs on your machine).

Produces both plain text and word-level timestamps, which power moment
selection (Feature 1) and animated captions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import get_settings


@dataclass
class Word:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)


@dataclass
class Transcript:
    text: str
    segments: list[Segment] = field(default_factory=list)


def transcribe(media_path: Path) -> Transcript:
    """Transcribe an audio/video file with word timestamps."""
    from faster_whisper import WhisperModel

    settings = get_settings()
    model = WhisperModel(
        settings.whisper_model, device=settings.whisper_device, compute_type="int8"
    )
    seg_iter, _info = model.transcribe(str(media_path), word_timestamps=True)

    segments: list[Segment] = []
    full: list[str] = []
    for s in seg_iter:
        words = [Word(w.start, w.end, w.word) for w in (s.words or [])]
        segments.append(Segment(s.start, s.end, s.text.strip(), words))
        full.append(s.text.strip())

    return Transcript(text=" ".join(full), segments=segments)


def to_srt(segments: list[Segment]) -> str:
    """Render segments as SRT subtitle text."""
    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{_ts(seg.start)} --> {_ts(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    return "\n".join(lines)


def _ts(seconds: float) -> str:
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
