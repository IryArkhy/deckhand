# Deckhand

**A macOS menu bar app that keeps your Anki decks in sync across Desktop, Mobile, and AnkiWeb.**

Anki's built-in sync is replace-not-merge: whichever device synced last wins, and the other device's changes are discarded. Deckhand fixes this by using Google Drive as a neutral merge point — decks are exported as `.apkg` files, merged by Anki's own import logic (which uses modification timestamps to pick the winner card-by-card), then pushed to AnkiWeb so mobile picks them up.

---

## Install

### Option A — Homebrew (recommended, no Gatekeeper warning)

```bash
brew tap IryArkhy/deckhand
brew install --cask deckhand
```

### Option B — Direct download

Download the latest `.zip` from [Releases](https://github.com/IryArkhy/deckhand/releases), unzip, and drag `Deckhand.app` to `/Applications`.

> **Note:** macOS will show a Gatekeeper warning on first launch because the app is not notarized (that requires a $99/yr Apple Developer account). Go to **System Settings → Privacy & Security → Open Anyway** to allow it. Homebrew install skips this entirely.

---

## Requirements

| Requirement | Notes |
|---|---|
| macOS 12 Monterey or later | |
| [Anki desktop](https://apps.ankiweb.net/) | Any recent version |
| [AnkiConnect plugin](https://ankiweb.net/shared/info/2055492159) | Plugin code: `2055492159` |
| Google Drive for Desktop | Must be running and signed in |

**Installing AnkiConnect:** In Anki desktop, go to **Tools → Add-ons → Get Add-ons**, enter code `2055492159`, restart Anki.

---

## How it works

Each time you press **Sync Now**, Deckhand runs this sequence:

```
1. Launch Anki if it's not already open
2. Import every .apkg file from your Google Drive/AnkiSync/ folder
3. Export every top-level local deck to that same folder
4. Delete stale .apkg files (decks you've renamed or deleted)
5. Trigger an AnkiWeb sync to push the merged state to the cloud
```

Your mobile device then syncs with AnkiWeb as usual and gets the merged result.

### Why .apkg as the merge format?

When Anki imports an `.apkg`, it uses each note's globally unique ID (`guid`) and modification timestamp (`mod`) to decide what to keep:

- If the same card exists in both places, the **newer modification wins**
- Cards that only exist in the import are **added**
- Cards that only exist locally are **kept** (import is additive)

This means two devices can independently add cards to the same deck and both sets survive the merge.

---

## What syncs correctly

| Scenario | Handled |
|---|---|
| New cards added on any device | ✅ |
| Card content edited (front/back/fields) | ✅ — newer `mod` timestamp wins |
| New deck created | ✅ |
| Deck renamed | ✅ — stale Drive file is deleted, new one is written |
| Tags added or changed | ✅ — included in `.apkg` export |
| Note type changes | ✅ — included in `.apkg` export |

## What does NOT sync through Deckhand

| Scenario | Why | Workaround |
|---|---|---|
| Card deletions | `.apkg` import is additive — absent cards are ignored, not removed | Delete the card on all devices manually, or let AnkiWeb native sync propagate it |
| Deck deletions | Same reason — the exported `.apkg` for other decks won't mention the deleted one | Delete the deck on all devices manually |
| Review history / scheduling | Synced via AnkiWeb natively, not through Drive | Use AnkiWeb sync (Deckhand triggers this automatically as step 5) |
| Media files (images, audio) | Not included in `.apkg` exports by default | Sync your Anki media folder manually, or use AnkiWeb's media sync |

> **Key insight:** Deckhand handles *content* (notes, cards, decks). Deletions and scheduling flow through AnkiWeb's native channel, which Deckhand triggers at the end of every sync.

---

## Menu bar options

| Item | What it does |
|---|---|
| **Sync Now** | Runs the full sync cycle |
| **Check for Updates…** | Checks for a new Deckhand version via Sparkle |
| **View Log** | Shows the last 100 log lines |
| **Change Sync Folder…** | Pick a different folder if auto-detection fails |
| **Last synced: …** | Timestamp of the most recent successful sync |

---

## Automatic updates

Deckhand uses [Sparkle](https://sparkle-project.org/) for automatic updates. You'll get a notification when a new version is available. Updates are signed with an EdDSA key and served via this repo's `appcast.xml`.

---

## Google Drive folder

Deckhand auto-detects your Google Drive and creates an `AnkiSync/` subfolder inside **My Drive**. Each top-level deck is stored as `DeckName.apkg`. Subdecks (e.g. `Japanese::Vocabulary`) are included inside their parent deck's file — they don't get their own separate files.

If auto-detection fails (e.g. you have multiple Google accounts), use **Change Sync Folder…** to pick the folder manually. The path is saved to `~/.deckhand/config.json`.

---

## Troubleshooting

**"Anki did not start within 30 seconds"**
Open Anki manually before pressing Sync Now. AnkiConnect must be able to respond on `localhost:8765`.

**"No sync folder selected"**
Google Drive wasn't auto-detected. Use **Change Sync Folder…** and navigate to your `Google Drive/My Drive/AnkiSync` folder (create it if it doesn't exist).

**Duplicate decks after a rename**
If you renamed a deck before v0.1.4, the old `.apkg` may still be on Drive. Open your `AnkiSync/` folder in Google Drive and delete the file with the old name manually, then run Sync Now.

**Log location:** `~/.deckhand/deckhand.log`
**Config location:** `~/.deckhand/config.json`

---

## Development

```bash
git clone https://github.com/IryArkhy/deckhand.git
cd deckhand
pip install -e ".[dev]"
python -m deckhand        # run from source
pytest                    # run tests
```

### Building a release

```bash
bash scripts/build.sh v0.2.0
bash scripts/release.sh v0.2.0 "Notes here"
```

---

## Architecture

```
deckhand/
├── __main__.py       Entry point
├── app.py            rumps menu bar app, UI callbacks
├── sync.py           Orchestrates the full sync cycle
├── ankiconnect.py    HTTP client for AnkiConnect (localhost:8765)
├── drive.py          Google Drive folder detection and .apkg file I/O
├── config.py         Reads/writes ~/.deckhand/config.json
└── logger.py         Appends to ~/.deckhand/deckhand.log (capped at 500 lines)
```

---

## License

MIT — see [LICENSE](LICENSE).

Icon: [Anchor](https://phosphoricons.com/) by Phosphor Icons (MIT).
