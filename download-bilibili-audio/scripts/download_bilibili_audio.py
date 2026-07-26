#!/usr/bin/env python3
"""Download one Bilibili video's best audio stream with yt-dlp."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


FILE_MARKER = "__BILIBILI_AUDIO_FILE__:"
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the best audio stream from one Bilibili video.",
    )
    parser.add_argument("url", help="A bilibili.com or b23.tv video URL.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Destination directory (default: current directory).",
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER_SPEC",
        help="Pass a yt-dlp browser cookie spec, such as chrome or safari.",
    )
    return parser.parse_args()


def validate_bilibili_url(value: str) -> str:
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    is_bilibili = hostname == "bilibili.com" or hostname.endswith(".bilibili.com")
    is_short_link = hostname == "b23.tv" or hostname.endswith(".b23.tv")

    if parsed.scheme not in {"http", "https"} or not (is_bilibili or is_short_link):
        raise ValueError("URL must be an http(s) link on bilibili.com or b23.tv")
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


def build_command(args: argparse.Namespace, output_dir: Path) -> list[str]:
    command = [
        *yt_dlp_command(),
        "--no-playlist",
        "--no-progress",
        "--format",
        "bestaudio/best",
        "--output",
        str(output_dir / "%(title).180B [%(id)s].%(ext)s"),
        "--print",
        f"after_move:{FILE_MARKER}%(filepath)s",
    ]

    if args.cookies_from_browser:
        command.extend(["--cookies-from-browser", args.cookies_from_browser])

    command.append(args.url)
    return command


def extract_output_path(stdout: str) -> Path:
    marked_paths = [
        line.split(FILE_MARKER, 1)[1].strip()
        for line in stdout.splitlines()
        if FILE_MARKER in line
    ]
    if not marked_paths:
        raise RuntimeError("yt-dlp completed without reporting an output file")

    output_path = Path(marked_paths[-1]).expanduser()
    if not output_path.is_absolute():
        output_path = output_path.resolve()
    if not output_path.is_file():
        raise RuntimeError(f"yt-dlp reported a file that does not exist: {output_path}")
    return output_path


def main() -> int:
    args = parse_args()

    try:
        args.url = validate_bilibili_url(args.url)
        output_dir = args.output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        command = build_command(args, output_dir)
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"yt-dlp failed:\n{detail}")
        output_path = extract_output_path(result.stdout)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Downloaded audio: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
