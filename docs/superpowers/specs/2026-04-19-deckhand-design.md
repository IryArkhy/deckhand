# Deckhand — Design Spec

**Date:** 2026-04-19
**Status:** Approved

---

## Overview

Deckhand is a macOS menu bar app that merges Anki decks across Desktop, Mobile, and AnkiWeb. It uses AnkiConnect (a local HTTP API plugin for Anki desktop) and a Google Drive folder as a shared file drop zone for `.apkg` deck packages. The user triggers sync on demand; the app handles the rest.

---

## Goals

- Keep all Anki decks in sync across desktop, mobile, and AnkiWeb with a single click
- Handle new decks, updated decks (new/removed cards), and cross-device additions
- Provide clear feedback on success and failure via macOS notifications and a log window
- Be readable and well-structured for open source contributors

## Non-Goals

- Automatic/scheduled background sync
- Support for sync providers other than Google Drive
- Propagating card deletions via `.apkg` (deletions flow via AnkiWeb's native sync channel instead)
- iOS/Android automation (mobile steps remain manual)

---

## Architecture

A single `deckhand` Python package with six modules. Dependency direction is strictly one-way — nothing calls back up the chain. No circular imports, no shared mutable state between modules.

```
app.py
  └── sync.py
        ├── ankiconnect.py
        ├── drive.py
        ├── logger.py
        └── config.py
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | rumps menu bar UI — menu items, notifications, log window, file picker |
| `sync.py` | Orchestrator — calls other modules in the correct order, handles errors |
| `ankiconnect.py` | Thin HTTP wrapper around AnkiConnect at `localhost:8765` |
| `drive.py` | Google Drive folder — auto-detect path, read/write `.apkg` files |
| `config.py` | Persist settings to `~/.deckhand/config.json` |
| `logger.py` | Write timestamped log entries, expose recent lines for the log window |

---

## Data Flow

This is the exact sequence when the user clicks "Sync Now":

1. `app.py` calls `sync.run()`
2. `sync.py` calls `ankiconnect.ping()`
   - OK → continue
   - FAIL → launch Anki via `open -a Anki`, poll `ping()` every 2s, 30s timeout
     - Still failing after timeout → log error, show error notification, open log window, stop
3. `sync.py` calls `drive.get_folder_path()`
   - Found → continue
   - Not found → `app.py` shows native folder picker; user picks folder → `config.save(path)`; user cancels → stop
4. `sync.py` fetches:
   - `ankiconnect.get_deck_names()` → e.g. `[a, b, c]`
   - `drive.list_apkg_files()` → e.g. `[d.apkg, e.apkg]`
5. `sync.py` sets:
   - `to_import` = **all** `.apkg` files in Drive (always — handles new decks and updates)
   - `to_export` = **all** local decks (always — handles new decks and updates)
6. For each file in `to_import`: `ankiconnect.import_package(path)`
7. For each deck in `to_export`: `ankiconnect.export_package(deck_name, drive_path)`
   - **Export scope:** only top-level decks (no `::` in name). Exporting a parent deck includes all its subdecks, so exporting subdecks separately would create redundant `.apkg` files.
8. `ankiconnect.sync()` — triggers AnkiWeb sync
9. `logger.write(summary)`, success notification shown, menu timestamp updated

If any step in 6–8 raises an exception: log error with traceback, fire error notification, open log window, stop.

### Note on card deletions

`.apkg` files do not carry deletion records. Deletions propagate via AnkiWeb's native sync (step 8), which tracks deletions in Anki's internal `graves` table. This means:
- Cards added or edited on any device → sync correctly via `.apkg` (merge by `guid`, higher `mod` timestamp wins)
- Cards deleted on any device → sync correctly via AnkiWeb (step 8)

---

## Configuration & First-Run

Settings file: `~/.deckhand/config.json`

```json
{
  "drive_folder": "/Users/you/Library/CloudStorage/GoogleDrive-you@gmail.com/My Drive/AnkiSync"
}
```

**First-run detection:** absence of `config.json`.

**Auto-detection order** (checked on every launch until a path is saved):

1. `~/Library/CloudStorage/GoogleDrive-*/My Drive/` (Google Drive for Desktop, modern)
2. `~/Google Drive/My Drive/` (legacy path)
3. `~/Google Drive/` (older legacy path)

If exactly one match: create `AnkiSync/` subfolder there, save path, proceed silently.
If zero or multiple matches: show native folder picker. User selects folder → saved. User cancels → sync aborted.

**Changing the folder:** "Change Sync Folder..." menu item re-triggers the picker at any time.

---

## Logging & Error Handling

**Log file:** `~/.deckhand/deckhand.log` — plain text, timestamped lines, capped at 500 lines.

```
2026-04-19 14:32:01  INFO   Sync started
2026-04-19 14:32:01  INFO   Anki not running — launching...
2026-04-19 14:32:04  INFO   AnkiConnect ready
2026-04-19 14:32:04  INFO   Local decks: [a, b, c]
2026-04-19 14:32:04  INFO   Drive files: [d.apkg, e.apkg]
2026-04-19 14:32:05  INFO   Imported: d, e
2026-04-19 14:32:06  INFO   Exported: a, b, c
2026-04-19 14:32:07  INFO   AnkiWeb sync complete
2026-04-19 14:32:07  INFO   Done — 2 imported, 3 exported
```

**Log window:** "View Log" menu item opens a `rumps` window showing the last 100 lines. Refreshes each time it is opened.

**Error handling strategy:** all external calls (`ankiconnect`, `drive`, filesystem) are wrapped in try/except inside `sync.py`. On any exception:
1. Log error with full traceback
2. Fire macOS error notification with a short human-readable message
3. Open log window automatically
4. Stop — no partial states silently swallowed

---

## Testing

`pytest` + `unittest.mock`. No real Anki, filesystem, or Google Drive required in tests.

```
tests/
├── test_ankiconnect.py   # mock HTTP responses, verify each API call
├── test_drive.py         # mock filesystem, test path detection and file ops
├── test_config.py        # read/write/defaults using a temp directory
└── test_sync.py          # mock ankiconnect + drive, test orchestration logic
```

Key cases in `test_sync.py`:
- Anki not running → launches, polls, proceeds
- Anki not running → timeout after 30s → error + stop
- Drive folder not found → triggers folder picker callback
- Normal sync → imports all Drive files, exports all local decks, calls AnkiWeb sync
- Export fails mid-sync → stops, logs error, notifies

---

## Project Structure

```
deckhand/
├── deckhand/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── sync.py
│   ├── ankiconnect.py
│   ├── drive.py
│   ├── config.py
│   └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_ankiconnect.py
│   ├── test_drive.py
│   ├── test_config.py
│   └── test_sync.py
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-19-deckhand-design.md
├── scripts/
│   └── build.sh          # PyInstaller → .app bundle
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `rumps` | macOS menu bar app framework |
| `requests` | HTTP calls to AnkiConnect |
| `pytest` | Test runner |
| `pyinstaller` | Package into `.app` for distribution |
