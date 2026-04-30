# Image-Gen-WebUI

A lightweight local web UI for text-to-image generation and image editing using an OpenAI-compatible API. Runs entirely on localhost — no images or credentials leave your machine beyond the API provider.

## How It Works

```
 Browser (127.0.0.1:5000)
        │
   ┌────▼────┐     credentials.json      ┌────────────────┐
   │  Flask   │◄──────────────────────────│  API Provider  │
   │ (app.py) │     OpenAI SDK            │  (remote)      │
   └────┬─────┘                           └────────────────┘
        │
   ┌────▼────┐     ┌────────┐
   │ outputs/│     │uploads/│
   └─────────┘     └────────┘
```

1. User opens `http://127.0.0.1:5000` and fills in a prompt
2. **Text → Image**: Flask calls `client.images.generate()` via the configured API provider
3. **Image → Image**: User uploads an image → Flask calls `client.images.edit()`
4. API returns a base64-encoded PNG → Flask decodes and saves to `outputs/`
5. Result page shows the image with download link and history gallery

## Features

- Text-to-image generation
- Image editing / variation with prompt
- Resolution support: 1024x1024 up to 3840x2160
- Quality selection (standard / high)
- History gallery (last 20 generated images)
- Lightbox preview, one-click download
- Delete to trash (uses system trash instead of permanent removal)
- Loading indicator during generation
- Prompt copy helper

## Quick Start

```bash
./run.sh
```

The script will auto-detect python3, create a `.venv` virtual environment, install dependencies, start the server, and open your browser.

## Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open: http://127.0.0.1:5000

## Configuration

Create `credentials.json` in the project root:

```json
{
  "api_key": "YOUR_API_KEY",
  "base_url": "https://api.example.com/v1",
  "model": "openai/gpt-image-2"
}
```

This file is git-ignored. Never commit or share it.

## Project Structure

```
Image-Gen-WebUI/
├── app.py                 # Flask web server (main entry point)
├── edit_image.py          # CLI script for batch image editing
├── test_image_size.py     # Test script for checking supported resolutions
├── run.sh                 # One-click startup script
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Single-page web UI (Jinja2 template)
├── credentials.json       # API credentials (git-ignored)
├── outputs/               # Generated images (git-ignored)
├── uploads/               # Uploaded source images (git-ignored)
└── edit/                  # edit_image.py output directory (git-ignored)
```

## Scripts Reference

### `app.py` — Web UI

Main application. Serves the web interface and handles all API calls.

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Serve the web interface |
| `/` | POST | Generate or edit an image |
| `/outputs/<path>` | GET | Serve a generated image file |
| `/delete` | POST | Move an image to system trash |

### `edit_image.py` — CLI Image Editing

Command-line tool that reads an image from `edit/input.png`, sends it to the API with a cinematic enhancement prompt, and saves the result to `edit/`.

### `test_image_size.py` — Resolution Tester

Tests which image sizes the API supports. Edit `SIZES_TO_TEST` in the script to configure.

## Dependencies

- **Flask** (≥3.0) — web framework
- **openai** (≥1.0) — OpenAI SDK for API communication
- **send2trash** (≥1.8) — safe delete to system trash bin
- **Pillow** — image resolution verification (optional, used by test/edit scripts)

## Security

- Server binds to **127.0.0.1 only** — not accessible from the network
- `debug=False` — Werkzeug debugger console is disabled
- `credentials.json`, `outputs/`, `uploads/`, `edit/` are all **git-ignored**
- Proxy environment variables are stripped at startup to prevent request leakage
- This is a **personal local tool** — not intended for multi-user or networked deployment
