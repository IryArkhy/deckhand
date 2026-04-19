import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".deckhand"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text())


def save(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def get_drive_folder() -> Optional[str]:
    return load().get("drive_folder")


def set_drive_folder(path: str) -> None:
    data = load()
    data["drive_folder"] = path
    save(data)
