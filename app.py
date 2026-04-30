from flask import Flask, request, render_template, send_from_directory, jsonify
import base64
import os
import sys
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from send2trash import send2trash

from config_manager import (
    get_current_env, list_env_files, load_config, load_current_config,
    save_config, switch_env, get_client, mask_key,
)

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

app = Flask(__name__)
client = None  # created lazily via ensure_client()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def ensure_client():
    """Create or return the global OpenAI client. Rebuilds on config change."""
    global client
    client = get_client()
    return client


# --- Image serving routes ---

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


# --- Main page ---

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":
        return render_template(
            "index.html",
            history=list_outputs(),
            no_config=(get_current_env() is None),
        )

    # POST: generate or edit image
    prompt = request.form.get("prompt", "").strip()
    size = request.form.get("size", "2048x1152")
    quality = request.form.get("quality", "auto")
    uploaded = request.files.get("image")

    # Load current config for the model name
    config = load_current_config()
    model = config.get("model", "openai/gpt-image-2") if config else "openai/gpt-image-2"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{OUTPUT_DIR}/output_{timestamp}.png"

    try:
        c = ensure_client()

        if uploaded and uploaded.filename:
            # Edit mode
            safe_name = secure_filename(uploaded.filename)
            input_path = f"{UPLOAD_DIR}/input_{timestamp}_{safe_name}"
            uploaded.save(input_path)

            with open(input_path, "rb") as f:
                result = c.images.edit(
                    model=model,
                    image=f,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                )

            mode = "Image edit"

        else:
            # Generate mode
            result = c.images.generate(
                model=model,
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


# --- Config API routes ---

@app.route("/api/config")
def api_config():
    current = get_current_env()
    files = list_env_files()
    show_key = request.args.get("show_key") == "1"

    if not current:
        return jsonify({
            "current": None,
            "data": None,
            "files": files,
            "no_config": True,
        })

    data = load_config(current)
    result = {
        "current": current,
        "data": {
            "provider_name": data.get("provider_name", ""),
            "base_url": data.get("base_url", ""),
            "api_key_masked": mask_key(data.get("api_key", "")),
            "model": data.get("model", ""),
        },
        "files": files,
        "no_config": False,
    }
    if show_key:
        result["data"]["api_key"] = data.get("api_key", "")
    return jsonify(result)


@app.route("/api/config/save", methods=["POST"])
def api_config_save():
    body = request.get_json()
    env_file = body.get("env_file", "").strip()
    provider_name = body.get("provider_name", "").strip()
    base_url = body.get("base_url", "").strip()
    api_key = body.get("api_key", "").strip()
    model = body.get("model", "").strip()

    if not env_file or not env_file.startswith(".env_"):
        return jsonify({"ok": False, "error": "Invalid env file name"}), 400
    if not base_url:
        return jsonify({"ok": False, "error": "base_url is required"}), 400
    if not api_key:
        return jsonify({"ok": False, "error": "api_key is required"}), 400
    if not model:
        return jsonify({"ok": False, "error": "model is required"}), 400

    save_config(env_file, {
        "provider_name": provider_name,
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    })

    # Rebuild client if saving to current env
    if get_current_env() == env_file:
        global client
        try:
            client = get_client()
        except Exception:
            pass

    return jsonify({"ok": True})


@app.route("/api/config/switch", methods=["POST"])
def api_config_switch():
    body = request.get_json()
    env_file = body.get("env_file", "").strip()

    if not env_file or env_file not in list_env_files():
        return jsonify({"ok": False, "error": "Profile not found"}), 404

    switch_env(env_file)
    global client
    client = get_client()

    data = load_config(env_file)
    return jsonify({
        "ok": True,
        "data": {
            "provider_name": data.get("provider_name", ""),
            "base_url": data.get("base_url", ""),
            "api_key_masked": mask_key(data.get("api_key", "")),
            "model": data.get("model", ""),
        },
    })


@app.route("/api/config/new", methods=["POST"])
def api_config_new():
    body = request.get_json()
    name = body.get("name", "").strip()

    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
    if not name:
        return jsonify({"ok": False, "error": "Invalid name"}), 400

    env_file = f".env_{name}"
    if env_file in list_env_files():
        return jsonify({"ok": False, "error": "Profile already exists"}), 409

    save_config(env_file, {
        "provider_name": name,
        "base_url": "",
        "api_key": "",
        "model": "",
    })
    return jsonify({"ok": True, "env_file": env_file})


if __name__ == "__main__":
    import signal as _signal
    import sys as _sys
    from socket import SOL_SOCKET, SO_REUSEADDR
    from werkzeug.serving import BaseWSGIServer

    # Allow immediate port reuse after shutdown
    _orig_init = BaseWSGIServer.__init__
    def _patched_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    BaseWSGIServer.__init__ = _patched_init

    # Ensure clean exit on Ctrl+C / termination
    def _shutdown(sig, frame):
        _sys.exit(0)
    _signal.signal(_signal.SIGINT, _shutdown)
    _signal.signal(_signal.SIGTERM, _shutdown)

    app.run(host="127.0.0.1", debug=False)
