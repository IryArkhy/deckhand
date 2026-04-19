import requests

BASE_URL = "http://localhost:8765"


def _invoke(action: str, **params) -> object:
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post(BASE_URL, json=payload, timeout=10)
    response.raise_for_status()
    result = response.json()
    if result.get("error"):
        raise RuntimeError(f"AnkiConnect error: {result['error']}")
    return result["result"]


def ping() -> bool:
    try:
        _invoke("version")
        return True
    except Exception:
        return False


def get_deck_names() -> list[str]:
    return _invoke("deckNames")


def import_package(path: str) -> None:
    _invoke("importPackage", path=path)


def export_package(deck_name: str, path: str) -> None:
    _invoke("exportPackage", deck=deck_name, path=path, includeSched=True)


def sync() -> None:
    _invoke("sync")
