from flask import Flask, request, render_template, send_from_directory, jsonify
from openai import OpenAI
import base64
import os
import json
import sys
from datetime import datetime
from werkzeug.utils import secure_filename
from send2trash import send2trash

# Ensure the script runs inside the local .venv if it exists
VENV_PYTHON = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")
if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

# Disable proxy env vars
for key in [
    "http_proxy", "https_proxy", "all_proxy",
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
]:
    os.environ.pop(key, None)

# ===== Load credentials =====
CONFIG_FILE = "credentials.json"

if not os.path.exists(CONFIG_FILE):
    raise RuntimeError("❌ credentials.json not found")

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

API_KEY = config.get("api_key")
BASE_URL = config.get("base_url")
MODEL = config.get("model", "openai/gpt-image-2")

if not API_KEY or not BASE_URL:
    raise RuntimeError("❌ api_key or base_url missing in credentials.json")

# ============================

app = Flask(__name__)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Serve generated images
@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)

def list_outputs():
    try:
        files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")]
        files.sort(reverse=True)
        return [f"{OUTPUT_DIR}/{f}" for f in files[:20]]
    except Exception:
        return []

@app.route('/delete', methods=['POST'])
def delete_image():
    data = request.get_json()
    path = data.get("path")
    if not path:
        return jsonify({"ok": False})

    try:
        safe = os.path.basename(path)
        full = os.path.join(OUTPUT_DIR, safe)
        if os.path.exists(full):
            send2trash(full)
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False})

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":
        return render_template("index.html", history=list_outputs())

    prompt = request.form.get("prompt", "").strip()
    size = request.form.get("size", "2048x1152")
    quality = request.form.get("quality", "standard")
    uploaded = request.files.get("image")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{OUTPUT_DIR}/output_{timestamp}.png"

    try:
        if uploaded and uploaded.filename:
            # Edit mode
            safe_name = secure_filename(uploaded.filename)
            input_path = f"{UPLOAD_DIR}/input_{timestamp}_{safe_name}"
            uploaded.save(input_path)

            with open(input_path, "rb") as f:
                result = client.images.edit(
                    model=MODEL,
                    image=f,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                )

            mode = "Image edit"

        else:
            # Generate mode
            result = client.images.generate(
                model=MODEL,
                prompt=prompt,
                size=size,
                quality=quality,
            )

            mode = "Image generation"

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        with open(output_path, "wb") as f:
            f.write(image_bytes)

        return render_template(
            "index.html",
            output_image=output_path,
            error=None,
            prompt=prompt,
            mode=mode,
            history=list_outputs(),
        )

    except Exception as e:
        return render_template(
            "index.html",
            output_image=None,
            error=str(e),
            prompt=prompt,
            mode=None,
            history=list_outputs(),
        )

if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)
