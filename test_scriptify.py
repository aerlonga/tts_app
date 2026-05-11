import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

url = "http://127.0.0.1:5000/scriptify"
payload = {
    "api_key": api_key,
    "url": "https://en.wikipedia.org/wiki/Battle_of_Midway"
}
response = requests.post(url, json=payload)
data = response.json()
print(f"Script length: {len(data.get('script', ''))}")
print(f"Image Prompts count: {len(data.get('image_prompts', []))}")
if len(data.get('image_prompts', [])) == 0:
    print("Full response from server:")
    # Wait, the server only returns script and image_prompts, we can't see the raw output
    # Let's see the end of the script to check if it has the marker
    script = data.get('script', '')
    print(script[-500:])
