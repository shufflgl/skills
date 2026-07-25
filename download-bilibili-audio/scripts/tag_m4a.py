#!/usr/bin/env python3
"""Embed verified metadata and cover art in an M4A file."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from mutagen.mp4 import MP4, MP4Cover


def text_list(value: object, field: str) -> list[str]:
    values = value if isinstance(value, list) else [value]
    if not all(isinstance(item, str) and item.strip() for item in values):
        raise ValueError(f"{field} must contain non-empty strings")
    return [item.strip() for item in values]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--cover", type=Path)
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Directory for the pre-tag backup (default: beside the audio).",
    )
    args = parser.parse_args()
    try:
        path = args.audio.expanduser().resolve(strict=True)
        data = json.loads(args.metadata.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not all(key in data for key in ("title", "artist")):
            raise ValueError("metadata requires title and artist")
        allowed = {"title", "artist", "album", "album_artist", "composer", "lyricist", "genre", "date", "comment"}
        if set(data) - allowed:
            raise ValueError(f"unknown fields: {', '.join(sorted(set(data) - allowed))}")
        backup_dir = (
            args.backup_dir.expanduser().resolve()
            if args.backup_dir
            else path.parent
        )
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{path.stem}.before-tags{path.suffix}"
        if backup.exists():
            raise FileExistsError(f"backup already exists: {backup}")
        shutil.copy2(path, backup)
        audio = MP4(path)
        fields = {"title": "\xa9nam", "artist": "\xa9ART", "album": "\xa9alb", "album_artist": "aART", "composer": "\xa9wrt", "genre": "\xa9gen", "date": "\xa9day", "comment": "\xa9cmt"}
        for field, atom in fields.items():
            if field in data:
                audio[atom] = text_list(data[field], field)
        if "lyricist" in data:
            audio["----:com.apple.iTunes:LYRICIST"] = [v.encode() for v in text_list(data["lyricist"], "lyricist")]
        if args.cover:
            raw = args.cover.read_bytes()
            kind = MP4Cover.FORMAT_JPEG if raw.startswith(b"\xff\xd8\xff") else MP4Cover.FORMAT_PNG if raw.startswith(b"\x89PNG") else None
            if kind is None:
                raise ValueError("cover must be JPEG or PNG")
            audio["covr"] = [MP4Cover(raw, imageformat=kind)]
        audio.save()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Tagged audio: {path}\nBackup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
