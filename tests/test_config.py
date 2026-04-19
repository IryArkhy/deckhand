import json
import pytest


def test_get_drive_folder_returns_none_when_no_config_file(isolated_env):
    from deckhand import config
    assert config.get_drive_folder() is None


def test_set_drive_folder_creates_config_file(isolated_env):
    from deckhand import config
    config.set_drive_folder("/some/path")
    assert (isolated_env / "config.json").exists()


def test_set_drive_folder_persists_value(isolated_env):
    from deckhand import config
    config.set_drive_folder("/some/path")
    assert config.get_drive_folder() == "/some/path"


def test_set_drive_folder_writes_valid_json(isolated_env):
    from deckhand import config
    config.set_drive_folder("/some/path")
    raw = json.loads((isolated_env / "config.json").read_text())
    assert raw["drive_folder"] == "/some/path"


def test_set_drive_folder_overwrites_existing_value(isolated_env):
    from deckhand import config
    config.set_drive_folder("/first")
    config.set_drive_folder("/second")
    assert config.get_drive_folder() == "/second"
