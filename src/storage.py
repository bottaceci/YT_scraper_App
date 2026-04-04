from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import sys

APP_DIR_NAME = "channel-watcher"
SEEN_FILENAME = "seen_videos.json"
HISTORY_FILENAME = "successful_runs.json"
LEGACY_FILENAME = "dict.txt"
HISTORY_LIMIT = 5


def get_data_dir() -> Path:
    """Return a writable per-user data directory and force-create it."""
    if os.name == "nt":
        base = (os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or "").strip()
        if not base:
            raise RuntimeError("Neither LOCALAPPDATA nor APPDATA is set.")
        path = Path(base) / APP_DIR_NAME.strip()
    else:
        path = Path.home() / ".local" / "share" / APP_DIR_NAME.strip()

    path.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        raise RuntimeError(f"Failed to create data directory: {path!r}")

    return path


def get_seen_file() -> Path:
    return get_data_dir() / SEEN_FILENAME


def get_history_file() -> Path:
    return get_data_dir() / HISTORY_FILENAME


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_seen_data() -> dict[str, Any]:
    return _read_json(get_seen_file(), {"version": 1, "channels": {}})


def save_seen_data(payload: dict[str, Any]) -> None:
    _write_json(get_seen_file(), payload)


def load_history_data() -> dict[str, Any]:
    return _read_json(get_history_file(), {"version": 1, "runs": []})


def save_history_data(payload: dict[str, Any]) -> None:
    _write_json(get_history_file(), payload)


def record_successful_run(run_payload: dict[str, Any]) -> None:
    if not run_payload.get("items"):
        return

    history = load_history_data()
    runs = history.get("runs", [])
    runs.insert(0, run_payload)
    history["runs"] = runs[:HISTORY_LIMIT]
    save_history_data(history)


def load_legacy_seen_by_title() -> dict[str, list[str]]:
    """Fallback import for the user's original dict.txt format."""
    candidate_paths = [
        Path.cwd() / LEGACY_FILENAME,
        Path(__file__).resolve().parent / LEGACY_FILENAME,
        Path(__file__).resolve().parent.parent / LEGACY_FILENAME,
        get_data_dir() / LEGACY_FILENAME,
    ]

    for path in candidate_paths:
        if not path.exists():
            continue
        payload = _read_json(path, {})
        if isinstance(payload, dict):
            cleaned: dict[str, list[str]] = {}
            for key, value in payload.items():
                if isinstance(key, str) and isinstance(value, list):
                    cleaned[key] = [str(item) for item in value]
            return cleaned
    return {}