#!/usr/bin/env python3
"""Inspect and stream-copy M4A files into a conservative Music-compatible MP4 layout."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


class PreparationError(RuntimeError):
    pass


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def require_tools() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise PreparationError(f"missing required tools: {', '.join(missing)}")


def probe(path: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ]
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise PreparationError("ffprobe did not return an object")
    return value


def top_level_boxes(path: Path) -> list[str]:
    boxes: list[str] = []
    size = path.stat().st_size
    with path.open("rb") as handle:
        offset = 0
        while offset + 8 <= size:
            handle.seek(offset)
            header = handle.read(8)
            if len(header) != 8:
                break
            box_size = int.from_bytes(header[:4], "big")
            box_type = header[4:8].decode("latin-1")
            header_size = 8
            if box_size == 1:
                extended = handle.read(8)
                if len(extended) != 8:
                    break
                box_size = int.from_bytes(extended, "big")
                header_size = 16
            elif box_size == 0:
                box_size = size - offset
            if box_size < header_size or offset + box_size > size:
                break
            boxes.append(box_type)
            offset += box_size
    return boxes


def stream_hash(path: Path) -> str:
    result = run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-c",
            "copy",
            "-f",
            "hash",
            "-hash",
            "sha256",
            "-",
        ]
    )
    line = result.stdout.strip()
    if not line.startswith("SHA256="):
        raise PreparationError("FFmpeg did not return an audio SHA-256")
    return line.split("=", 1)[1].lower()


def disposition(stream: dict[str, Any], key: str) -> bool:
    return bool((stream.get("disposition") or {}).get(key, 0))


def analyze(path: Path) -> dict[str, Any]:
    details = probe(path)
    fmt = details.get("format") or {}
    tags = {str(k).lower(): str(v) for k, v in (fmt.get("tags") or {}).items()}
    streams = details.get("streams") or []
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    covers = [stream for stream in video_streams if disposition(stream, "attached_pic")]
    real_video = [stream for stream in video_streams if not disposition(stream, "attached_pic")]
    boxes = top_level_boxes(path)
    major_brand = tags.get("major_brand", "").strip()
    compatible = tags.get("compatible_brands", "")
    fragmented = "moof" in boxes or "dash" in compatible.lower()
    faststart = "moov" in boxes and (
        "mdat" not in boxes or boxes.index("moov") < boxes.index("mdat")
    )
    audio = audio_streams[0] if len(audio_streams) == 1 else {}
    metadata_aliases = {
        "title": ("title",),
        "artist": ("artist",),
        "album": ("album",),
        "album_artist": ("album_artist", "album artist", "aartist"),
        "composer": ("composer",),
        "lyricist": ("lyricist",),
        "genre": ("genre",),
        "date": ("date", "year"),
        "comment": ("comment",),
    }
    metadata = {
        field: next((tags[key] for key in aliases if tags.get(key)), None)
        for field, aliases in metadata_aliases.items()
    }
    reasons: list[str] = []
    if len(audio_streams) != 1:
        reasons.append(f"expected one audio stream, found {len(audio_streams)}")
    if major_brand != "M4A":
        reasons.append(f"nonstandard major_brand={major_brand or 'missing'}")
    if "m4a" not in compatible.lower():
        reasons.append("compatible_brands does not advertise M4A")
    if not ({"isom", "iso2"} & {compatible[index : index + 4] for index in range(0, len(compatible), 4)}):
        reasons.append("compatible_brands lacks isom or iso2")
    if fragmented:
        reasons.append("fragmented MP4 or DASH layout")
    if not faststart:
        reasons.append("moov atom is not fast-start positioned")
    if real_video:
        reasons.append("contains a non-cover video stream")
    if len(covers) != 1:
        reasons.append(f"expected one attached cover stream, found {len(covers)}")
    elif covers[0].get("codec_name") not in {"mjpeg", "png"}:
        reasons.append(f"unsupported cover codec={covers[0].get('codec_name')}")
    for required in ("title", "artist"):
        if not tags.get(required):
            reasons.append(f"missing required {required} tag")

    return {
        "path": str(path),
        "file_size": path.stat().st_size,
        "container": {
            "format_name": fmt.get("format_name"),
            "major_brand": major_brand,
            "compatible_brands": compatible,
            "top_level_boxes": boxes,
            "fragmented": fragmented,
            "faststart": faststart,
        },
        "audio": {
            "codec": audio.get("codec_name"),
            "profile": audio.get("profile"),
            "sample_rate": int(audio["sample_rate"]) if audio.get("sample_rate") else None,
            "channels": audio.get("channels"),
            "channel_layout": audio.get("channel_layout"),
            "bit_rate": int(audio["bit_rate"]) if audio.get("bit_rate") else None,
            "duration": float(audio.get("duration") or fmt.get("duration") or 0),
        },
        "other_streams": [
            {
                "index": stream.get("index"),
                "type": stream.get("codec_type"),
                "codec": stream.get("codec_name"),
                "attached_pic": disposition(stream, "attached_pic"),
            }
            for stream in streams
            if stream.get("codec_type") != "audio"
        ],
        "cover": {
            "count": len(covers),
            "codec": covers[0].get("codec_name") if len(covers) == 1 else None,
            "attached_pic": len(covers) == 1,
        },
        "metadata": metadata,
        "compatible": not reasons,
        "compatibility_reasons": reasons,
    }


def validate_safe_input(report: dict[str, Any]) -> None:
    reasons = report["compatibility_reasons"]
    fatal = [
        reason
        for reason in reasons
        if reason.startswith("expected one audio")
        or reason == "contains a non-cover video stream"
        or reason.startswith("expected one attached cover")
        or reason.startswith("unsupported cover")
        or reason.startswith("missing required")
    ]
    if fatal:
        raise PreparationError("unsafe input: " + "; ".join(fatal))


def remux(source: Path, output: Path) -> None:
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-map",
            "0:v?",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            "-disposition:v:0",
            "attached_pic",
            "-movflags",
            "+faststart",
            "-brand",
            "M4A",
            str(output),
        ]
    )


def prepare(source: Path, output: Path, force_remux: bool) -> dict[str, Any]:
    if output.exists():
        raise PreparationError(f"output already exists: {output}")
    if source == output:
        raise PreparationError("source and output must differ")
    before = analyze(source)
    validate_safe_input(before)
    before_hash = stream_hash(source)
    remuxed = force_remux or not before["compatible"]
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if remuxed:
            remux(source, output)
        else:
            shutil.copy2(source, output)
        after_hash = stream_hash(output)
        if before_hash != after_hash:
            raise PreparationError(
                f"audio stream hash mismatch: before={before_hash} after={after_hash}"
            )
        after = analyze(output)
        if not after["compatible"]:
            raise PreparationError(
                "prepared output remains incompatible: "
                + "; ".join(after["compatibility_reasons"])
            )
        if before["metadata"] != after["metadata"]:
            changed = [
                field
                for field in before["metadata"]
                if before["metadata"][field] != after["metadata"][field]
            ]
            raise PreparationError(
                "verified metadata changed during preparation: " + ", ".join(changed)
            )
        if before["cover"] != after["cover"]:
            raise PreparationError("cover stream changed or was lost during preparation")
    except Exception:
        if output.exists():
            output.unlink()
        raise
    return {
        "source": str(source),
        "output": str(output),
        "remuxed": remuxed,
        "audio_stream_sha256_before": before_hash,
        "audio_stream_sha256_after": after_hash,
        "audio_bitstream_unchanged": True,
        "container_changed": remuxed,
        "before": before,
        "after": after,
    }


def resolved_existing(value: str) -> Path:
    return Path(value).expanduser().resolve(strict=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("input")
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("input")
    prepare_parser.add_argument("--output", required=True)
    prepare_parser.add_argument("--force-remux", action="store_true")
    args = parser.parse_args()
    try:
        require_tools()
        source = resolved_existing(args.input)
        if args.command == "inspect":
            result = analyze(source)
        else:
            output = Path(args.output).expanduser().resolve()
            result = prepare(source, output, args.force_remux)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError, PreparationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
