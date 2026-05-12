import json
import unittest

from tests.support_google_stub import install_test_stubs

install_test_stubs()

from app.services.short_service import ShortService


class FakeGeminiService:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.last_kwargs: dict | None = None

    def generate_text(self, **kwargs) -> dict:
        self.last_kwargs = kwargs
        return {
            "text": json.dumps(self.payload),
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }


class ShortServiceTestCase(unittest.TestCase):
    def test_generate_shorts_keeps_legacy_shape_when_pack_is_missing(self) -> None:
        service = ShortService(
            gemini=FakeGeminiService(
                {
                    "shorts": [
                        {
                            "id": "short_1",
                            "title": "Legacy Short",
                            "hook": "A hook",
                            "script": "A script",
                            "cta": "Watch more",
                            "image_prompts": [{"cue": "Opening", "prompt": "legacy prompt"}],
                            "broll_keywords": ["archive"],
                        },
                        {
                            "id": "short_2",
                            "title": "Legacy Short 2",
                            "hook": "A second hook",
                            "script": "A second script",
                            "cta": "Watch the full documentary",
                            "image_prompts": [],
                            "broll_keywords": ["history"],
                        },
                    ]
                }
            )
        )

        result = service.generate_shorts(
            script="This is a long documentary script. " * 40,
            count=2,
            duration_seconds=60,
            api_key="fake-key",
        )

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["shorts"][0]["image_prompts"][0]["cue"], "Opening")
        self.assertIsNone(result["shorts"][0]["production_pack"])
        self.assertEqual(result["shorts"][1]["broll_keywords"], ["history"])

    def test_generate_shorts_builds_production_pack_with_safe_defaults(self) -> None:
        fake_gemini = FakeGeminiService(
            {
                "shorts": [
                    {
                        "id": "short_1",
                        "title": "Pack Short",
                        "hook": "They hid the weapon in plain sight.",
                        "script": "They hid the weapon in plain sight. The full documentary explains how.",
                        "cta": "Watch the full documentary.",
                        "image_prompts": [
                            {"cue": "Fallback 1", "prompt": "Fallback visual one"},
                            {"cue": "Fallback 2", "prompt": "Fallback visual two"},
                        ],
                        "broll_keywords": ["weapons", "vault"],
                        "flow_video_prompt": "Vertical cinematic tracking shot through a classified vault",
                        "whisk_image_prompts": [
                            {"cue": "Scene 1", "prompt": "Whisk visual one"},
                            {"cue": "Scene 2", "prompt": "Whisk visual two"},
                            {"cue": "Scene 3", "prompt": "Whisk visual three"},
                        ],
                    }
                ]
            }
        )
        service = ShortService(gemini=fake_gemini)

        result = service.generate_shorts(
            script="This is a long documentary script. " * 40,
            count=3,
            duration_seconds=60,
            api_key="fake-key",
        )

        production_pack = result["shorts"][0]["production_pack"]
        self.assertIsNotNone(production_pack)
        assert production_pack is not None
        self.assertEqual(production_pack["template_id"], "production_pack_v1")
        self.assertEqual(len(production_pack["whisk_image_prompts"]), 5)
        self.assertEqual(production_pack["caption_text"], "They hid the weapon in plain sight.")
        self.assertEqual(production_pack["cta_text"], "Watch the full documentary.")
        self.assertEqual(production_pack["timeline_segments"][4]["overlay_text"], production_pack["caption_text"])
        self.assertEqual(production_pack["timeline_segments"][5]["overlay_text"], production_pack["cta_text"])
        self.assertIn("Flow video prompt", fake_gemini.last_kwargs["system_instruction"])


if __name__ == "__main__":
    unittest.main()
