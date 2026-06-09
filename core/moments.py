"""Pick the most share-worthy moments from a transcript (Feature 1).

v1 uses the local LLM to score candidate windows. If no LLM is available it
falls back to evenly spaced segments so the pipeline still produces clips.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import llm
from .transcriber import Transcript

SYSTEM = (
    "You find the most viral, self-contained moments in a transcript for "
    "short-form video. Prefer strong hooks, surprises, and clear payoffs."
)


@dataclass
class Moment:
    start: float
    end: float
    reason: str = ""


def find_moments(
    transcript: Transcript, count: int = 3, max_len: float = 45.0
) -> list[Moment]:
    if not transcript.segments:
        return []
    try:
        return _llm_moments(transcript, count, max_len)
    except llm.LLMError:
        return _even_moments(transcript, count, max_len)


def _llm_moments(transcript: Transcript, count: int, max_len: float) -> list[Moment]:
    indexed = "\n".join(
        f"[{i}] {s.start:.1f}-{s.end:.1f}: {s.text}"
        for i, s in enumerate(transcript.segments)
    )
    prompt = (
        f"Transcript segments (index, start-end, text):\n{indexed}\n\n"
        f"Select the {count} best moments for short clips, each under "
        f"{max_len:.0f}s. Return JSON list of objects with keys "
        '"start", "end", "reason".'
    )
    data = llm.complete_json(prompt, SYSTEM)
    moments = []
    for item in data[:count]:
        start = float(item["start"])
        end = min(float(item["end"]), start + max_len)
        moments.append(Moment(start, end, str(item.get("reason", ""))))
    return moments


def _even_moments(transcript: Transcript, count: int, max_len: float) -> list[Moment]:
    segs = transcript.segments
    total = segs[-1].end
    step = max(total / (count + 1), max_len)
    moments = []
    for i in range(1, count + 1):
        start = min(step * i, max(total - max_len, 0))
        moments.append(Moment(start, min(start + max_len, total), "evenly sampled"))
    return moments
