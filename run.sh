#!/usr/bin/env bash

# Run the Image-Gen-WebUI server
# This script assumes it lives in the project root

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR"

echo "Starting Image-Gen-WebUI..."
echo "Project directory: $SCRIPT_DIR"

# Detect python3
PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "python3 not found. Please install Python 3."
  read -p "Press enter to close..."
  exit 1
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  "$PYTHON_BIN" -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Ensure clean shutdown on exit (including Ctrl+C)
cleanup() {
  kill $APP_PID 2>/dev/null || true
  wait $APP_PID 2>/dev/null || true
  deactivate 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies..."
  python -m pip install -r requirements.txt
fi

python app.py &
APP_PID=$!

# Give Flask a moment to start then open browser
sleep 1
gio open http://127.0.0.1:5000

wait $APP_PID

read -p "Press enter to close..."
