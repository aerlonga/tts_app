from __future__ import annotations

import json
import os
import re

import requests


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
3. Use long, flowing paragraphs - NO bullet points, NO lists, NO headers inside the script body.
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
  - "cue": a short editorial label, such as "Opening Shot - Cold War dawn" or "Act 2 - The Chase"
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
  {"timestamp": "00:34", "cue": "Act 1", "prompt": "..."}
]
"""

SHORTS_SYSTEM_PROMPT = """You are a senior vertical video scriptwriter for an American channel focused on military history, dark historical events, declassified programs, and geopolitical conflict.

Your task: derive short-form vertical video scripts from a long documentary script and return creative inputs for a manual production workflow.

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
11. For the production workflow, provide exactly 1 Flow video prompt and exactly 5 Whisk image prompts per short.
12. `caption_text` must be a punchy on-screen line for the fifth segment. `cta_text` must be a short final on-screen CTA for the sixth segment.

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
      "broll_keywords": ["keyword one", "keyword two", "keyword three"],
      "flow_video_prompt": "Vertical 9:16 cinematic video prompt for Flow.",
      "whisk_image_prompts": [
        {
          "cue": "Scene 1",
          "prompt": "Vertical 9:16 prompt for Whisk..."
        }
      ],
      "caption_text": "Short dramatic caption text",
      "cta_text": "Watch the full story"
    }
  ]
}
"""

PRODUCTION_PACK_TEMPLATE_ID = "production_pack_v1"
PRODUCTION_PACK_SEGMENTS = (
    {"slot_index": 0, "asset_kind": "video", "duration_seconds": 8, "motion_preset": "flow_open"},
    {"slot_index": 1, "asset_kind": "image", "duration_seconds": 9, "motion_preset": "zoom_slow"},
    {"slot_index": 2, "asset_kind": "image", "duration_seconds": 10, "motion_preset": "pan_lateral"},
    {"slot_index": 3, "asset_kind": "image", "duration_seconds": 10, "motion_preset": "parallax_subtle"},
    {"slot_index": 4, "asset_kind": "image", "duration_seconds": 12, "motion_preset": "caption_emphasis"},
    {"slot_index": 5, "asset_kind": "image", "duration_seconds": 13, "motion_preset": "cta_hold"},
)

STREAM_CHUNK_MAX_CHARS = 9500
STREAM_THROTTLE_SECONDS = 62
JOBS: dict[str, dict] = {}
MAX_AGE_SECS = 2 * 60 * 60

ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
SAFE_COLLECTIONS = {"nasa", "prelinger", "national-archives"}
PART_NAME_RE = re.compile(r"(?:^|[\s_-])(?:parte|part)\s*0*(\d+)(?=\D|$)", re.IGNORECASE)


def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    text = re.sub(r"\[\d{2}:\d{2}.*?\]", "", text)
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []

    def split_long_block(block: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+", block)
        if len(parts) == 1:
            parts = block.split()

        out: list[str] = []
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
                out.extend(part[index : index + max_chars] for index in range(0, len(part), max_chars))
                current = ""
        if current:
            out.append(current)
        return out

    for paragraph in paragraphs:
        if len(paragraph) < 10:
            continue
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
        else:
            chunks.extend(split_long_block(paragraph))

    return chunks


def natural_asset_sort_key(filename: str, fallback_index: int = 0):
    name = os.path.splitext(os.path.basename(filename or ""))[0].lower()
    part_match = PART_NAME_RE.search(name)
    if part_match:
        return (0, int(part_match.group(1)), name, fallback_index)

    natural_parts = [(0, int(part)) if part.isdigit() else (1, part) for part in re.split(r"(\d+)", name)]
    return (1, natural_parts, fallback_index)


def extract_json_block(text: str):
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    obj_start = cleaned.find("{")
    arr_start = cleaned.find("[")
    starts = [position for position in (obj_start, arr_start) if position != -1]
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


def _normalize_prompt_list(prompts: object) -> list[dict[str, str]]:
    parsed_prompts: list[dict[str, str]] = []
    for prompt in prompts or []:
        if isinstance(prompt, dict):
            parsed_prompts.append(
                {
                    "cue": str(prompt.get("cue", "")).strip(),
                    "prompt": str(prompt.get("prompt", "")).strip(),
                }
            )
        elif isinstance(prompt, str):
            parsed_prompts.append({"cue": "", "prompt": prompt.strip()})
    return [item for item in parsed_prompts if item["prompt"]]


def _build_production_pack(item: dict, image_prompts: list[dict[str, str]]) -> dict | None:
    flow_video_prompt = str(item.get("flow_video_prompt") or "").strip()
    whisk_prompts = _normalize_prompt_list(item.get("whisk_image_prompts"))
    if len(whisk_prompts) < 5:
        whisk_prompts.extend(image_prompts[: 5 - len(whisk_prompts)])
    whisk_prompts = whisk_prompts[:5]

    caption_text = str(item.get("caption_text") or item.get("hook") or "").strip()
    cta_text = str(item.get("cta_text") or item.get("cta") or "").strip()

    if not flow_video_prompt or len(whisk_prompts) != 5:
        return None
    if not caption_text or not cta_text:
        return None

    timeline_segments = []
    for segment in PRODUCTION_PACK_SEGMENTS:
        overlay_text = None
        if segment["slot_index"] == 4:
            overlay_text = caption_text
        elif segment["slot_index"] == 5:
            overlay_text = cta_text
        timeline_segments.append({**segment, "overlay_text": overlay_text})

    return {
        "template_id": PRODUCTION_PACK_TEMPLATE_ID,
        "flow_video_prompt": flow_video_prompt,
        "whisk_image_prompts": whisk_prompts,
        "timeline_segments": timeline_segments,
        "caption_text": caption_text,
        "cta_text": cta_text,
    }


def normalize_short_item(item: dict, index: int) -> dict:
    image_prompts = _normalize_prompt_list(item.get("image_prompts"))
    keywords = item.get("broll_keywords") or []
    keywords = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]

    return {
        "id": str(item.get("id") or f"short_{index + 1}"),
        "title": str(item.get("title") or f"Short {index + 1}").strip(),
        "hook": str(item.get("hook") or "").strip(),
        "script": str(item.get("script") or "").strip(),
        "cta": str(item.get("cta") or "").strip(),
        "image_prompts": image_prompts,
        "broll_keywords": keywords,
        "production_pack": _build_production_pack(item, image_prompts),
    }


def search_broll(keywords: list[str], collection: str = "prelinger") -> list[dict]:
    if collection not in SAFE_COLLECTIONS:
        collection = "prelinger"

    query = " ".join(keywords) + f" collection:{collection} mediatype:movies"
    params = {
        "q": query,
        "fl[]": ["identifier", "title", "description", "subject", "licenseurl"],
        "rows": 20,
        "output": "json",
    }
    response = requests.get(ARCHIVE_SEARCH, params=params, timeout=15)
    response.raise_for_status()
    docs = response.json()["response"]["docs"]

    results = []
    for doc in docs:
        identifier = doc["identifier"]
        license_url = doc.get("licenseurl", "")
        is_public_domain = "publicdomain" in license_url.lower()
        is_safe = collection in SAFE_COLLECTIONS or is_public_domain
        if not is_safe:
            continue

        try:
            metadata_response = requests.get(f"https://archive.org/metadata/{identifier}", timeout=5)
            metadata_response.raise_for_status()
            files = metadata_response.json().get("files", [])
            mp4_files = [file for file in files if file.get("name", "").lower().endswith(".mp4")]
            if not mp4_files:
                continue

            best_file = max(mp4_files, key=lambda file: int(file.get("size", 0)))
            filename = best_file["name"]
            results.append(
                {
                    "title": doc.get("title", ""),
                    "identifier": identifier,
                    "license": license_url or "public domain (collection)",
                    "download_url": f"https://archive.org/download/{identifier}/{filename}",
                    "thumb": f"https://archive.org/services/img/{identifier}",
                    "preview_url": f"https://archive.org/embed/{identifier}?autoplay=1",
                }
            )
        except Exception:
            continue

    return results[:10]
