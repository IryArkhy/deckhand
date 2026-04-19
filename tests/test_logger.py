import re
import pytest


def test_info_writes_timestamped_line(isolated_env):
    from deckhand import logger
    logger.info("hello world")
    content = (isolated_env / "deckhand.log").read_text()
    assert "INFO" in content
    assert "hello world" in content
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content)


def test_error_writes_error_level(isolated_env):
    from deckhand import logger
    logger.error("something broke")
    content = (isolated_env / "deckhand.log").read_text()
    assert "ERROR" in content
    assert "something broke" in content
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content)


def test_log_lines_are_capped_at_max(isolated_env, monkeypatch):
    monkeypatch.setattr("deckhand.logger.MAX_LINES", 5)
    from deckhand import logger
    for i in range(10):
        logger.info(f"line {i}")
    lines = (isolated_env / "deckhand.log").read_text().strip().splitlines()
    assert len(lines) == 5


def test_log_keeps_most_recent_lines(isolated_env, monkeypatch):
    monkeypatch.setattr("deckhand.logger.MAX_LINES", 3)
    from deckhand import logger
    for i in range(5):
        logger.info(f"line {i}")
    content = (isolated_env / "deckhand.log").read_text()
    assert "line 4" in content
    assert "line 0" not in content


def test_tail_returns_last_n_lines(isolated_env):
    from deckhand import logger
    for i in range(10):
        logger.info(f"line {i}")
    result = logger.tail(3)
    lines = result.splitlines()
    assert len(lines) == 3
    assert "line 9" in lines[-1]


def test_tail_returns_empty_string_when_no_log(isolated_env):
    from deckhand import logger
    assert logger.tail() == ""
