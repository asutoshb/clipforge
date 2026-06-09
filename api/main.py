"""FastAPI app exposing ClipForge's three features.

Run: uvicorn clipforge.api.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..core import captions as captions_mod
from ..core import pipeline
from ..core.config import get_settings

app = FastAPI(title="ClipForge", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class DownloadReq(BaseModel):
    url: str
    start: Optional[float] = None
    end: Optional[float] = None


class ShortsReq(BaseModel):
    url: str
    count: int = 3
    aspect: str = "9:16"
    platform: str = "youtube"
    niche: Optional[str] = None


class CaptionReq(BaseModel):
    text: str
    platform: str = "youtube"
    niche: Optional[str] = None


@app.get("/api/health")
def health() -> dict:
    s = get_settings()
    return {"status": "ok", "llm_provider": s.llm_provider}


@app.post("/api/youtube/download")
def youtube_download(req: DownloadReq) -> dict:
    try:
        return pipeline.youtube_download(req.url, req.start, req.end)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/youtube/shorts")
def youtube_shorts(req: ShortsReq) -> dict:
    try:
        return pipeline.youtube_to_shorts(
            req.url, req.count, req.aspect, req.platform, req.niche)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reel")
async def make_reel(
    prompt: str = Form(...),
    duration: float = Form(30.0),
    aspect: str = Form("9:16"),
    platform: str = Form("instagram"),
    niche: Optional[str] = Form(None),
    files: list[UploadFile] = File(...),
) -> dict:
    settings = get_settings()
    job_dir = settings.subdir("uploads") / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        dest = job_dir / Path(f.filename).name
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
    try:
        return pipeline.media_prompt_to_short(
            job_dir, prompt, duration, aspect, platform, niche)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/caption")
def caption(req: CaptionReq) -> dict:
    from dataclasses import asdict

    return asdict(captions_mod.generate_copy(
        req.text, platform=req.platform, niche=req.niche))


@app.get("/api/file")
def get_file(path: str) -> FileResponse:
    """Serve a generated file for the download button. Restricted to storage/."""
    settings = get_settings()
    target = Path(path).resolve()
    if settings.storage_path.resolve() not in target.parents:
        raise HTTPException(status_code=403, detail="Path not allowed.")
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(target, filename=target.name)
