from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any


VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
TEMPLATE_SLOT_PRESETS = {
    0: ("video", 8, "flow_open"),
    1: ("image", 9, "zoom_slow"),
    2: ("image", 10, "pan_lateral"),
    3: ("image", 10, "parallax_subtle"),
    4: ("image", 12, "caption_emphasis"),
    5: ("image", 13, "cta_hold"),
}
TEMPLATE_DURATION_SECONDS = 62


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def get_video_encoder() -> tuple[str, list[str]]:
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if "h264_nvenc" in result.stdout:
            gpu = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if gpu.returncode == 0:
                return "h264_nvenc", ["-cq", "23", "-preset", "p4"]
    except Exception:
        pass
    return "libx264", ["-crf", "23", "-preset", "ultrafast"]


def get_audio_duration(audio_path: str) -> float:
    probe_result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    probe_data = json.loads(probe_result.stdout)
    return float(probe_data["format"]["duration"])


def _asset_ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def _is_video_asset(path: str) -> bool:
    return _asset_ext(path) in VIDEO_EXTENSIONS


def _normalize_assets(asset_inputs: list[dict[str, Any] | str]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for index, item in enumerate(asset_inputs):
        if isinstance(item, str):
            assets.append({"path": item, "index": index})
            continue

        normalized = dict(item)
        normalized.setdefault("index", index)
        normalized["path"] = str(normalized.get("path") or "")
        assets.append(normalized)
    return assets


def _uses_template_manifest(assets: list[dict[str, Any]]) -> bool:
    template_keys = {"slot_index", "asset_kind", "duration_seconds", "motion_preset"}
    return any(template_keys.intersection(asset.keys()) for asset in assets)


def uses_template_manifest(asset_inputs: list[dict[str, Any] | str]) -> bool:
    return _uses_template_manifest(_normalize_assets(asset_inputs))


def validate_template_manifest(asset_inputs: list[dict[str, Any] | str]) -> list[dict[str, Any]]:
    assets = _normalize_assets(asset_inputs)
    if len(assets) != len(TEMPLATE_SLOT_PRESETS):
        raise ValueError("Template production_pack_v1 exige exatamente 6 assets.")

    assets = sorted(assets, key=lambda asset: int(asset.get("slot_index", -1)))
    total_duration = 0

    for expected_slot, asset in enumerate(assets):
        slot_index = int(asset.get("slot_index", -1))
        if slot_index != expected_slot:
            raise ValueError("Assets do template precisam estar em ordem de slot_index de 0 a 5.")

        expected_kind, expected_duration, expected_preset = TEMPLATE_SLOT_PRESETS[expected_slot]
        asset_kind = str(asset.get("asset_kind") or "").strip().lower()
        motion_preset = str(asset.get("motion_preset") or "").strip()
        duration_seconds = int(asset.get("duration_seconds", 0) or 0)
        path = str(asset.get("path") or "")

        if asset_kind != expected_kind:
            raise ValueError(f"Slot {expected_slot} deve usar asset_kind='{expected_kind}'.")
        if duration_seconds != expected_duration:
            raise ValueError(f"Slot {expected_slot} deve durar {expected_duration}s.")
        if motion_preset != expected_preset:
            raise ValueError(f"Slot {expected_slot} deve usar preset '{expected_preset}'.")
        if not path:
            raise ValueError(f"Slot {expected_slot} nao possui arquivo associado.")
        if expected_kind == "video" and not _is_video_asset(path):
            raise ValueError(f"Slot {expected_slot} exige um arquivo de video.")
        if expected_kind == "image" and _is_video_asset(path):
            raise ValueError(f"Slot {expected_slot} exige um arquivo de imagem.")
        total_duration += duration_seconds

    if total_duration != TEMPLATE_DURATION_SECONDS:
        raise ValueError("Template production_pack_v1 exige soma total de 62 segundos.")
    return assets


def _scaled_template_durations(audio_duration: float) -> dict[int, float]:
    target_duration = max(audio_duration, TEMPLATE_DURATION_SECONDS)
    scale = target_duration / TEMPLATE_DURATION_SECONDS
    durations = {
        slot_index: expected_duration * scale
        for slot_index, (_, expected_duration, _) in TEMPLATE_SLOT_PRESETS.items()
    }
    drift = target_duration - sum(durations.values())
    durations[max(durations)] += drift
    return durations


def _resolve_output_size(video_format: str) -> tuple[int, int, int, int]:
    is_short = video_format == "short"
    out_w, out_h = (1080, 1920) if is_short else (1920, 1080)
    return out_w, out_h, out_w * 2, out_h * 2


def _build_video_scale_filter(out_w: int, out_h: int, is_short: bool) -> str:
    if is_short:
        return (
            f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
            f"crop={out_w}:{out_h},setsar=1"
        )
    return (
        f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
        f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )


def _build_image_base_filter(work_w: int, work_h: int, is_short: bool) -> str:
    if is_short:
        return (
            f"scale={work_w}:{work_h}:force_original_aspect_ratio=increase,"
            f"crop={work_w}:{work_h},setsar=1,"
        )
    return (
        f"scale={work_w}:{work_h}:force_original_aspect_ratio=decrease,"
        f"pad={work_w}:{work_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
    )


def _template_image_filter(
    preset: str,
    duration_seconds: float,
    out_w: int,
    out_h: int,
    work_w: int,
    work_h: int,
) -> str:
    fps = 25
    d_frames = max(int(duration_seconds * fps), 1)
    denom = max(d_frames - 1, 1)
    base_filter = _build_image_base_filter(work_w, work_h, True)

    if preset == "zoom_slow":
        motion = (
            "zoompan="
            "z='min(zoom+0.00075,1.18)'"
            ":x='iw/2-(iw/zoom/2)'"
            ":y='ih/2-(ih/zoom/2)'"
        )
    elif preset == "pan_lateral":
        motion = (
            "zoompan="
            "z='1.15'"
            f":x='(iw-iw/zoom)*(on/{denom})'"
            ":y='ih/2-(ih/zoom/2)'"
        )
    elif preset == "parallax_subtle":
        motion = (
            "zoompan="
            "z='min(zoom+0.00035,1.08)'"
            ":x='iw/2-(iw/zoom/2)'"
            f":y='ih*0.46-(ih/zoom/2)+(on/{denom})*24'"
        )
    elif preset == "caption_emphasis":
        motion = (
            "zoompan="
            "z='min(zoom+0.0009,1.12)'"
            ":x='iw/2-(iw/zoom/2)'"
            ":y='ih/2-(ih/zoom/2)'"
        )
    elif preset == "cta_hold":
        motion = (
            "zoompan="
            "z='min(zoom+0.00015,1.03)'"
            ":x='iw/2-(iw/zoom/2)'"
            ":y='ih/2-(ih/zoom/2)'"
        )
    else:
        raise ValueError(f"Preset de imagem nao suportado: {preset}")

    vf = (
        base_filter
        + motion
        + f":d={d_frames}:s={out_w}x{out_h}:fps={fps}"
    )
    return vf


def _run_ffmpeg(cmd: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _assemble_generic_video(
    audio_path: str,
    assets: list[dict[str, Any]],
    output_path: str,
    job_id: str | None = None,
    video_format: str = "long",
    jobs: dict[str, dict] | None = None,
) -> bool:
    is_short = video_format == "short"
    out_w, out_h, work_w, work_h = _resolve_output_size(video_format)
    total_duration = get_audio_duration(audio_path)
    job_dir = os.path.dirname(output_path)
    encoder, enc_flags = get_video_encoder()
    fps = 25
    n = len(assets)
    duration_per_asset = total_duration / n if n > 0 else total_duration
    clip_paths: list[str] = []

    for idx, asset in enumerate(assets):
        asset_path = asset["path"]
        ext = _asset_ext(asset_path)
        clip_path = os.path.join(job_dir, f"clip_{idx:04d}.mp4")

        if ext in VIDEO_EXTENSIONS:
            vf = _build_video_scale_filter(out_w, out_h, is_short)
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                asset_path,
                "-t",
                str(duration_per_asset),
                "-vf",
                vf,
                "-r",
                str(fps),
                "-c:v",
                encoder,
                *enc_flags,
                "-an",
                "-pix_fmt",
                "yuv420p",
                clip_path,
            ]
        else:
            z_expr = "min(zoom+0.0015,1.5)" if idx % 2 == 0 else "if(lte(zoom\\,1.0)\\,1.5\\,max(1.0\\,zoom-0.0015))"
            d_frames = int(duration_per_asset * fps)
            vf_filter = (
                _build_image_base_filter(work_w, work_h, is_short)
                + f"zoompan=z='{z_expr}'"
                ":x='iw/2-(iw/zoom/2)'"
                ":y='ih/2-(ih/zoom/2)'"
                f":d={d_frames}:s={out_w}x{out_h}:fps={fps}"
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                asset_path,
                "-vf",
                vf_filter,
                "-t",
                str(duration_per_asset),
                "-r",
                str(fps),
                "-c:v",
                encoder,
                *enc_flags,
                "-pix_fmt",
                "yuv420p",
                clip_path,
            ]

        result = _run_ffmpeg(cmd, timeout=600)
        if result.returncode != 0:
            print(f"[ERROR] Pass 1 clip {idx}: {result.stderr[-500:]}")
            return False

        clip_paths.append(clip_path)
        if job_id and jobs and job_id in jobs:
            jobs[job_id]["progress"] = (idx + 1) / (n + 1)

    return _concat_clips(audio_path, clip_paths, output_path, job_id=job_id, jobs=jobs)


def _assemble_template_video(
    audio_path: str,
    assets: list[dict[str, Any]],
    output_path: str,
    job_id: str | None = None,
    jobs: dict[str, dict] | None = None,
) -> bool:
    assets = validate_template_manifest(assets)
    job_dir = os.path.dirname(output_path)
    encoder, enc_flags = get_video_encoder()
    out_w, out_h, work_w, work_h = _resolve_output_size("short")
    fps = 25
    clip_paths: list[str] = []
    slot_durations = _scaled_template_durations(get_audio_duration(audio_path))

    for idx, asset in enumerate(assets):
        asset_path = asset["path"]
        clip_path = os.path.join(job_dir, f"clip_{idx:04d}.mp4")
        slot_index = int(asset["slot_index"])
        duration_seconds = slot_durations[slot_index]
        motion_preset = str(asset["motion_preset"])

        if motion_preset == "flow_open":
            vf = _build_video_scale_filter(out_w, out_h, True)
            cmd = [
                "ffmpeg",
                "-y",
                "-stream_loop",
                "-1",
                "-i",
                asset_path,
                "-t",
                f"{duration_seconds:.3f}",
                "-vf",
                vf,
                "-r",
                str(fps),
                "-c:v",
                encoder,
                *enc_flags,
                "-an",
                "-pix_fmt",
                "yuv420p",
                clip_path,
            ]
        else:
            vf = _template_image_filter(
                motion_preset,
                duration_seconds,
                out_w,
                out_h,
                work_w,
                work_h,
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                asset_path,
                "-vf",
                vf,
                "-t",
                f"{duration_seconds:.3f}",
                "-r",
                str(fps),
                "-c:v",
                encoder,
                *enc_flags,
                "-pix_fmt",
                "yuv420p",
                clip_path,
            ]

        result = _run_ffmpeg(cmd, timeout=900)
        if result.returncode != 0:
            print(f"[ERROR] Template clip {idx}: {result.stderr[-500:]}")
            return False

        clip_paths.append(clip_path)
        if job_id and jobs and job_id in jobs:
            jobs[job_id]["progress"] = (idx + 1) / (len(assets) + 1)

    return _concat_clips(audio_path, clip_paths, output_path, job_id=job_id, jobs=jobs)


def _concat_clips(
    audio_path: str,
    clip_paths: list[str],
    output_path: str,
    *,
    job_id: str | None = None,
    jobs: dict[str, dict] | None = None,
) -> bool:
    job_dir = os.path.dirname(output_path)
    clips_txt_path = os.path.join(job_dir, "clips.txt")
    with open(clips_txt_path, "w", encoding="utf-8") as file_obj:
        for clip_path in clip_paths:
            file_obj.write(f"file '{clip_path}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        clips_txt_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-shortest",
        output_path,
    ]
    result = _run_ffmpeg(cmd, timeout=3600)
    if result.returncode != 0:
        print(f"[ERROR] Pass 2 concat: {result.stderr[-500:]}")
        return False

    if job_id and jobs and job_id in jobs:
        jobs[job_id]["progress"] = 1.0
    return True


def assemble_video(
    audio_path: str,
    asset_inputs: list[dict[str, Any] | str],
    output_path: str,
    *,
    job_id: str | None = None,
    video_format: str = "long",
    jobs: dict[str, dict] | None = None,
) -> bool:
    try:
        assets = _normalize_assets(asset_inputs)
        if _uses_template_manifest(assets):
            return _assemble_template_video(audio_path, assets, output_path, job_id=job_id, jobs=jobs)
        return _assemble_generic_video(
            audio_path,
            assets,
            output_path,
            job_id=job_id,
            video_format=video_format,
            jobs=jobs,
        )
    except Exception as exc:
        print(f"[ERROR] assemble_video: {exc}")
        return False
