#!/usr/bin/env python3
"""Embed verified metadata and cover art without transcoding audio."""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
from pathlib import Path

from mutagen import File, MutagenError
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, COMM, TALB, TCOM, TCON, TDRC, TEXT, TIT2, TPE1, TPE2
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis


ALLOWED_FIELDS = {
    "title",
    "artist",
    "album",
    "album_artist",
    "composer",
    "lyricist",
    "genre",
    "date",
    "comment",
}


def text_list(value: object, field: str) -> list[str]:
    values = value if isinstance(value, list) else [value]
    if not all(isinstance(item, str) and item.strip() for item in values):
        raise ValueError(f"{field} must contain non-empty strings")
    return [item.strip() for item in values]


def picture_from_bytes(raw: bytes) -> tuple[Picture, str]:
    if raw.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif raw.startswith(b"\x89PNG"):
        mime = "image/png"
    else:
        raise ValueError("cover must be JPEG or PNG")

    picture = Picture()
    picture.type = 3
    picture.mime = mime
    picture.desc = "Cover"
    picture.data = raw
    return picture, mime


def tag_mp4(audio: MP4, data: dict[str, object], cover: bytes | None) -> None:
    fields = {
        "title": "\xa9nam",
        "artist": "\xa9ART",
        "album": "\xa9alb",
        "album_artist": "aART",
        "composer": "\xa9wrt",
        "genre": "\xa9gen",
        "date": "\xa9day",
        "comment": "\xa9cmt",
    }
    for field, atom in fields.items():
        if field in data:
            audio[atom] = text_list(data[field], field)
    if "lyricist" in data:
        audio["----:com.apple.iTunes:LYRICIST"] = [
            value.encode("utf-8") for value in text_list(data["lyricist"], "lyricist")
        ]
    if cover is not None:
        _, mime = picture_from_bytes(cover)
        image_format = (
            MP4Cover.FORMAT_JPEG if mime == "image/jpeg" else MP4Cover.FORMAT_PNG
        )
        audio["covr"] = [MP4Cover(cover, imageformat=image_format)]


def tag_vorbis(
    audio: FLAC | OggOpus | OggVorbis,
    data: dict[str, object],
    cover: bytes | None,
) -> None:
    fields = {
        "title": "title",
        "artist": "artist",
        "album": "album",
        "album_artist": "albumartist",
        "composer": "composer",
        "lyricist": "lyricist",
        "genre": "genre",
        "date": "date",
        "comment": "comment",
    }
    for field, key in fields.items():
        if field in data:
            audio[key] = text_list(data[field], field)

    if cover is None:
        return

    picture, _ = picture_from_bytes(cover)
    if isinstance(audio, FLAC):
        audio.clear_pictures()
        audio.add_picture(picture)
    else:
        encoded = base64.b64encode(picture.write()).decode("ascii")
        audio["metadata_block_picture"] = [encoded]


def tag_mp3(audio: MP3, data: dict[str, object], cover: bytes | None) -> None:
    if audio.tags is None:
        audio.add_tags()

    frames = {
        "title": ("TIT2", TIT2),
        "artist": ("TPE1", TPE1),
        "album": ("TALB", TALB),
        "album_artist": ("TPE2", TPE2),
        "composer": ("TCOM", TCOM),
        "lyricist": ("TEXT", TEXT),
        "genre": ("TCON", TCON),
        "date": ("TDRC", TDRC),
    }
    for field, (frame_id, frame_type) in frames.items():
        if field in data:
            audio.tags.delall(frame_id)
            audio.tags.add(
                frame_type(encoding=3, text=text_list(data[field], field))
            )
    if "comment" in data:
        audio.tags.delall("COMM")
        audio.tags.add(
            COMM(
                encoding=3,
                lang="eng",
                desc="",
                text=text_list(data["comment"], "comment"),
            )
        )
    if cover is not None:
        _, mime = picture_from_bytes(cover)
        audio.tags.delall("APIC")
        audio.tags.add(
            APIC(encoding=3, mime=mime, type=3, desc="Cover", data=cover)
        )


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
        if not isinstance(data, dict) or not all(
            key in data for key in ("title", "artist")
        ):
            raise ValueError("metadata requires title and artist")
        if set(data) - ALLOWED_FIELDS:
            unknown = ", ".join(sorted(set(data) - ALLOWED_FIELDS))
            raise ValueError(f"unknown fields: {unknown}")

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

        audio = File(path)
        if audio is None:
            raise ValueError(f"unsupported audio container: {path.suffix}")
        cover = args.cover.read_bytes() if args.cover else None

        if isinstance(audio, MP4):
            tag_mp4(audio, data, cover)
        elif isinstance(audio, (FLAC, OggOpus, OggVorbis)):
            tag_vorbis(audio, data, cover)
        elif isinstance(audio, MP3):
            tag_mp3(audio, data, cover)
        else:
            raise ValueError(
                "unsupported tagged container; remux with stream copy to "
                "M4A, Ogg Opus, Ogg Vorbis, FLAC, or MP3"
            )
        audio.save()
    except (OSError, ValueError, json.JSONDecodeError, MutagenError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Tagged audio: {path}\nBackup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
