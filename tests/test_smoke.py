"""Smoke test: the package imports and exposes a version."""

import privilege_drift


def test_package_imports() -> None:
    assert privilege_drift.__version__
