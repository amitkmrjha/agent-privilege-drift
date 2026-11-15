.PHONY: setup lint test pilot run-cell analyse

setup:
	uv sync
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

test:
	uv run pytest

# Not implemented yet: wired up by later issues.
pilot:
	@echo "pilot: not implemented yet (see Phase 2)" >&2; exit 1

run-cell:
	@echo "run-cell: not implemented yet (see Phase 1)" >&2; exit 1

analyse:
	@echo "analyse: not implemented yet (see Phase 4)" >&2; exit 1
