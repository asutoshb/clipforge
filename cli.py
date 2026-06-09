"""ClipForge command-line interface.

Examples:
    python -m clipforge.cli download "<url>" --start 70 --end 100
    python -m clipforge.cli shorts "<url>" --count 3 --platform youtube
    python -m clipforge.cli reel ./my_media "energetic 30s travel reel"
    python -m clipforge.cli caption "we built an AI editor" --platform linkedin
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import captions, pipeline


def main() -> None:
    parser = argparse.ArgumentParser(prog="clipforge")
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="Feature 2: download / trim a video")
    d.add_argument("url")
    d.add_argument("--start", type=float, default=None)
    d.add_argument("--end", type=float, default=None)

    s = sub.add_parser("shorts", help="Feature 1: YouTube -> shorts")
    s.add_argument("url")
    s.add_argument("--count", type=int, default=3)
    s.add_argument("--aspect", default="9:16")
    s.add_argument("--platform", default="youtube")
    s.add_argument("--niche", default=None)

    r = sub.add_parser("reel", help="Feature 3: media + prompt -> short")
    r.add_argument("media_dir")
    r.add_argument("prompt")
    r.add_argument("--duration", type=float, default=30.0)
    r.add_argument("--aspect", default="9:16")
    r.add_argument("--platform", default="instagram")
    r.add_argument("--niche", default=None)

    c = sub.add_parser("caption", help="Generate titles/caption/hashtags")
    c.add_argument("text")
    c.add_argument("--platform", default="youtube")
    c.add_argument("--niche", default=None)

    args = parser.parse_args()

    if args.cmd == "download":
        out = pipeline.youtube_download(args.url, args.start, args.end)
    elif args.cmd == "shorts":
        out = pipeline.youtube_to_shorts(
            args.url, args.count, args.aspect, args.platform, args.niche)
    elif args.cmd == "reel":
        out = pipeline.media_prompt_to_short(
            Path(args.media_dir), args.prompt, args.duration,
            args.aspect, args.platform, args.niche)
    elif args.cmd == "caption":
        from dataclasses import asdict
        out = asdict(captions.generate_copy(
            args.text, platform=args.platform, niche=args.niche))
    else:  # pragma: no cover
        parser.error("unknown command")

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
