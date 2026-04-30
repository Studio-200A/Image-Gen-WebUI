from openai import OpenAI
from PIL import Image
import base64
import os
import sys
import json

# Disable proxy env vars for this script only
for key in [
    "http_proxy", "https_proxy", "all_proxy",
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
]:
    os.environ.pop(key, None)

# ===== Load credentials =====
CONFIG_FILE = "credentials.json"

if not os.path.exists(CONFIG_FILE):
    print("❌ credentials.json not found")
    sys.exit(1)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

API_KEY = config.get("api_key")
BASE_URL = config.get("base_url")
MODEL = config.get("model", "openai/gpt-image-2")

if not API_KEY or not BASE_URL:
    print("❌ api_key or base_url missing in credentials.json")
    sys.exit(1)

# ===== Config =====
PROMPT = "A cinematic futuristic city skyline at sunset, ultra detailed, sharp, wallpaper composition"

SIZES_TO_TEST = [
    # "1024x1024",
    # "1536x1024",
    # "1024x1536",
    "2048x1152",
    # "2048x2048",
    # "3840x2160",
    # "2160x3840",
]

QUALITY = "high"
# ==================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

os.makedirs("outputs", exist_ok=True)

for size in SIZES_TO_TEST:
    print(f"\nTesting size: {size}")

    try:
        result = client.images.generate(
            model=MODEL,
            prompt=PROMPT,
            size=size,
            quality=QUALITY,
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        output_path = f"outputs/test_{size}.png"

        with open(output_path, "wb") as f:
            f.write(image_bytes)

        with Image.open(output_path) as img:
            actual_size = img.size

        print(f"✅ Success: requested {size}, actual {actual_size[0]}x{actual_size[1]}")
        print(f"Saved: {output_path}")

    except Exception as e:
        print(f"❌ Failed: {size}")
        print(e)
