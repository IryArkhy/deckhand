import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".deckhand"
LOG_FILE = LOG_DIR / "deckhand.log"
MAX_LINES = 500


def write(level: str, message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp}  {level:<6} {message}\n"
    existing = LOG_FILE.read_text().splitlines(keepends=True) if LOG_FILE.exists() else []
    existing.append(line)
    if len(existing) > MAX_LINES:
        existing = existing[-MAX_LINES:]
    LOG_FILE.write_text("".join(existing))


def info(message: str) -> None:
    write("INFO", message)


def error(message: str) -> None:
    write("ERROR", message)


def tail(n: int = 100) -> str:
    if not LOG_FILE.exists():
        return ""
    return "\n".join(LOG_FILE.read_text().splitlines()[-n:])
