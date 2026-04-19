import pytest
from unittest.mock import patch, MagicMock


def _mock_response(result=None, error=None):
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"result": result, "error": error}
    return mock


def test_ping_returns_true_when_reachable():
    with patch("deckhand.ankiconnect.requests.post") as mock_post:
        mock_post.return_value = _mock_response(result=6)
        from deckhand import ankiconnect
        assert ankiconnect.ping() is True


def test_ping_returns_false_when_connection_refused():
    with patch("deckhand.ankiconnect.requests.post") as mock_post:
        mock_post.side_effect = Exception("Connection refused")
        from deckhand import ankiconnect
        assert ankiconnect.ping() is False


def test_get_deck_names_returns_list():
    with patch("deckhand.ankiconnect.requests.post") as mock_post:
        mock_post.return_value = _mock_response(result=["Default", "Japanese"])
        from deckhand import ankiconnect
        assert ankiconnect.get_deck_names() == ["Default", "Japanese"]


def test_invoke_raises_runtime_error_on_ankiconnect_error():
    with patch("deckhand.ankiconnect.requests.post") as mock_post:
        mock_post.return_value = _mock_response(result=None, error="deck not found")
        from deckhand import ankiconnect
        with pytest.raises(RuntimeError, match="AnkiConnect error: deck not found"):
            ankiconnect.get_deck_names()


def test_import_package_posts_correct_action():
    with patch("deckhand.ankiconnect.requests.post") as mock_post:
        mock_post.return_value = _mock_response(result=None)
        from deckhand import ankiconnect
        ankiconnect.import_package("/tmp/deck.apkg")
        payload = mock_post.call_args.kwargs["json"]
        assert payload["action"] == "importPackage"
        assert payload["params"]["path"] == "/tmp/deck.apkg"


def test_export_package_posts_correct_action():
    with patch("deckhand.ankiconnect.requests.post") as mock_post:
        mock_post.return_value = _mock_response(result=None)
        from deckhand import ankiconnect
        ankiconnect.export_package("Japanese", "/tmp/Japanese.apkg")
        payload = mock_post.call_args.kwargs["json"]
        assert payload["action"] == "exportPackage"
        assert payload["params"]["deck"] == "Japanese"
        assert payload["params"]["path"] == "/tmp/Japanese.apkg"
        assert payload["params"]["includeSched"] is True


def test_sync_posts_sync_action():
    with patch("deckhand.ankiconnect.requests.post") as mock_post:
        mock_post.return_value = _mock_response(result=None)
        from deckhand import ankiconnect
        ankiconnect.sync()
        payload = mock_post.call_args.kwargs["json"]
        assert payload["action"] == "sync"
