"""Smoke test: the package imports and exposes a version."""

import polp


def test_package_imports() -> None:
    assert polp.__version__
