from openai import OpenAI
from PIL import Image
from datetime import datetime
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
INPUT_IMAGE = "edit/input.png"
base_name = os.path.splitext(os.path.basename(INPUT_IMAGE))[0]
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_IMAGE = f"edit/{base_name}_edited_{timestamp}.png"

PROMPT = """
Edit this image according to the following instruction:
make the lighting more cinematic, improve overall detail, keep the original composition and subject identity.
"""

SIZE = "2048x1152"
QUALITY = "high"
# ==================

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

os.makedirs("edit", exist_ok=True)

if not os.path.exists(INPUT_IMAGE):
    print(f"Input image not found: {INPUT_IMAGE}")
    sys.exit(1)

try:
    with open(INPUT_IMAGE, "rb") as image_file:
        result = client.images.edit(
            model=MODEL,
            image=image_file,
            prompt=PROMPT,
            size=SIZE,
            quality=QUALITY,
        )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    with open(OUTPUT_IMAGE, "wb") as f:
        f.write(image_bytes)

    with Image.open(OUTPUT_IMAGE) as img:
        print(f"✅ Saved: {OUTPUT_IMAGE}")
        print(f"Actual size: {img.size[0]}x{img.size[1]}")

except Exception as e:
    print("❌ Image edit failed")
    print(e)
