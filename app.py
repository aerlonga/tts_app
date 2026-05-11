from flask import Flask, request, jsonify, send_file, render_template_string, Response, stream_with_context
from google import genai
from google.genai import types
import wave, io, os, glob
import base64
import json
import time
import subprocess
import shutil
import tempfile
import uuid
import re

app = Flask(__name__)

# ─── Temp directories ────────────────────────────────────────────────────────

TMP_SESSIONS = "/tmp/tts_sessions"
TMP_JOBS     = "/tmp/tts_jobs"

HTML = open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8").read()

# ─── FFmpeg check ───────────────────────────────────────────────────────────

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("[WARN] FFmpeg não encontrado. A Fase 3 (montagem de vídeo) não estará disponível.")
        return False
    return True

FFMPEG_AVAILABLE = check_ffmpeg()

# ─── System Prompts ──────────────────────────────────────────────────────────

ENHANCE_SYSTEM_PROMPT = """You are a professional voiceover director.
Your task is to receive a raw text script and rewrite it with natural intonation markup in natural language,
inserted INLINE within the text, in parentheses.

Rules:
- Use markup such as: (with enthusiasm), (short pause), (long pause), (emphasizing), (calm tone), (serious tone),
  (with curiosity), (slightly speeding up), (slowing down), (with energy), (softly), etc.
- Place the markup immediately BEFORE the sentence or word that should receive that intonation.
- Do not invent content, do not alter the original text other than adding the markup.
- Do not add comments, explanations, or code blocks. Return only the annotated script.
- Keep timestamps and script structure intact.
- The output MUST be in English.
"""

SCRIPTIFY_SYSTEM_PROMPT = """You are a professional scriptwriter for an American YouTube channel focused on military history, dark historical events, and geopolitical conflicts, targeting American veterans and history enthusiasts aged 35-65.

Your task: transform raw input text into a dramatic, engaging video script.

SCRIPT RULES:
1. Write ONLY in English, regardless of input language.
2. Target 2200-2400 words. HARD MAXIMUM: 2500 words, approximately 15 minutes of narration.
3. Use long, flowing paragraphs — NO bullet points, NO lists, NO headers inside the script body.
4. Open with a powerful hook: a dramatic scene, shocking statistic, or provocative question.
5. Maintain a tone of gravitas, patriotism, and historical curiosity throughout.
6. Use active voice. Avoid passive constructions.
7. Add dramatic pauses naturally by ending paragraphs with short, punchy sentences.
8. DO NOT invent facts. Dramatize what is in the source material, but stay truthful.
9. Use timestamps every ~30 seconds in the format [MM:SS - Section Name] to help with video editing.
10. Do not write beyond the 15:00 mark. The final timestamp must be 15:00 or earlier.

IMAGE PROMPTS RULES (append AFTER the script):
- Generate exactly 26 image prompts, one approximately every 34 seconds of narration.
- Each prompt MUST be a JSON object with three fields:
  - "timestamp": the [MM:SS] timestamp from the script where this image should appear
  - "cue": a short editorial label (e.g. "Opening Shot — Cold War dawn", "Act 2 — The Chase")
  - "prompt": the full image generation prompt in English
- Style: dramatic black and white photorealistic photography, 16:9 aspect ratio, cinematic lighting.
- Each prompt should describe a specific scene from the script at that timestamp.
- Image prompt timestamps must not go beyond [15:00].
- Format as a JSON array at the very end, after the marker: ===IMAGE_PROMPTS===

OUTPUT FORMAT:
[Full script text with timestamps]

===IMAGE_PROMPTS===
[
  {"timestamp": "00:00", "cue": "Opening Shot", "prompt": "dramatic aerial view..."},
  {"timestamp": "00:34", "cue": "Act 1", "prompt": "..."},
  ...
]
"""

SHORTS_SYSTEM_PROMPT = """You are a senior vertical video scriptwriter for an American channel focused on military history, dark historical events, declassified programs, and geopolitical conflict.

Your task: derive short-form vertical video scripts from a long documentary script.

RULES:
1. Write ONLY in English.
2. Return ONLY valid JSON. No markdown, no explanations, no code fences.
3. Generate exactly the requested number of vertical videos.
4. Follow the requested platform and duration window exactly.
5. Each vertical video must feel like a self-contained discovery hook, not a random excerpt.
6. Keep the tone dark, cinematic, factual, and serious.
7. Start each script with a strong hook in the first sentence.
8. End each script with a short CTA that points viewers to the full documentary.
9. Do not invent facts beyond the source script.
10. Use plain narration text. No timestamps, no bullet points inside the script.

Return this JSON shape:
{
  "shorts": [
    {
      "id": "short_1",
      "title": "Short title under 70 characters",
      "hook": "The opening hook sentence.",
      "script": "Full narrated script for the Short.",
      "cta": "Short CTA sentence.",
      "image_prompts": [
        {
          "cue": "Opening shot",
          "prompt": "Vertical 9:16 black and white photorealistic cinematic image prompt..."
        }
      ],
      "broll_keywords": ["keyword one", "keyword two", "keyword three"]
    }
  ]
}
"""

# ─── Chunking ─────────────────────────────────────────────────────────────────

STREAM_CHUNK_MAX_CHARS = 9500
STREAM_THROTTLE_SECONDS = 62

def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    """
    Divide o texto em chunks por parágrafo e quebra blocos longos sem
    ultrapassar o limite de caracteres.
    """
    text = re.sub(r'\[\d{2}:\d{2}.*?\]', '', text) 

    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []

    def split_long_block(block: str) -> list[str]:
        parts = re.split(r'(?<=[.!?])\s+', block)
        if len(parts) == 1:
            parts = block.split()

        out = []
        current = ""
        for part in parts:
            candidate = f"{current} {part}".strip()
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                out.append(current)
            if len(part) <= max_chars:
                current = part
            else:
                out.extend(part[i:i + max_chars] for i in range(0, len(part), max_chars))
                current = ""
        if current:
            out.append(current)
        return out

    for para in paragraphs:
        if len(para) < 10:
            continue
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            chunks.extend(split_long_block(para))

    return chunks

# ─── FFmpeg video assembly — Ken Burns Two-Pass ──────────────────────────────

import threading
import requests as http_requests  # avoid conflict with flask.request

# ── Job tracking ──
JOBS: dict[str, dict] = {}
MAX_AGE_SECS = 2 * 60 * 60  # 2 hours

PART_NAME_RE = re.compile(r"(?:^|[\s_-])(?:parte|part)\s*0*(\d+)(?=\D|$)", re.IGNORECASE)

def natural_asset_sort_key(filename: str, fallback_index: int = 0):
    """
    Sort assets by prompt/image sequence names such as "parte 1", "parte 02",
    "part 13". Falls back to natural filename sorting for older naming styles.
    """
    name = os.path.splitext(os.path.basename(filename or ""))[0].lower()
    part_match = PART_NAME_RE.search(name)
    if part_match:
        return (0, int(part_match.group(1)), name, fallback_index)

    natural_parts = [
        (0, int(part)) if part.isdigit() else (1, part)
        for part in re.split(r"(\d+)", name)
    ]
    return (1, natural_parts, fallback_index)

def get_video_encoder() -> tuple:
    """
    Detecta se NVENC está disponível e retorna o encoder + flags corretos.
    Fallback automático para libx264 se não houver GPU Nvidia.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=10
        )
        if "h264_nvenc" in result.stdout:
            gpu = subprocess.run(
                ["nvidia-smi"],
                capture_output=True, text=True, timeout=5
            )
            if gpu.returncode == 0:
                return "h264_nvenc", ["-cq", "23", "-preset", "p4"]
    except Exception:
        pass
    return "libx264", ["-crf", "23", "-preset", "ultrafast"]


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds via ffprobe."""
    probe_result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_path],
        capture_output=True, text=True, timeout=30
    )
    probe_data = json.loads(probe_result.stdout)
    return float(probe_data['format']['duration'])


def extract_json_block(text: str):
    """Extract the first JSON object or array from a model response."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    obj_start = cleaned.find("{")
    arr_start = cleaned.find("[")
    starts = [pos for pos in (obj_start, arr_start) if pos != -1]
    if not starts:
        raise ValueError("Nenhum JSON encontrado na resposta do Gemini.")

    start = min(starts)
    closer = "}" if cleaned[start] == "{" else "]"
    end = cleaned.rfind(closer) + 1
    if end <= start:
        raise ValueError("JSON incompleto na resposta do Gemini.")

    json_str = cleaned[start:end]
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
    return json.loads(json_str)


def normalize_short_item(item: dict, index: int) -> dict:
    """Keep the frontend contract stable even if the model omits optional fields."""
    image_prompts = item.get("image_prompts") or []
    parsed_prompts = []
    for prompt in image_prompts:
        if isinstance(prompt, dict):
            parsed_prompts.append({
                "cue": str(prompt.get("cue", "")).strip(),
                "prompt": str(prompt.get("prompt", "")).strip(),
            })
        elif isinstance(prompt, str):
            parsed_prompts.append({"cue": "", "prompt": prompt.strip()})

    keywords = item.get("broll_keywords") or []
    keywords = [str(k).strip() for k in keywords if str(k).strip()]

    return {
        "id": str(item.get("id") or f"short_{index + 1}"),
        "title": str(item.get("title") or f"Short {index + 1}").strip(),
        "hook": str(item.get("hook") or "").strip(),
        "script": str(item.get("script") or "").strip(),
        "cta": str(item.get("cta") or "").strip(),
        "image_prompts": parsed_prompts,
        "broll_keywords": keywords,
    }


def assemble_video(audio_path: str, asset_paths: list[str], output_path: str,
                   job_id: str = None, format: str = "long") -> bool:
    """
    Ken Burns Two-Pass video assembly.

    Pass 1: Generate individual clips with zoompan effect (memory O(1) per clip).
    Pass 2: Concat demuxer joins all clips + audio without re-encoding video.

    Supports mixed assets: images (.jpg/.png) get Ken Burns, videos (.mp4/.mov) are used directly.
    """
    try:
        is_short = format == "short"
        out_w, out_h = (1080, 1920) if is_short else (1920, 1080)
        work_w, work_h = (out_w * 2, out_h * 2)
        total_duration = get_audio_duration(audio_path)
        job_dir = os.path.dirname(output_path)
        encoder, enc_flags = get_video_encoder()

        # Separate images from video clips
        image_indices = []
        video_indices = []
        for i, path in enumerate(asset_paths):
            ext = os.path.splitext(path)[1].lower()
            if ext in ('.mp4', '.mov', '.webm'):
                video_indices.append(i)
            else:
                image_indices.append(i)

        n = len(asset_paths)
        duration_per_asset = total_duration / n if n > 0 else total_duration

        clip_paths = []
        fps = 25

        # ── Pass 1: Generate individual clips ──
        for idx, asset_path in enumerate(asset_paths):
            ext = os.path.splitext(asset_path)[1].lower()
            clip_path = os.path.join(job_dir, f"clip_{idx:04d}.mp4")

            if ext in ('.mp4', '.mov', '.webm'):
                # Video clip: trim to duration, re-encode to match format
                if is_short:
                    vf = (
                        f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
                        f"crop={out_w}:{out_h},setsar=1"
                    )
                else:
                    vf = (
                        f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
                        f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2,setsar=1"
                    )
                cmd = [
                    'ffmpeg', '-y', '-i', asset_path,
                    '-t', str(duration_per_asset),
                    '-vf', vf,
                    '-r', str(fps),
                    '-c:v', encoder, *enc_flags,
                    '-an', '-pix_fmt', 'yuv420p',
                    clip_path
                ]
            else:
                # Image: Ken Burns zoompan effect
                # Alternate zoom in (even) / zoom out (odd)
                if idx % 2 == 0:
                    # Zoom IN: start at 1.0, zoom to 1.5
                    z_expr = "min(zoom+0.0015,1.5)"
                else:
                    # Zoom OUT: start at 1.5, zoom to 1.0
                    z_expr = "if(lte(zoom\\,1.0)\\,1.5\\,max(1.0\\,zoom-0.0015))"

                # Duration in frames for zoompan
                d_frames = int(duration_per_asset * fps)

                # Scale up first, then zoompan downscales to the final frame.
                if is_short:
                    base_filter = (
                        f"scale={work_w}:{work_h}:force_original_aspect_ratio=increase,"
                        f"crop={work_w}:{work_h},setsar=1,"
                    )
                else:
                    base_filter = (
                        f"scale={work_w}:{work_h}:force_original_aspect_ratio=decrease,"
                        f"pad={work_w}:{work_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
                    )

                vf_filter = (
                    base_filter
                    + f"zoompan=z='{z_expr}'"
                    f":x='iw/2-(iw/zoom/2)'"
                    f":y='ih/2-(ih/zoom/2)'"
                    f":d={d_frames}:s={out_w}x{out_h}:fps={fps}"
                )

                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1', '-i', asset_path,
                    '-vf', vf_filter,
                    '-t', str(duration_per_asset),
                    '-r', str(fps),
                    '-c:v', encoder, *enc_flags,
                    '-pix_fmt', 'yuv420p',
                    clip_path
                ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                print(f"[ERROR] Pass 1 clip {idx}: {result.stderr[-500:]}")
                return False

            clip_paths.append(clip_path)

            # Update job progress
            if job_id and job_id in JOBS:
                JOBS[job_id]["progress"] = (idx + 1) / (n + 1)  # reserve last slot for pass 2

            print(f"[Pass 1] Clip {idx+1}/{n} done: {os.path.basename(asset_path)}")

        # ── Pass 2: Concat all clips + audio ──
        clips_txt_path = os.path.join(job_dir, "clips.txt")
        with open(clips_txt_path, "w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")

        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0', '-i', clips_txt_path,
            '-i', audio_path,
            '-c:v', 'copy',  # clips already encoded — just copy
            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
            '-shortest',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            print(f"[ERROR] Pass 2 concat: {result.stderr[-500:]}")
            return False

        if job_id and job_id in JOBS:
            JOBS[job_id]["progress"] = 1.0

        print(f"[Pass 2] Final video assembled: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] assemble_video: {e}")
        return False


# ─── Cleanup worker ──────────────────────────────────────────────────────────

def cleanup_worker():
    """Background thread that cleans up old temp directories every 30 minutes."""
    while True:
        now = time.time()
        for base_dir in (TMP_JOBS, TMP_SESSIONS):
            if not os.path.exists(base_dir):
                continue
            try:
                for entry in os.scandir(base_dir):
                    if not entry.is_dir():
                        continue
                    age = now - entry.stat().st_mtime
                    if age > MAX_AGE_SECS:
                        shutil.rmtree(entry.path, ignore_errors=True)
                        JOBS.pop(entry.name, None)
                        print(f"[CLEANUP] Removed {entry.path} (age: {age/3600:.1f}h)")
            except Exception as e:
                print(f"[CLEANUP ERROR] {e}")
        time.sleep(30 * 60)  # check every 30 minutes


# ─── B-Roll Scraper (archive.org) ────────────────────────────────────────────

ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
SAFE_COLLECTIONS = {"nasa", "prelinger", "national-archives"}


def search_broll(keywords: list[str], collection: str = "prelinger") -> list[dict]:
    """Search archive.org for public domain video clips."""
    if collection not in SAFE_COLLECTIONS:
        collection = "prelinger"

    query = " ".join(keywords) + f" collection:{collection} mediatype:movies"
    params = {
        "q": query,
        "fl[]": ["identifier", "title", "description", "subject", "licenseurl"],
        "rows": 20,
        "output": "json",
    }
    r = http_requests.get(ARCHIVE_SEARCH, params=params, timeout=15)
    docs = r.json()["response"]["docs"]

    results = []
    for d in docs:
        identifier = d["identifier"]
        license_url = d.get("licenseurl", "")
        is_public_domain = "publicdomain" in license_url.lower()
        is_safe = collection in SAFE_COLLECTIONS or is_public_domain

        if not is_safe:
            continue

        # Fetch metadata to find the actual MP4 file
        try:
            meta_url = f"https://archive.org/metadata/{identifier}"
            meta_r = http_requests.get(meta_url, timeout=5)
            meta_data = meta_r.json()
            
            # Find the best MP4 file (prefer original or high quality)
            files = meta_data.get("files", [])
            mp4_files = [f for f in files if f.get("name", "").lower().endswith(".mp4")]
            
            if not mp4_files:
                continue # No MP4 found for this movie item

            # Pick the largest MP4 (usually the highest quality)
            best_file = max(mp4_files, key=lambda f: int(f.get("size", 0)))
            filename = best_file["name"]
            
            results.append({
                "title": d.get("title", ""),
                "identifier": identifier,
                "license": license_url or "public domain (collection)",
                "download_url": f"https://archive.org/download/{identifier}/{filename}",
                "thumb": f"https://archive.org/services/img/{identifier}",
                "preview_url": f"https://archive.org/embed/{identifier}?autoplay=1",
            })
        except Exception as e:
            print(f"[WARN] Error fetching metadata for {identifier}: {e}")
            continue

    return results[:10]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/enhance", methods=["POST"])
def enhance():
    """Step 1: use a text model to annotate the script with intonation cues."""
    data = request.json
    api_key = data.get("api_key", "").strip()
    text = data.get("text", "").strip()

    if not api_key:
        return jsonify({"error": "API Key do Gemini e obrigatoria."}), 400
    if not text:
        return jsonify({"error": "Texto nao pode estar vazio."}), 400

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=ENHANCE_SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        enhanced = response.text.strip()
        return jsonify({"enhanced_text": enhanced})
    except Exception as e:
        print(f"[ERROR] /enhance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    """Fallback para textos curtos — retorna WAV direto."""
    data = request.json
    api_key = data.get("api_key", "").strip()
    text = data.get("text", "").strip()
    voice = data.get("voice", "Charon")

    if not api_key:
        return jsonify({"error": "API Key do Gemini e obrigatoria."}), 400
    if not text:
        return jsonify({"error": "Texto nao pode estar vazio."}), 400

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    language_code="en-US",
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    )
                ),
            ),
        )

        audio_data = response.candidates[0].content.parts[0].inline_data.data

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        buf.seek(0)

        return send_file(buf, mimetype="audio/wav", as_attachment=False, download_name="audio.wav")

    except Exception as e:
        print(f"[ERROR] /generate: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/generate-stream", methods=["POST"])
def generate_stream():
    """TTS com chunking, progresso via SSE e checkpointing em disco."""
    data = request.json
    api_key = data.get("api_key", "").strip()
    text = data.get("text", "").strip()
    voice = data.get("voice", "Charon")
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not api_key:
        return jsonify({"error": "API Key do Gemini e obrigatoria."}), 400
    if not text:
        return jsonify({"error": "Texto nao pode estar vazio."}), 400

    def event_stream():
        # ── Session directory ──
        session_dir = os.path.join(TMP_SESSIONS, session_id)
        os.makedirs(session_dir, exist_ok=True)

        # Emit session event first so frontend can save it for retry
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

        # ── Deterministic chunking — persist on first run ──
        chunks_meta = os.path.join(session_dir, "chunks.json")
        if os.path.exists(chunks_meta):
            with open(chunks_meta, "r") as f:
                chunks = json.load(f)
        else:
            chunks = chunk_text(text, max_chars=STREAM_CHUNK_MAX_CHARS)
            with open(chunks_meta, "w") as f:
                json.dump(chunks, f)

        n = len(chunks)
        client = genai.Client(api_key=api_key)
        chunks_processed = 0

        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(session_dir, f"chunk_{i:04d}.pcm")

            # ── Checkpoint: skip if already on disk ──
            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                yield f"data: {json.dumps({'type': 'skipped', 'chunk': i + 1, 'total': n})}\n\n"
                chunks_processed += 1
                continue

            # Envia progresso
            progress_event = json.dumps({
                "type": "progress",
                "current": i + 1,
                "total": n,
                "preview": chunk[:80]
            })
            yield f"data: {progress_event}\n\n"

            try:
                response = client.models.generate_content(
                    # model="gemini-2.5-flash-preview-tts",
                    model="gemini-3.1-flash-tts-preview",
                    contents=chunk,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            language_code="en-US",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                            )
                        ),
                    ),
                )
                pcm_data = response.candidates[0].content.parts[0].inline_data.data

                # ── Save chunk to disk ──
                with open(chunk_path, "wb") as f:
                    f.write(pcm_data)
                chunks_processed += 1

                has_pending_chunks = any(
                    not (
                        os.path.exists(os.path.join(session_dir, f"chunk_{j:04d}.pcm")) and
                        os.path.getsize(os.path.join(session_dir, f"chunk_{j:04d}.pcm")) > 0
                    )
                    for j in range(i + 1, n)
                )
                if has_pending_chunks:
                    waiting_event = json.dumps({
                        "type": "waiting",
                        "seconds": STREAM_THROTTLE_SECONDS,
                        "chunk": i + 1,
                        "total": n
                    })
                    yield f"data: {waiting_event}\n\n"
                    time.sleep(STREAM_THROTTLE_SECONDS)

            except Exception as e:
                error_event = json.dumps({
                    "type": "error",
                    "chunk": i + 1,
                    "message": str(e)
                })
                yield f"data: {error_event}\n\n"
                print(f"[WARN] Chunk {i+1} falhou: {e}")
                continue

        # ── Final: read all .pcm from disk in order → WAV → base64 ──
        pcm_files = sorted(glob.glob(os.path.join(session_dir, "chunk_*.pcm")))
        if not pcm_files:
            error_event = json.dumps({"type": "error", "chunk": 0, "message": "Nenhum chunk processado com sucesso."})
            yield f"data: {error_event}\n\n"
            return

        combined_pcm = b"".join(open(f, "rb").read() for f in pcm_files)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(combined_pcm)
        buf.seek(0)
        wav_bytes = buf.read()
        audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")

        done_event = json.dumps({
            "type": "done",
            "audio_b64": audio_b64,
            "chunks_processed": chunks_processed
        })
        yield f"data: {done_event}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.route("/scriptify", methods=["POST"])
def scriptify():
    """Roteiriza um artigo a partir de uma URL usando newspaper3k + Gemini."""
    data = request.json
    api_key = data.get("api_key", "").strip()
    url = data.get("url", "").strip()

    if not api_key:
        return jsonify({"error": "API Key do Gemini é obrigatória."}), 400
    if not url or not url.startswith("http"):
        return jsonify({"error": "URL inválida. Deve começar com http(s)://"}), 400

    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        raw_text = article.text

        if len(raw_text) < 200:
            return jsonify({"error": "Não foi possível extrair conteúdo da URL. Tente outra URL."}), 400

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=raw_text,
            config=types.GenerateContentConfig(
                system_instruction=SCRIPTIFY_SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )

        full_response = response.text.strip()

        import re
        script_part = full_response
        image_raw = full_response
        image_prompts = []

        if "===IMAGE_PROMPTS===" in full_response:
            parts = full_response.split("===IMAGE_PROMPTS===", 1)
            script_part = parts[0].strip()
            image_raw = parts[1].strip()

        try:
            # Procura o array JSON
            start = image_raw.find('[')
            end = image_raw.rfind(']') + 1
            if start != -1 and end > start:
                json_str = image_raw[start:end]
                # Cleanup common JSON errors from LLMs
                json_str = re.sub(r',\s*]', ']', json_str) # Remove trailing commas
                
                try:
                    image_prompts = json.loads(json_str)
                    
                    # Se usou o fallback (sem marcador), limpa o script_part
                    if "===IMAGE_PROMPTS===" not in full_response:
                        script_part = full_response[:full_response.rfind('[')].strip()
                        
                except json.JSONDecodeError as e:
                    print(f"[WARN] Falha no JSON.loads: {e}")
                    print(f"[WARN] Conteudo problematico: {json_str}")
        except Exception as e:
            print(f"[WARN] Erro ao extrair blocos de imagem: {e}")

        # ── Parse image prompts (supports both dict and string formats) ──
        parsed_prompts = []
        raw_items = image_prompts if image_prompts else []
        for item in raw_items:
            if isinstance(item, dict) and "prompt" in item:
                parsed_prompts.append(item)
            elif isinstance(item, str):
                # Backward compatibility: plain string prompts
                parsed_prompts.append({"timestamp": "00:00", "cue": "", "prompt": item})

        return jsonify({
            "script": script_part,
            "image_prompts": parsed_prompts,
            "source_chars": len(raw_text)
        })

    except Exception as e:
        print(f"[ERROR] /scriptify: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/shorts/scriptify", methods=["POST"])
def shorts_scriptify():
    """Gera roteiros curtos derivados do roteiro longo."""
    data = request.json or {}
    api_key = data.get("api_key", "").strip()
    script = data.get("script", "").strip()

    try:
        count = int(data.get("count", 3))
    except Exception:
        count = 3
    count = 2 if count == 2 else 3

    try:
        duration_seconds = int(data.get("duration_seconds", 60))
    except Exception:
        duration_seconds = 60
    duration_seconds = duration_seconds if duration_seconds in (45, 60, 65) else 60
    platform = "TikTok Creator Rewards" if duration_seconds == 65 else "YouTube Shorts"
    duration_rule = (
        "Each TikTok script must be long enough for a final narrated video between 61 and 65 seconds. "
        "Do not make it shorter than 61 seconds."
        if duration_seconds == 65
        else f"Each YouTube Shorts script must fit safely within {duration_seconds} seconds."
    )

    if not api_key:
        return jsonify({"error": "API Key do Gemini é obrigatória."}), 400
    if len(script) < 500:
        return jsonify({"error": "Roteiro longo muito curto para derivar Shorts."}), 400

    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            f"Platform: {platform}.\n"
            f"Generate exactly {count} vertical videos.\n"
            f"{duration_rule}\n\n"
            f"LONG DOCUMENTARY SCRIPT:\n{script}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SHORTS_SYSTEM_PROMPT,
                temperature=0.65,
            ),
        )

        parsed = extract_json_block(response.text)
        raw_shorts = parsed if isinstance(parsed, list) else parsed.get("shorts", [])
        shorts = [
            normalize_short_item(item, i)
            for i, item in enumerate(raw_shorts)
            if isinstance(item, dict)
        ][:count]

        if not shorts:
            return jsonify({"error": "O Gemini não retornou Shorts válidos."}), 500

        return jsonify({
            "shorts": shorts,
            "count": len(shorts),
            "duration_seconds": duration_seconds,
        })

    except Exception as e:
        print(f"[ERROR] /shorts/scriptify: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/assemble", methods=["POST"])
def assemble():
    """Monta um MP4 a partir de WAV + imagens/vídeos via FFmpeg (background task)."""
    if not FFMPEG_AVAILABLE:
        return jsonify({"error": "FFmpeg não está instalado no servidor. Instale FFmpeg para usar esta funcionalidade."}), 503

    audio_file = request.files.get("audio")
    image_files = request.files.getlist("images")
    video_format = request.form.get("format", "long").strip().lower()
    if video_format not in ("long", "short"):
        return jsonify({"error": "Formato inválido. Use long ou short."}), 400

    manifest_str = request.form.get("manifest", "[]")
    try:
        manifest = json.loads(manifest_str)
    except Exception:
        manifest = []

    if not audio_file:
        return jsonify({"error": "Arquivo de áudio (WAV) é obrigatório."}), 400
    if not image_files and not manifest:
        return jsonify({"error": "Pelo menos 1 imagem/vídeo é obrigatório."}), 400
    if len(image_files) > 50:
        return jsonify({"error": "Máximo de 50 assets permitidos."}), 400

    # Validar mimetype do áudio
    audio_mime = audio_file.mimetype or ""
    audio_name = audio_file.filename or ""
    if not (audio_mime.startswith("audio/") or audio_name.lower().endswith(".wav")):
        return jsonify({"error": "O arquivo de áudio deve ser um WAV."}), 400

    # Validar imagens/vídeos
    valid_image_types = ("image/jpeg", "image/png")
    valid_video_types = ("video/mp4", "video/quicktime", "video/webm")
    valid_asset_exts = (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm")
    for img in image_files:
        filename = (img.filename or "").lower()
        if img.mimetype not in valid_image_types + valid_video_types and not filename.endswith(valid_asset_exts):
            return jsonify({"error": f"Arquivo inválido: {img.filename}. Aceitos: JPG, PNG, MP4, MOV, WebM."}), 400

    # ── Create job directory ──
    job_id = uuid.uuid4().hex
    job_dir = os.path.join(TMP_JOBS, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Save audio
    audio_path = os.path.join(job_dir, f"audio_{job_id}.wav")
    audio_file.save(audio_path)

    if manifest and all(item.get("type") == "upload" for item in manifest):
        manifest = [
            item for _, item in sorted(
                enumerate(manifest),
                key=lambda pair: natural_asset_sort_key(pair[1].get("filename", ""), pair[0])
            )
        ]

    asset_paths = []
    
    if manifest:
        # Use manifest for ordering
        uploaded_files = {f.filename: f for f in image_files if f.filename}
        for item in manifest:
            if item.get("type") == "upload":
                fname = item.get("filename")
                if fname in uploaded_files:
                    f = uploaded_files[fname]
                    ext = os.path.splitext(fname)[1].lower() or ".jpg"
                    path = os.path.join(job_dir, f"asset_{len(asset_paths):04d}{ext}")
                    f.save(path)
                    asset_paths.append(path)
            elif item.get("type") == "server":
                # Ensure it's a safe path (e.g., inside /tmp/broll)
                srv_path = item.get("path")
                if srv_path and srv_path.startswith("/tmp/broll/") and os.path.exists(srv_path):
                    ext = os.path.splitext(srv_path)[1].lower() or ".mp4"
                    path = os.path.join(job_dir, f"asset_{len(asset_paths):04d}{ext}")
                    # Copiamos ou linkamos. Copiar é mais seguro.
                    shutil.copy2(srv_path, path)
                    asset_paths.append(path)
    else:
        # Fallback: apenas arquivos anexados (comportamento antigo)
        ordered_files = [
            f for _, f in sorted(
                enumerate(image_files),
                key=lambda pair: natural_asset_sort_key(pair[1].filename or "", pair[0])
            )
        ]
        for i, f in enumerate(ordered_files):
            fname = f.filename or f"asset_{i}"
            ext = os.path.splitext(fname)[1].lower() or ".jpg"
            path = os.path.join(job_dir, f"asset_{len(asset_paths):04d}{ext}")
            f.save(path)
            asset_paths.append(path)

    if not asset_paths:
        return jsonify({"error": "Nenhum asset válido foi encontrado para montar o vídeo."}), 400

    output_path = os.path.join(job_dir, f"video_{job_id}.mp4")

    # ── Register job ──
    JOBS[job_id] = {
        "status": "processing",
        "progress": 0.0,
        "output_path": output_path,
        "format": video_format,
        "error": None,
        "created_at": time.time(),
    }

    # ── Background thread ──
    def run_job():
        try:
            success = assemble_video(
                audio_path, asset_paths, output_path,
                job_id=job_id, format=video_format
            )
            if success and os.path.exists(output_path):
                JOBS[job_id]["status"] = "done"
                JOBS[job_id]["progress"] = 1.0
            else:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = "FFmpeg falhou ao montar o vídeo."
        except Exception as e:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(e)
            print(f"[ERROR] Job {job_id}: {e}")

    t = threading.Thread(target=run_job, daemon=True)
    t.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/assemble/status/<job_id>", methods=["GET"])
def assemble_status(job_id):
    """Retorna o status e progresso de um job de montagem."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job não encontrado."}), 404

    result = {
        "status": job["status"],
        "progress": round(job["progress"], 3),
    }

    if job["status"] == "done":
        result["download_url"] = f"/assemble/download/{job_id}"
    elif job["status"] == "error":
        result["error"] = job["error"]

    return jsonify(result)


@app.route("/assemble/download/<job_id>", methods=["GET"])
def assemble_download(job_id):
    """Serve o MP4 finalizado de um job."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job não encontrado."}), 404
    if job["status"] != "done":
        return jsonify({"error": "Vídeo ainda não está pronto."}), 400
    if not os.path.exists(job["output_path"]):
        return jsonify({"error": "Arquivo de vídeo não encontrado."}), 404

    return send_file(
        job["output_path"],
        mimetype="video/mp4",
        as_attachment=True,
        download_name="short_final.mp4" if job.get("format") == "short" else "video_final.mp4"
    )


# ─── B-Roll Routes ───────────────────────────────────────────────────────────

@app.route("/broll/search", methods=["POST"])
def broll_search():
    """Pesquisa clips de vídeo de domínio público no archive.org."""
    data = request.json or {}
    keywords = data.get("keywords", [])
    collection = data.get("collection", "prelinger")

    if not keywords:
        return jsonify({"error": "Palavras-chave são obrigatórias."}), 400

    try:
        clips = search_broll(keywords, collection)
        return jsonify({"clips": clips})
    except Exception as e:
        print(f"[ERROR] /broll/search: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/broll/download", methods=["POST"])
def broll_download():
    """Download de um clip do archive.org para uso local."""
    data = request.json or {}
    url = data.get("url", "").strip()

    if not url or not url.startswith("https://archive.org/"):
        return jsonify({"error": "URL inválida. Deve ser do archive.org."}), 400

    try:
        filename = url.split("/")[-1]
        broll_dir = "/tmp/broll"
        os.makedirs(broll_dir, exist_ok=True)
        dest = os.path.join(broll_dir, filename)

        with http_requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return jsonify({"local_path": dest, "filename": filename})
    except Exception as e:
        print(f"[ERROR] /broll/download: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Start cleanup worker thread
    threading.Thread(target=cleanup_worker, daemon=True).start()

    print("\n[TTS Studio v2.0] Rotas disponíveis:")
    print("  GET  /                        → Interface principal")
    print("  POST /enhance                 → Entonação inteligente")
    print("  POST /generate                → TTS curto, retorna WAV")
    print("  POST /generate-stream         → TTS longo com checkpointing + SSE")
    print("  POST /scriptify               → Roteirizar URL → Script + Image Prompts")
    print("  POST /shorts/scriptify        → Roteiro longo → Shorts")
    print("  POST /assemble                → Montar vídeo (background task, retorna job_id)")
    print("  GET  /assemble/status/<id>    → Status + progresso do job")
    print("  GET  /assemble/download/<id>  → Download do MP4 finalizado")
    print("  POST /broll/search            → Pesquisar B-Roll no archive.org")
    print("  POST /broll/download          → Download de clip do archive.org")
    print()
    app.run(debug=False, port=5000)
