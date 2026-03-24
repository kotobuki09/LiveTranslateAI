"""
json_config.py — Persistent user settings stored in config.json.

Path resolution strategy (PyInstaller-safe):
  1. When running as a frozen .exe, use the directory that contains the .exe
     (sys.executable), NOT __file__ which points to the _MEIPASS temp dir.
  2. If that directory is read-only (e.g. C:\\Program Files), fall back to
     %APPDATA%\\LiveTranslate\\config.json so we never crash on PermissionError.
  3. When running from source (python main.py), use the project root as before.
"""
import json
import sys
import os
from pathlib import Path


def _resolve_config_path() -> Path:
    """Return the best writable path for config.json."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle — use the folder that holds the .exe
        exe_dir = Path(sys.executable).parent
    else:
        # Running from source — use project root (two levels up from this file)
        exe_dir = Path(__file__).parent.parent

    candidate = exe_dir / "config.json"

    # Quick write-permission probe
    try:
        candidate.touch(exist_ok=True)
        return candidate
    except (PermissionError, OSError):
        pass

    # Fallback: %APPDATA%\LiveTranslate\config.json
    appdata = Path(os.environ.get("APPDATA", Path.home())) / "LiveTranslate"
    appdata.mkdir(parents=True, exist_ok=True)
    return appdata / "config.json"


CONFIG_FILE = _resolve_config_path()


def load_settings() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_settings(settings: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except OSError as e:
        # Log but don't crash — settings simply won't persist this session
        print(f"[json_config] Could not save settings to {CONFIG_FILE}: {e}")

