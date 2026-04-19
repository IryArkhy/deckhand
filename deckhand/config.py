from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".deckhand"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def get_drive_folder() -> str | None:
    return load().get("drive_folder")


def set_drive_folder(path: str) -> None:
    data = load()
    data["drive_folder"] = path
    save(data)
