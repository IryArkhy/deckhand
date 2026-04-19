import pytest


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Redirect config and log files into tmp_path so tests never touch ~/.deckhand."""
    monkeypatch.setattr("deckhand.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("deckhand.config.CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr("deckhand.logger.LOG_DIR", tmp_path)
    monkeypatch.setattr("deckhand.logger.LOG_FILE", tmp_path / "deckhand.log")
    return tmp_path
