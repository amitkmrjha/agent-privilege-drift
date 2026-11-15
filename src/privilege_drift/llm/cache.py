"""On-disk response cache keyed by a hash of the full request."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def cache_key(payload: dict[str, Any]) -> str:
    """Stable SHA-256 of a JSON-serialisable request description."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ResponseCache:
    """One JSON file per key. Writes are atomic; unreadable entries count as misses."""

    def __init__(self, directory: Path | str) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        try:
            loaded = json.loads(path.read_text())
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            logger.warning("ignoring unreadable cache entry %s: %s", path.name, exc)
            return None
        if not isinstance(loaded, dict):
            logger.warning("ignoring cache entry %s: not a JSON object", path.name)
            return None
        return loaded

    def put(self, key: str, value: dict[str, Any]) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(value, handle, ensure_ascii=False)
            os.replace(tmp, self._path(key))
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
