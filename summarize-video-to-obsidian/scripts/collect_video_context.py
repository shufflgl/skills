#!/usr/bin/env python3
"""Collect metadata and the best subtitle track for one Bilibili or YouTube video."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


SUPPORTED_SUFFIXES = (
    ".youtube.com",
    ".youtu.be",
    ".bilibili.com",
    ".b23.tv",
)
DEFAULT_LANGUAGES = ("zh-Hans", "zh-Hant", "zh", "en")
DEFAULT_TIMEOUT_SECONDS = 45
CUE_TIMESTAMP_RE = re.compile(
    r"^\s*((?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3})\s+-->\s+"
    r"(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3}"
)
TAG_RE = re.compile(r"<[^>]+>")
ASS_OVERRIDE_RE = re.compile(r"\{[^}]*\}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect metadata and the preferred manual or automatic subtitle "
            "track for one Bilibili or YouTube video."
        )
    )
    parser.add_argument("url", help="A Bilibili or YouTube video URL.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path instead of standard output.",
    )
    parser.add_argument(
        "--languages",
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated subtitle preference order.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER_SPEC",
        help="Pass a yt-dlp browser cookie spec, such as chrome or safari.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=(
            "Maximum seconds for each yt-dlp operation "
            f"(default: {DEFAULT_TIMEOUT_SECONDS})."
        ),
    )
    return parser.parse_args()


def validate_video_url(value: str) -> str:
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    supported = any(
        hostname == suffix[1:] or hostname.endswith(suffix)
        for suffix in SUPPORTED_SUFFIXES
    )
    if parsed.scheme not in {"http", "https"} or not supported:
        raise ValueError(
            "URL must be an http(s) Bilibili, b23.tv, YouTube, or youtu.be link"
        )
    return value


def yt_dlp_command() -> list[str]:
    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]
    uvx = shutil.which("uvx")
    if uvx:
        return [uvx, "--from", "yt-dlp", "yt-dlp"]
    raise RuntimeError(
        "yt-dlp is unavailable and uvx was not found; install yt-dlp or uv first"
    )


def run_yt_dlp(
    arguments: list[str], timeout_seconds: float
) -> subprocess.CompletedProcess[str]:
    if timeout_seconds <= 0:
        raise ValueError("timeout must be greater than zero")
    try:
        result = subprocess.run(
            [*yt_dlp_command(), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"yt-dlp timed out after {timeout_seconds:g} seconds"
        ) from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"yt-dlp failed:\n{detail}")
    return result


def cookie_arguments(browser_spec: str | None) -> list[str]:
    if not browser_spec:
        return []
    return ["--cookies-from-browser", browser_spec]


def fetch_metadata(
    url: str, browser_spec: str | None, timeout_seconds: float
) -> dict[str, Any]:
    result = run_yt_dlp(
        [
            "--no-playlist",
            "--no-progress",
            "--no-warnings",
            "--skip-download",
            "--dump-single-json",
            *cookie_arguments(browser_spec),
            url,
        ],
        timeout_seconds,
    )
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("yt-dlp returned invalid metadata JSON") from exc
    if not isinstance(metadata, dict):
        raise RuntimeError("yt-dlp returned an unexpected metadata payload")
    return metadata


def normalize_language(value: str) -> str:
    return value.lower().replace("_", "-")


def language_score(language: str, preferences: Iterable[str]) -> tuple[int, int]:
    normalized = normalize_language(language)
    for index, preference in enumerate(preferences):
        wanted = normalize_language(preference)
        if normalized == wanted:
            return (index, 0)
        if normalized.split("-", 1)[0] == wanted.split("-", 1)[0]:
            return (index, 1)
    return (10_000, 10_000)


def choose_subtitle(
    metadata: dict[str, Any], preferences: list[str]
) -> tuple[str, str] | None:
    fallbacks: list[tuple[str, str]] = []
    for field, source in (("subtitles", "manual"), ("automatic_captions", "automatic")):
        tracks = metadata.get(field) or {}
        if not isinstance(tracks, dict) or not tracks:
            continue
        fallbacks.append((next(iter(tracks)), source))
        ranked = sorted(
            (language_score(language, preferences), language)
            for language in tracks
        )
        if ranked and ranked[0][0][0] < 10_000:
            return ranked[0][1], source
    return fallbacks[0] if fallbacks else None


def download_subtitle(
    url: str,
    language: str,
    source: str,
    work_dir: Path,
    browser_spec: str | None,
    timeout_seconds: float,
) -> Path:
    write_flag = "--write-subs" if source == "manual" else "--write-auto-subs"
    output_template = str(work_dir / "subtitle.%(ext)s")
    run_yt_dlp(
        [
            "--no-playlist",
            "--no-progress",
            "--no-warnings",
            "--skip-download",
            write_flag,
            "--sub-langs",
            language,
            "--sub-format",
            "vtt/srt/ass/json3/best",
            "--output",
            output_template,
            *cookie_arguments(browser_spec),
            url,
        ],
        timeout_seconds,
    )
    files = sorted(path for path in work_dir.glob("subtitle*") if path.is_file())
    if not files:
        raise RuntimeError("yt-dlp reported subtitles but did not create a subtitle file")
    return files[0]


def deduplicate_lines(lines: Iterable[str]) -> list[str]:
    output: list[str] = []
    for raw in lines:
        line = re.sub(r"\s+", " ", html.unescape(raw)).strip()
        if not line:
            continue
        if output and line == output[-1]:
            continue
        if output and line.startswith(output[-1]) and len(line) > len(output[-1]):
            output[-1] = line
            continue
        output.append(line)
    return output


def clock_to_seconds(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    seconds = float(parts[-1])
    minutes = int(parts[-2])
    hours = int(parts[-3]) if len(parts) == 3 else 0
    return hours * 3600 + minutes * 60 + seconds


def parse_vtt_or_srt_payload(text: str) -> tuple[str, list[dict[str, Any]]]:
    cues: list[dict[str, Any]] = []
    current_start: float | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_start, current_lines
        if current_start is None:
            current_lines = []
            return
        values = deduplicate_lines(current_lines)
        cue_text = " ".join(values)
        if cue_text:
            if cues and cue_text.startswith(cues[-1]["text"]):
                cues[-1]["text"] = cue_text
            else:
                cues.append({"start_seconds": current_start, "text": cue_text})
        current_start = None
        current_lines = []

    for raw in text.splitlines():
        stripped = raw.strip()
        timestamp = CUE_TIMESTAMP_RE.match(stripped)
        if timestamp:
            flush()
            current_start = clock_to_seconds(timestamp.group(1))
            continue
        if not stripped:
            flush()
            continue
        if (
            stripped == "WEBVTT"
            or stripped.isdigit()
            or stripped.startswith(("NOTE", "Kind:", "Language:"))
        ):
            continue
        if current_start is not None:
            current_lines.append(TAG_RE.sub("", stripped))
    flush()
    transcript = "\n".join(deduplicate_lines(cue["text"] for cue in cues))
    return transcript, cues


def parse_vtt_or_srt(text: str) -> str:
    transcript, _ = parse_vtt_or_srt_payload(text)
    return transcript


def parse_ass(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        if not raw.startswith("Dialogue:"):
            continue
        parts = raw.split(",", 9)
        if len(parts) != 10:
            continue
        dialogue = parts[9].replace(r"\N", " ").replace(r"\n", " ")
        lines.append(ASS_OVERRIDE_RE.sub("", dialogue))
    return "\n".join(deduplicate_lines(lines))


def parse_json3(text: str) -> str:
    payload = json.loads(text)
    lines: list[str] = []
    for event in payload.get("events", []):
        segments = event.get("segs") or []
        value = "".join(str(segment.get("utf8", "")) for segment in segments)
        if value.strip():
            lines.append(value)
    return "\n".join(deduplicate_lines(lines))


def parse_xml(text: str) -> str:
    root = ET.fromstring(text)
    return "\n".join(deduplicate_lines("".join(node.itertext()) for node in root))


def parse_subtitle(path: Path) -> tuple[str, list[dict[str, Any]]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    suffix = path.suffix.lower()
    if suffix in {".vtt", ".srt"}:
        return parse_vtt_or_srt_payload(text)
    if suffix in {".ass", ".ssa"}:
        return parse_ass(text), []
    if suffix in {".json3", ".json"}:
        return parse_json3(text), []
    if suffix in {".srv1", ".srv2", ".srv3", ".ttml", ".xml"}:
        return parse_xml(text), []
    return parse_vtt_or_srt_payload(text)


def platform_name(metadata: dict[str, Any], url: str) -> str:
    extractor = str(metadata.get("extractor_key") or metadata.get("extractor") or "")
    hostname = (urlparse(url).hostname or "").lower()
    if "bili" in extractor.lower() or "bili" in hostname or hostname.endswith("b23.tv"):
        return "Bilibili"
    return "YouTube"


def project_metadata(
    metadata: dict[str, Any],
    requested_url: str,
    transcript: str,
    cues: list[dict[str, Any]],
    language: str | None,
    source: str,
) -> dict[str, Any]:
    chapters = []
    for chapter in metadata.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        chapters.append(
            {
                "start_time": chapter.get("start_time"),
                "end_time": chapter.get("end_time"),
                "title": chapter.get("title"),
            }
        )
    return {
        "platform": platform_name(metadata, requested_url),
        "video_id": metadata.get("id"),
        "canonical_url": metadata.get("webpage_url") or requested_url,
        "requested_url": requested_url,
        "video_title": metadata.get("title"),
        "creator": (
            metadata.get("channel")
            or metadata.get("uploader")
            or metadata.get("creator")
        ),
        "upload_date": metadata.get("upload_date"),
        "duration_seconds": metadata.get("duration"),
        "description": metadata.get("description"),
        "language": metadata.get("language"),
        "chapters": chapters,
        "transcript": {
            "source": source,
            "language": language,
            "text": transcript,
            "cues": cues,
        },
    }


def write_json(payload: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output is None:
        sys.stdout.write(rendered)
        return
    destination = output.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(destination)


def main() -> int:
    args = parse_args()
    try:
        url = validate_video_url(args.url)
        preferences = [
            item.strip() for item in args.languages.split(",") if item.strip()
        ]
        if not preferences:
            raise ValueError("--languages must include at least one language")
        metadata = fetch_metadata(
            url, args.cookies_from_browser, args.timeout_seconds
        )
        original_language = metadata.get("language")
        if original_language and original_language not in preferences:
            preferences.append(str(original_language))
        selected = choose_subtitle(metadata, preferences)
        transcript = ""
        cues: list[dict[str, Any]] = []
        language: str | None = None
        source = "none"
        if selected:
            language, source = selected
            with tempfile.TemporaryDirectory(prefix="video-context-") as temporary:
                subtitle = download_subtitle(
                    url,
                    language,
                    source,
                    Path(temporary),
                    args.cookies_from_browser,
                    args.timeout_seconds,
                )
                transcript, cues = parse_subtitle(subtitle)
        payload = project_metadata(
            metadata, url, transcript, cues, language, source
        )
        write_json(payload, args.output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
