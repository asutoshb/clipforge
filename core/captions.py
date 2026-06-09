"""Viral titles, captions & hashtags generator (used by every feature).

Given a transcript snippet OR a user prompt and a target platform, returns
ready-to-post copy tuned per platform (YouTube, Instagram, LinkedIn).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import llm

PLATFORM_GUIDE = {
    "youtube": "Punchy <70-char titles with a curiosity hook; 3-5 hashtags.",
    "instagram": "Short hook + emojis + 1 CTA; 8-15 niche hashtags.",
    "linkedin": "Professional, insight-first hook; no clickbait; 3-5 hashtags.",
}

SYSTEM = (
    "You are a senior social media copywriter who writes high-retention, "
    "non-cringe hooks. You understand YouTube, Instagram and LinkedIn norms."
)


@dataclass
class CopyResult:
    titles: list[str] = field(default_factory=list)
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)


def generate_copy(
    context: str,
    platform: str = "youtube",
    niche: Optional[str] = None,
    tone: str = "energetic",
) -> CopyResult:
    """Generate titles + caption + hashtags for the given platform."""
    guide = PLATFORM_GUIDE.get(platform, PLATFORM_GUIDE["youtube"])
    niche_line = f"Creator niche: {niche}.\n" if niche else ""
    prompt = (
        f"{niche_line}Platform: {platform}. Tone: {tone}.\n"
        f"Platform style: {guide}\n\n"
        "Source content (transcript or idea):\n"
        f'"""{context[:3000]}"""\n\n'
        "Return JSON with keys: "
        '"titles" (5 strings, best first), '
        '"caption" (1 string ready to post), '
        '"hashtags" (list of strings without the # symbol).'
    )
    try:
        data = llm.complete_json(prompt, SYSTEM)
    except llm.LLMError:
        return _fallback(context, platform)

    return CopyResult(
        titles=[str(t) for t in data.get("titles", [])][:5],
        caption=str(data.get("caption", "")).strip(),
        hashtags=[str(h).lstrip("#") for h in data.get("hashtags", [])],
    )


def _fallback(context: str, platform: str) -> CopyResult:
    """Deterministic copy if no LLM is available, so the app still works."""
    snippet = " ".join(context.split())[:60].rstrip(",. ")
    base = snippet or "New video"
    tags = {
        "youtube": ["shorts", "viral", "trending"],
        "instagram": ["reels", "instadaily", "explore", "viral"],
        "linkedin": ["learning", "growth", "buildinpublic"],
    }.get(platform, ["shorts"])
    return CopyResult(
        titles=[base, f"{base} 🔥", f"You won't believe: {base}"],
        caption=f"{base} — watch till the end!",
        hashtags=tags,
    )
