# ClipForge 🎬

**Open-source AI tool that turns links and raw media into ready-to-post shorts,
reels, and copy** for YouTube, Instagram, and LinkedIn — runs **100% locally and
free** (no paid APIs required).

> Built in public. The tool makes your content *and* is itself the content.

## ✨ Features

| # | Feature | What it does |
|---|---------|--------------|
| 1 | **YouTube → Shorts** | Link → transcribe → AI finds best moments → 9:16 clips + captions + titles |
| 2 | **YouTube → Download** | Link → download full video, or trim a `start–end` second range |
| 3 | **Media + Prompt → Short** | Upload photos/videos + a prompt → AI assembles a finished reel |
| ➕ | **Titles & Captions** | Viral titles, captions & hashtags tuned per platform |

All three share **one engine** (download → transcribe → render), so each feature
reuses the same building blocks.

## 🧱 Architecture

```
core/        shared engine
  config.py        settings (.env)
  downloader.py    yt-dlp wrapper            (Features 1 & 2)
  transcriber.py   faster-whisper            (Feature 1)
  moments.py       AI moment selection       (Feature 1)
  director.py      LLM edit plan + assemble  (Feature 3)
  renderer.py      ffmpeg: trim / 9:16 / captions (all)
  llm.py           local Ollama / cloud OpenAI
  captions.py      titles + captions + hashtags
  pipeline.py      high-level orchestrators
api/         FastAPI backend (main.py)
web/         React (Vite) frontend — 3 modes + download buttons
cli.py       command-line interface
```

## 🛠️ Tech (all free / open-source)

`yt-dlp` · `faster-whisper` · **Ollama** (local LLM) · `ffmpeg` / `moviepy` ·
`opencv` · `scenedetect` · `librosa` · `FastAPI` · `React`

## 🚀 Setup

### Prerequisites
- Python 3.10+
- [`ffmpeg`](https://ffmpeg.org/) on your PATH
- [Ollama](https://ollama.com) for free local AI (optional but recommended):
  ```bash
  ollama pull llama3.1
  ```

### Install
```bash
cd clipforge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit if you want cloud LLM instead of local
```

### Run the API
```bash
uvicorn clipforge.api.main:app --reload     # docs at http://localhost:8000/docs
```

### Run the web UI
```bash
cd web && npm install && npm run dev          # http://localhost:5173
```

### Or use the CLI
```bash
python -m clipforge.cli download "<url>" --start 70 --end 100
python -m clipforge.cli shorts "<url>" --count 3 --platform youtube
python -m clipforge.cli reel ./my_media "energetic 30s travel reel" --platform instagram
python -m clipforge.cli caption "we built an AI editor" --platform linkedin
```

## 🗺️ Roadmap

- [x] **v1** — Download + trim, basic shorts, media+prompt reels, titles/captions
- [ ] **v2** — LLM moment scoring, **face-tracking** 9:16 (MediaPipe), beat-synced cuts
- [ ] **v2** — Vision tagging of your media so the AI editor truly *understands* footage
- [ ] **v3** — Multi-platform repurpose (one asset → Short + Reel + LinkedIn + IG carousel)
- [ ] **v3** — Auto-publish (YouTube Data API / LinkedIn API)

### Future scopes (your channels)
- [ ] **⚽ Sports auto-update mode** — pull live scores/fixtures from a free sports
  API (e.g. football-data.org) → auto-generate **stats/score graphic reels**
  (no copyrighted footage needed). Great for daily World Cup content.
- [ ] **🏃 Running / fitness templates** — burn **distance/pace/time overlays**
  from a Strava/watch export onto your own run clips.
- [ ] **#️⃣ Niche presets** — saved tone + hashtag + caption styles per channel
  (travel, sports, running) for one-click on-brand posts.

## ⚖️ Legal / usage

Only download or edit content you **own**, that is **Creative Commons**, or that
you otherwise have rights to use. Respect each platform's Terms of Service.
This project is a creator productivity tool, not a piracy tool.

## 📄 License

MIT (see `LICENSE`).
