"""Shared configuration loader for Image-Gen-WebUI.

Manages .env_* multi-profile config files and .env_current active marker.
Used by app.py, edit_image.py, and test_image_size.py.
"""
import os
from typing import Optional, Dict, List
from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_current_env() -> Optional[str]:
    """Read .env_current, return the active env filename or None."""
    path = os.path.join(PROJECT_ROOT, ".env_current")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        line = f.readline().strip()
    return line if line else None


def list_env_files() -> List[str]:
    """Return sorted list of .env_* filenames (excluding .env_current)."""
    files = []
    try:
        for f in os.listdir(PROJECT_ROOT):
            if f.startswith(".env_") and f != ".env_current":
                files.append(f)
    except OSError:
        pass
    files.sort()
    return files


def load_config(env_file: str) -> Dict[str, str]:
    """Parse a .env_<name> file into a dict."""
    path = os.path.join(PROJECT_ROOT, env_file)
    data = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    data[key.strip()] = value.strip()
    # Default provider_name from filename stem
    stem = env_file[5:]  # strip ".env_" prefix
    data.setdefault("provider_name", stem)
    return data


def load_current_config() -> Optional[Dict[str, str]]:
    """Load the config pointed to by .env_current. Returns None if not set."""
    env_file = get_current_env()
    if not env_file:
        return None
    return load_config(env_file)


def save_config(env_file: str, data: Dict[str, str]) -> None:
    """Write key=value lines to a .env_<name> file."""
    path = os.path.join(PROJECT_ROOT, env_file)
    with open(path, "w") as f:
        for key in ["provider_name", "base_url", "api_key", "model"]:
            value = data.get(key, "")
            f.write(f"{key}={value}\n")


def switch_env(env_file: str) -> None:
    """Update .env_current to point to the given env file."""
    path = os.path.join(PROJECT_ROOT, ".env_current")
    with open(path, "w") as f:
        f.write(env_file + "\n")


def get_client() -> OpenAI:
    """Build and return an OpenAI client from the current config.

    Raises RuntimeError if no config or missing required fields.
    """
    config = load_current_config()
    if not config:
        raise RuntimeError(
            "No active configuration. Create a .env_<name> profile via the Web UI."
        )
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "")
    if not api_key or not base_url:
        raise RuntimeError(
            "api_key and base_url are required in the active config."
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def mask_key(key: str) -> str:
    """Return masked key showing only first 3 and last 4 characters."""
    if not key:
        return ""
    if len(key) <= 6:
        return "*" * len(key)
    return key[:3] + "..." + key[-4:]
