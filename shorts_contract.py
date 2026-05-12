from __future__ import annotations

import json
import re


PRODUCTION_PACK_TEMPLATE_ID = "production_pack_v1"
PRODUCTION_PACK_SEGMENTS = (
    {"slot_index": 0, "asset_kind": "video", "duration_seconds": 8, "motion_preset": "flow_open"},
    {"slot_index": 1, "asset_kind": "image", "duration_seconds": 9, "motion_preset": "zoom_slow"},
    {"slot_index": 2, "asset_kind": "image", "duration_seconds": 10, "motion_preset": "pan_lateral"},
    {"slot_index": 3, "asset_kind": "image", "duration_seconds": 10, "motion_preset": "parallax_subtle"},
    {"slot_index": 4, "asset_kind": "image", "duration_seconds": 12, "motion_preset": "caption_emphasis"},
    {"slot_index": 5, "asset_kind": "image", "duration_seconds": 13, "motion_preset": "cta_hold"},
)

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
    """Keep the frontend contract stable even if the model omits optional fields."""
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
