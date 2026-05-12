import json
import math
import os
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from tests.support_google_stub import install_test_stubs

install_test_stubs()

from app.services.video_assembler import (
    assemble_video,
    is_ffmpeg_available,
    validate_template_manifest,
)


def _generate_dummy_wav(path: str, duration: float) -> None:
    sample_rate = 24000
    num_samples = int(sample_rate * duration)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            value = int(32767.0 * math.cos(2.0 * math.pi * 220.0 * (i / sample_rate)))
            wav_file.writeframesraw(struct.pack("<h", value))


def _run_ffmpeg(args: list[str]) -> None:
    import subprocess

    result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:])


def _generate_dummy_image(path: str, color: str) -> None:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=720x1280",
            "-frames:v",
            "1",
            path,
        ]
    )


def _generate_dummy_video(path: str, duration_seconds: int) -> None:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=720x1280:r=25",
            "-t",
            str(duration_seconds),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            path,
        ]
    )


def _probe_dimensions_and_duration(path: str) -> tuple[int, int, float]:
    import subprocess

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=width,height",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            path,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    parsed = json.loads(result.stdout)
    stream = parsed["streams"][0]
    duration = float(parsed["format"]["duration"])
    return int(stream["width"]), int(stream["height"]), duration


class VideoAssemblerTestCase(unittest.TestCase):
    def test_validate_template_manifest_rejects_wrong_order(self) -> None:
        manifest = [
            {"path": "/tmp/video.mp4", "slot_index": 0, "asset_kind": "video", "duration_seconds": 8, "motion_preset": "flow_open"},
            {"path": "/tmp/image1.jpg", "slot_index": 2, "asset_kind": "image", "duration_seconds": 9, "motion_preset": "zoom_slow"},
            {"path": "/tmp/image2.jpg", "slot_index": 2, "asset_kind": "image", "duration_seconds": 10, "motion_preset": "pan_lateral"},
            {"path": "/tmp/image3.jpg", "slot_index": 3, "asset_kind": "image", "duration_seconds": 10, "motion_preset": "parallax_subtle"},
            {"path": "/tmp/image4.jpg", "slot_index": 4, "asset_kind": "image", "duration_seconds": 12, "motion_preset": "caption_emphasis", "overlay_text": "Caption"},
            {"path": "/tmp/image5.jpg", "slot_index": 5, "asset_kind": "image", "duration_seconds": 13, "motion_preset": "cta_hold", "overlay_text": "CTA"},
        ]

        with self.assertRaisesRegex(ValueError, "ordem de slot_index"):
            validate_template_manifest(manifest)

    def test_validate_template_manifest_rejects_wrong_slot_duration(self) -> None:
        manifest = []
        for slot_index, (asset_kind, duration_seconds, preset) in {
            0: ("video", 7, "flow_open"),
            1: ("image", 9, "zoom_slow"),
            2: ("image", 10, "pan_lateral"),
            3: ("image", 10, "parallax_subtle"),
            4: ("image", 12, "caption_emphasis"),
            5: ("image", 13, "cta_hold"),
        }.items():
            manifest.append(
                {
                    "path": "/tmp/asset.mp4" if asset_kind == "video" else "/tmp/asset.jpg",
                    "slot_index": slot_index,
                    "asset_kind": asset_kind,
                    "duration_seconds": duration_seconds,
                    "motion_preset": preset,
                    "overlay_text": "Caption" if slot_index in (4, 5) else None,
                }
            )

        with self.assertRaisesRegex(ValueError, "8s"):
            validate_template_manifest(manifest)

    def test_generic_assembly_still_supports_vertical_render(self) -> None:
        if not is_ffmpeg_available():
            self.skipTest("FFmpeg/ffprobe are missing")

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.wav")
            image_path = os.path.join(tmpdir, "image.jpg")
            output_path = os.path.join(tmpdir, "short.mp4")
            _generate_dummy_wav(audio_path, duration=1.0)
            _generate_dummy_image(image_path, color="red")

            result = assemble_video(audio_path, [{"path": image_path}], output_path, video_format="short")

            self.assertTrue(result)
            width, height, duration = _probe_dimensions_and_duration(output_path)
            self.assertEqual((width, height), (1080, 1920))
            self.assertGreater(duration, 0.5)

    def test_template_assembly_renders_vertical_pack(self) -> None:
        if not is_ffmpeg_available():
            self.skipTest("FFmpeg/ffprobe are missing")

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.wav")
            video_path = os.path.join(tmpdir, "slot0.mp4")
            output_path = os.path.join(tmpdir, "pack.mp4")
            image_paths = [os.path.join(tmpdir, f"slot{i}.jpg") for i in range(1, 6)]

            _generate_dummy_wav(audio_path, duration=62.0)
            _generate_dummy_video(video_path, duration_seconds=8)
            for color, path in zip(("red", "blue", "green", "yellow", "purple"), image_paths):
                _generate_dummy_image(path, color=color)

            manifest = [
                {
                    "path": video_path,
                    "slot_index": 0,
                    "asset_kind": "video",
                    "duration_seconds": 8,
                    "motion_preset": "flow_open",
                }
            ]
            for slot_index, path in enumerate(image_paths, start=1):
                manifest.append(
                    {
                        "path": path,
                        "slot_index": slot_index,
                        "asset_kind": "image",
                        "duration_seconds": [9, 10, 10, 12, 13][slot_index - 1],
                        "motion_preset": ["zoom_slow", "pan_lateral", "parallax_subtle", "caption_emphasis", "cta_hold"][slot_index - 1],
                        "overlay_text": "Caption line" if slot_index == 4 else ("Watch full documentary" if slot_index == 5 else None),
                    }
                )

            result = assemble_video(audio_path, manifest, output_path, video_format="short")

            self.assertTrue(result)
            self.assertTrue(Path(output_path).exists())
            width, height, duration = _probe_dimensions_and_duration(output_path)
            self.assertEqual((width, height), (1080, 1920))
            self.assertGreater(duration, 61.0)
            self.assertLess(duration, 62.8)


if __name__ == "__main__":
    unittest.main()
