"""ResponseCache on its own."""

import logging
import os
from pathlib import Path

import pytest

from privilege_drift.llm import ResponseCache
from privilege_drift.llm.cache import cache_key


def test_miss_then_roundtrip(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    assert cache.get("abc") is None
    cache.put("abc", {"text": "héllo", "n": 1})
    assert cache.get("abc") == {"text": "héllo", "n": 1}


def test_corrupt_entry_is_a_miss_and_is_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    cache = ResponseCache(tmp_path)
    (tmp_path / "bad.json").write_text("{not json")
    with caplog.at_level(logging.WARNING):
        assert cache.get("bad") is None
    assert "unreadable cache entry" in caplog.text
    cache.put("bad", {"ok": True})  # a corrupt entry can be overwritten
    assert cache.get("bad") == {"ok": True}


def test_non_object_entry_is_a_miss(tmp_path: Path) -> None:
    (tmp_path / "list.json").write_text("[1, 2, 3]")
    assert ResponseCache(tmp_path).get("list") is None


def test_put_leaves_no_temp_files(tmp_path: Path) -> None:
    ResponseCache(tmp_path).put("k", {"a": 1})
    assert [p.name for p in tmp_path.iterdir()] == ["k.json"]


def test_failed_put_cleans_up_and_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(src: str, dst: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError, match="disk full"):
        ResponseCache(tmp_path).put("k", {"a": 1})
    assert list(tmp_path.iterdir()) == []


def test_cache_key_ignores_dict_order_but_not_content() -> None:
    assert cache_key({"a": 1, "b": 2}) == cache_key({"b": 2, "a": 1})
    assert cache_key({"a": 1}) != cache_key({"a": 2})
