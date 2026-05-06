import json
image_raw = """
```json
[
  "A dramatic black and white photorealistic image of the Battle of Midway. A chaotic scene...",
  "Another prompt"
]
```
"""
start = image_raw.find('[')
end = image_raw.rfind(']') + 1
if start != -1 and end > start:
    json_str = image_raw[start:end]
    print("Found JSON array:")
    print(json_str)
    try:
        prompts = json.loads(json_str)
        print("Parsed count:", len(prompts))
    except Exception as e:
        print("Error parsing:", e)
