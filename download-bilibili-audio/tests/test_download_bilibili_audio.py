from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "download_bilibili_audio.py"
)
SPEC = importlib.util.spec_from_file_location("download_bilibili_audio", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DownloadBilibiliAudioTests(unittest.TestCase):
    def test_accepts_bilibili_and_short_links(self) -> None:
        urls = (
            "https://www.bilibili.com/video/BV1GJ411x7h7/",
            "https://b23.tv/example",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(MODULE.validate_bilibili_url(url), url)

    def test_rejects_non_bilibili_link(self) -> None:
        with self.assertRaisesRegex(ValueError, "bilibili.com or b23.tv"):
            MODULE.validate_bilibili_url("https://example.com/video")

    def test_source_download_does_not_request_transcoding(self) -> None:
        args = MODULE.argparse.Namespace(
            url="https://www.bilibili.com/video/BV1GJ411x7h7/",
            cookies_from_browser=None,
        )
        with patch.object(MODULE, "yt_dlp_command", return_value=["yt-dlp"]):
            command = MODULE.build_command(args, Path("/tmp/output"))

        self.assertIn("bestaudio/best", command)
        self.assertNotIn("--extract-audio", command)
        self.assertNotIn("--audio-format", command)
        self.assertIn("--no-playlist", command)

    def test_extracts_existing_absolute_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audio_path = Path(directory) / "audio.m4a"
            audio_path.touch()
            stdout = f"{MODULE.FILE_MARKER}{audio_path}\n"

            self.assertEqual(MODULE.extract_output_path(stdout), audio_path)


if __name__ == "__main__":
    unittest.main()
