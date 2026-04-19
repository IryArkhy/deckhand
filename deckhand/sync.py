import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from deckhand import ankiconnect, config, drive, logger

LAUNCH_TIMEOUT = 30
POLL_INTERVAL = 2


def _wait_for_ankiconnect() -> bool:
    elapsed = 0
    while elapsed < LAUNCH_TIMEOUT:
        if ankiconnect.ping():
            return True
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    return False


def run(on_need_folder: Callable[[], Optional[str]]) -> dict:
    """
    Run a full sync cycle.

    on_need_folder: called when the Drive folder cannot be auto-detected.
                    Must return the chosen folder path string, or None if cancelled.

    Returns {"imported": [deck_names], "exported": [deck_names]} on success.
    Raises RuntimeError with a human-readable message on failure.
    """
    logger.info("Sync started")

    # Ensure AnkiConnect is reachable, launching Anki if needed
    if not ankiconnect.ping():
        logger.info("Anki not running — launching...")
        subprocess.Popen(["open", "-a", "Anki"])
        if not _wait_for_ankiconnect():
            raise RuntimeError(
                f"Anki did not start within {LAUNCH_TIMEOUT} seconds. Please open Anki manually and try again."
            )
        logger.info("AnkiConnect ready")

    # Resolve the Drive folder
    folder = drive.get_folder_path()
    if folder is None:
        folder = on_need_folder()
        if folder is None:
            raise RuntimeError("No sync folder selected. Sync cancelled.")
        config.set_drive_folder(folder)

    # Discover local decks (top-level only) and Drive files
    local_decks = [d for d in ankiconnect.get_deck_names() if "::" not in d]
    apkg_files = drive.list_apkg_files(folder)
    logger.info(f"Local decks: {local_decks}")
    logger.info(f"Drive files: {[Path(f).name for f in apkg_files]}")

    # Import all Drive files into local collection
    imported: list[str] = []
    for apkg in apkg_files:
        ankiconnect.import_package(apkg)
        imported.append(Path(apkg).stem)
        logger.info(f"Imported: {Path(apkg).stem}")

    # Export all top-level local decks to Drive
    exported: list[str] = []
    for deck in local_decks:
        path = drive.apkg_path_for_deck(folder, deck)
        ankiconnect.export_package(deck, path)
        exported.append(deck)
        logger.info(f"Exported: {deck}")

    # Push merged state to AnkiWeb
    ankiconnect.sync()
    logger.info("AnkiWeb sync complete")

    summary = f"Done — {len(imported)} imported, {len(exported)} exported"
    logger.info(summary)
    return {"imported": imported, "exported": exported}
