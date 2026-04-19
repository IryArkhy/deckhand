from pathlib import Path
from unittest.mock import patch, call
import pytest


def test_sync_happy_path(isolated_env):
    folder = str(isolated_env / "AnkiSync")
    Path(folder).mkdir()
    (Path(folder) / "mobile_deck.apkg").write_text("")

    with patch("deckhand.ankiconnect.ping", return_value=True), \
         patch("deckhand.drive.get_folder_path", return_value=folder), \
         patch("deckhand.ankiconnect.get_deck_names", return_value=["Default", "Japanese", "Japanese::Vocab"]), \
         patch("deckhand.ankiconnect.import_package") as mock_import, \
         patch("deckhand.ankiconnect.export_package") as mock_export, \
         patch("deckhand.ankiconnect.sync") as mock_sync:

        from deckhand import sync
        result = sync.run(on_need_folder=lambda: None)

        # Only top-level decks exported (:: decks excluded)
        exported_decks = [c.args[0] for c in mock_export.call_args_list]
        assert "Default" in exported_decks
        assert "Japanese" in exported_decks
        assert "Japanese::Vocab" not in exported_decks

        assert mock_import.call_count == 1
        assert mock_sync.call_count == 1
        assert result["imported"] == ["mobile_deck"]
        assert set(result["exported"]) == {"Default", "Japanese"}


def test_sync_launches_anki_when_not_running(isolated_env):
    folder = str(isolated_env / "AnkiSync")
    Path(folder).mkdir()

    # First call: initial ping fails. Next calls: two polls fail, third succeeds.
    ping_responses = [False, False, False, True]

    with patch("deckhand.ankiconnect.ping", side_effect=ping_responses), \
         patch("deckhand.sync.subprocess.Popen") as mock_popen, \
         patch("deckhand.sync.time.sleep"), \
         patch("deckhand.drive.get_folder_path", return_value=folder), \
         patch("deckhand.ankiconnect.get_deck_names", return_value=[]), \
         patch("deckhand.ankiconnect.import_package"), \
         patch("deckhand.ankiconnect.export_package"), \
         patch("deckhand.ankiconnect.sync"):

        from deckhand import sync
        sync.run(on_need_folder=lambda: None)
        mock_popen.assert_called_once_with(["open", "-a", "Anki"])


def test_sync_raises_on_launch_timeout(isolated_env, monkeypatch):
    monkeypatch.setattr("deckhand.sync.LAUNCH_TIMEOUT", 4)
    monkeypatch.setattr("deckhand.sync.POLL_INTERVAL", 2)

    with patch("deckhand.ankiconnect.ping", return_value=False), \
         patch("deckhand.sync.subprocess.Popen"), \
         patch("deckhand.sync.time.sleep"):

        from deckhand import sync
        with pytest.raises(RuntimeError, match="did not start"):
            sync.run(on_need_folder=lambda: None)


def test_sync_raises_when_folder_picker_cancelled(isolated_env):
    with patch("deckhand.ankiconnect.ping", return_value=True), \
         patch("deckhand.drive.get_folder_path", return_value=None):

        from deckhand import sync
        with pytest.raises(RuntimeError, match="No sync folder"):
            sync.run(on_need_folder=lambda: None)


def test_sync_calls_on_need_folder_when_not_detected(isolated_env):
    folder = str(isolated_env / "AnkiSync")
    Path(folder).mkdir()

    with patch("deckhand.ankiconnect.ping", return_value=True), \
         patch("deckhand.drive.get_folder_path", return_value=None), \
         patch("deckhand.ankiconnect.get_deck_names", return_value=[]), \
         patch("deckhand.ankiconnect.import_package"), \
         patch("deckhand.ankiconnect.export_package"), \
         patch("deckhand.ankiconnect.sync"):

        from deckhand import sync, config
        sync.run(on_need_folder=lambda: folder)
        assert config.get_drive_folder() == folder


def test_sync_stops_and_raises_on_export_error(isolated_env):
    folder = str(isolated_env / "AnkiSync")
    Path(folder).mkdir()

    with patch("deckhand.ankiconnect.ping", return_value=True), \
         patch("deckhand.drive.get_folder_path", return_value=folder), \
         patch("deckhand.ankiconnect.get_deck_names", return_value=["Default"]), \
         patch("deckhand.ankiconnect.import_package"), \
         patch("deckhand.ankiconnect.export_package", side_effect=RuntimeError("export failed")), \
         patch("deckhand.ankiconnect.sync") as mock_sync:

        from deckhand import sync
        with pytest.raises(RuntimeError, match="export failed"):
            sync.run(on_need_folder=lambda: None)
        mock_sync.assert_not_called()
