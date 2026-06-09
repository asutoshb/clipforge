"""ClipForge core engine — shared building blocks for all features.

Modules:
    config        Settings loaded from environment / .env
    downloader    yt-dlp wrapper (Features 1 & 2)
    renderer      ffmpeg helpers: trim, reframe 9:16, burn captions (all features)
    llm           Provider-agnostic LLM client (local Ollama / cloud OpenAI)
    captions      Viral titles, captions & hashtags generator (all features)
    transcriber   faster-whisper transcription with word timestamps (Feature 1)
"""

__version__ = "0.1.0"
