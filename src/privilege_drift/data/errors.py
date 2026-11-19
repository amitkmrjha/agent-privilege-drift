"""Errors raised while loading benchmark data."""

from __future__ import annotations


class DataError(ValueError):
    """Benchmark data or a tier map is missing, malformed or inconsistent."""
