from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_m4a.py"
SPEC = importlib.util.spec_from_file_location("prepare_m4a", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class PrepareM4ATests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def command(self, *args: str) -> None:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", *args],
            check=True,
            capture_output=True,
        )

    def make_cover(self, codec: str) -> Path:
        suffix = "jpg" if codec == "mjpeg" else "png"
        cover = self.root / f"cover.{suffix}"
        self.command(
            "-f",
            "lavfi",
            "-i",
            "color=c=navy:s=32x32",
            "-frames:v",
            "1",
            "-c:v",
            codec,
            str(cover),
        )
        return cover

    def make_fixture(self, name: str, cover_codec: str, fragmented: bool) -> Path:
        audio = self.root / f"{name}-audio.m4a"
        source = self.root / f"{name}.m4a"
        self.command(
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=44100:duration=1",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-metadata",
            "title=Fixture Song",
            "-metadata",
            "artist=Fixture Artist",
            "-metadata",
            "album=Fixture Album",
            "-metadata",
            "composer=Fixture Composer",
            "-metadata",
            "comment=Fixture provenance",
            "-movflags",
            "+faststart",
            "-brand",
            "M4A",
            str(audio),
        )
        cover = self.make_cover(cover_codec)
        self.command(
            "-i",
            str(audio),
            "-i",
            str(cover),
            "-map",
            "0:a:0",
            "-map",
            "1:v:0",
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
            str(source),
        )
        if fragmented:
            raw = source.read_bytes()
            ftyp = raw.find(b"ftyp")
            self.assertGreaterEqual(ftyp, 0)
            raw = raw[: ftyp + 4] + b"iso5" + raw[ftyp + 8 :]
            compatible = raw.find(b"M4A ", ftyp + 8)
            if compatible >= 0:
                raw = raw[:compatible] + b"dash" + raw[compatible + 4 :]
            source.write_bytes(raw + b"\x00\x00\x00\x08moof")
        return source

    def test_bilibili_dash_style_m4a_is_remuxed_without_audio_change(self) -> None:
        source = self.make_fixture("dash", "mjpeg", fragmented=True)
        before = MODULE.analyze(source)
        self.assertTrue(before["container"]["fragmented"])
        self.assertNotEqual(before["container"]["major_brand"], "M4A")

        output = self.root / "prepared.m4a"
        report = MODULE.prepare(source, output, force_remux=True)

        self.assertTrue(report["remuxed"])
        self.assertTrue(report["audio_bitstream_unchanged"])
        self.assertEqual(
            report["audio_stream_sha256_before"],
            report["audio_stream_sha256_after"],
        )
        self.assertTrue(report["after"]["compatible"])
        self.assertEqual(report["after"]["container"]["major_brand"], "M4A")
        self.assertFalse(report["after"]["container"]["fragmented"])

    def test_standard_m4a_is_copied_without_unneeded_remux(self) -> None:
        source = self.make_fixture("standard", "mjpeg", fragmented=False)
        self.assertTrue(MODULE.analyze(source)["compatible"])

        output = self.root / "standard-copy.m4a"
        report = MODULE.prepare(source, output, force_remux=False)

        self.assertFalse(report["remuxed"])
        self.assertTrue(report["audio_bitstream_unchanged"])

    def test_jpeg_and_png_attached_covers_survive(self) -> None:
        for codec in ("mjpeg", "png"):
            with self.subTest(codec=codec):
                source = self.make_fixture(codec, codec, fragmented=True)
                output = self.root / f"prepared-{codec}.m4a"
                report = MODULE.prepare(source, output, force_remux=True)
                self.assertEqual(report["after"]["cover"]["count"], 1)
                self.assertEqual(report["after"]["cover"]["codec"], codec)
                self.assertTrue(report["after"]["cover"]["attached_pic"])
                self.assertEqual(
                    report["before"]["metadata"], report["after"]["metadata"]
                )

    def test_hash_mismatch_stops_and_removes_candidate(self) -> None:
        source = self.make_fixture("mismatch", "mjpeg", fragmented=False)
        output = self.root / "must-not-survive.m4a"

        with patch.object(MODULE, "stream_hash", side_effect=["a", "b"]):
            with self.assertRaisesRegex(MODULE.PreparationError, "hash mismatch"):
                MODULE.prepare(source, output, force_remux=True)

        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
