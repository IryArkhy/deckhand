# Deckhand

macOS menu bar app that keeps your Anki decks in sync across Desktop, Mobile, and AnkiWeb.

## How it works

1. Exports all local Anki decks to a Google Drive folder as `.apkg` files
2. Imports any `.apkg` files in that folder that are not yet in your local collection
3. Triggers an AnkiWeb sync to push the merged state to the cloud
4. Mobile users sync with AnkiWeb and import new `.apkg` files from the shared folder

Card additions and edits sync in both directions. Card deletions flow via AnkiWeb's native sync channel.

## Requirements

- macOS 12+
- [Anki desktop](https://apps.ankiweb.net/) with the [AnkiConnect plugin](https://ankiweb.net/shared/info/2055492159) installed
- Google Drive for Desktop

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
python -m deckhand
```

## Build .app

```bash
pip install pyinstaller
bash scripts/build.sh
```

## License

MIT
