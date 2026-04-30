from PIL import Image
import base64
import os
import sys

from config_manager import load_current_config, get_client

# ===== Load credentials via config_manager =====
config = load_current_config()
if config is None:
    print("No active environment config found.")
    print("  Run the Web UI first to create a configuration,")
    print("  or create a .env_<name> file manually.")
    sys.exit(1)

API_KEY = config.get("api_key")
BASE_URL = config.get("base_url")
MODEL = config.get("model", "openai/gpt-image-2")

if not API_KEY or not BASE_URL:
    print("api_key and base_url are required in the active config.")
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

client = get_client()

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

        print(f"Success: requested {size}, actual {actual_size[0]}x{actual_size[1]}")
        print(f"Saved: {output_path}")

    except Exception as e:
        print(f"Failed: {size}")
        print(e)
