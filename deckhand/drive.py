from __future__ import annotations

import glob
import os
from pathlib import Path

from deckhand import config

CANDIDATE_PATTERNS = [
    str(Path.home() / "Library" / "CloudStorage" / "GoogleDrive-*" / "My Drive"),
    str(Path.home() / "Google Drive" / "My Drive"),
    str(Path.home() / "Google Drive"),
]
SUBFOLDER = "AnkiSync"


def _find_gdrive_roots() -> list[str]:
    results = []
    for pattern in CANDIDATE_PATTERNS:
        results.extend(glob.glob(pattern))
    return results


def get_folder_path() -> str | None:
    saved = config.get_drive_folder()
    if saved and Path(saved).exists():
        return saved
    roots = _find_gdrive_roots()
    if len(roots) == 1:
        folder = Path(roots[0]) / SUBFOLDER
        folder.mkdir(exist_ok=True)
        config.set_drive_folder(str(folder))
        return str(folder)
    return None


def list_apkg_files(folder: str) -> list[str]:
    return [str(p) for p in Path(folder).glob("*.apkg")]


def apkg_path_for_deck(folder: str, deck_name: str) -> str:
    safe_name = deck_name.replace(os.sep, "_").replace(":", "_")
    return str(Path(folder) / f"{safe_name}.apkg")
