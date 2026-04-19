from pathlib import Path
import pytest


def test_list_apkg_files_returns_only_apkg(tmp_path):
    (tmp_path / "deck1.apkg").write_text("")
    (tmp_path / "deck2.apkg").write_text("")
    (tmp_path / "notes.txt").write_text("")
    from deckhand import drive
    result = drive.list_apkg_files(str(tmp_path))
    names = {Path(p).name for p in result}
    assert names == {"deck1.apkg", "deck2.apkg"}


def test_list_apkg_files_returns_empty_for_empty_folder(tmp_path):
    from deckhand import drive
    assert drive.list_apkg_files(str(tmp_path)) == []


def test_apkg_path_for_deck_returns_correct_path(tmp_path):
    from deckhand import drive
    result = drive.apkg_path_for_deck(str(tmp_path), "Japanese")
    assert result == str(tmp_path / "Japanese.apkg")


def test_apkg_path_for_deck_replaces_sep_in_name(tmp_path):
    """Subdeck names like 'Japanese::Vocab' must not create nested directories."""
    from deckhand import drive
    import os
    result = drive.apkg_path_for_deck(str(tmp_path), "Japanese::Vocab")
    assert os.sep not in Path(result).name
    assert ":" not in Path(result).name
    assert Path(result).name == "Japanese__Vocab.apkg"


def test_get_folder_path_returns_saved_path(isolated_env):
    folder = str(isolated_env / "AnkiSync")
    Path(folder).mkdir()
    from deckhand import config, drive
    config.set_drive_folder(folder)
    assert drive.get_folder_path() == folder


def test_get_folder_path_returns_none_when_saved_path_missing(isolated_env, monkeypatch):
    monkeypatch.setattr("deckhand.drive.CANDIDATE_PATTERNS", [str(isolated_env / "nonexistent-*")])
    from deckhand import config, drive
    config.set_drive_folder("/nonexistent/path")
    assert drive.get_folder_path() is None


def test_get_folder_path_returns_none_when_no_gdrive_found(isolated_env, monkeypatch):
    monkeypatch.setattr("deckhand.drive.CANDIDATE_PATTERNS", [str(isolated_env / "nonexistent-*")])
    from deckhand import drive
    assert drive.get_folder_path() is None


def test_get_folder_path_auto_detects_single_gdrive(isolated_env, monkeypatch):
    gdrive = isolated_env / "GoogleDrive-test@gmail.com" / "My Drive"
    gdrive.mkdir(parents=True)
    monkeypatch.setattr(
        "deckhand.drive.CANDIDATE_PATTERNS",
        [str(isolated_env / "GoogleDrive-*" / "My Drive")],
    )
    from deckhand import drive
    result = drive.get_folder_path()
    assert result == str(gdrive / "AnkiSync")
    assert Path(result).exists()


def test_get_folder_path_returns_none_when_multiple_gdrive_found(isolated_env, monkeypatch):
    for name in ["GoogleDrive-a@gmail.com", "GoogleDrive-b@gmail.com"]:
        (isolated_env / name / "My Drive").mkdir(parents=True)
    monkeypatch.setattr(
        "deckhand.drive.CANDIDATE_PATTERNS",
        [str(isolated_env / "GoogleDrive-*" / "My Drive")],
    )
    from deckhand import drive
    assert drive.get_folder_path() is None
