"""Provider-agnostic LLM client.

Default is a local, free model served by Ollama. Switch to OpenAI by setting
CLIPFORGE_LLM_PROVIDER=openai and OPENAI_API_KEY. All callers use `complete()`
and `complete_json()` so the rest of the app never cares which provider runs.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx

from .config import get_settings


class LLMError(RuntimeError):
    pass


def complete(prompt: str, system: str = "", temperature: float = 0.7) -> str:
    """Return a plain-text completion from the configured provider."""
    settings = get_settings()
    if settings.llm_provider == "openai":
        return _openai(prompt, system, temperature)
    return _ollama(prompt, system, temperature)


def complete_json(prompt: str, system: str = "", temperature: float = 0.4) -> Any:
    """Ask the model for JSON and parse it, tolerating code fences."""
    raw = complete(prompt, system + "\nRespond with valid JSON only.", temperature)
    return _extract_json(raw)


def _ollama(prompt: str, system: str, temperature: float) -> str:
    settings = get_settings()
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        resp = httpx.post(
            f"{settings.ollama_host}/api/generate", json=payload, timeout=120
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMError(
            f"Could not reach Ollama at {settings.ollama_host}. "
            "Is it running? Try: `ollama serve` and `ollama pull "
            f"{settings.ollama_model}`. ({exc})"
        ) from exc
    return resp.json().get("response", "").strip()


def _openai(prompt: str, system: str, temperature: float) -> str:
    settings = get_settings()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("CLIPFORGE_LLM_PROVIDER=openai but OPENAI_API_KEY is unset.")
    payload = {
        "model": settings.openai_model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    start = min((i for i in (text.find("{"), text.find("[")) if i != -1), default=-1)
    if start == -1:
        raise LLMError(f"No JSON found in model output: {text[:200]}")
    snippet = text[start:]
    end = max(snippet.rfind("}"), snippet.rfind("]"))
    return json.loads(snippet[: end + 1])
