# uv-managed Makefile. `make check` is exactly what CI runs (.github/workflows/ci.yml).
.DEFAULT_GOAL := help
.PHONY: help setup format lint test check clean docker-build docker-test pilot run-cell analyse

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup:  ## Create/refresh the virtualenv and install pre-commit hooks
	uv sync
	uv run pre-commit install

format:  ## Format code with ruff
	uv run ruff format .

lint:  ## ruff check, ruff format --check, mypy (strict)
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

test:  ## Run the test suite
	uv run pytest

check: lint test  ## Full local gate: lint + typecheck + tests (what CI runs); run before every PR

clean:  ## Remove caches and build artifacts (never touches runs/ or data/)
	rm -rf .mypy_cache .ruff_cache .pytest_cache .coverage htmlcov dist build
	find . -type d -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} +

docker-build:  ## Build the harness image locally (no push)
	docker build --target runtime -t agent-privilege-drift:dev .

docker-test:  ## Run the test suite inside the test image
	docker build --target test -t agent-privilege-drift:test .
	docker run --rm agent-privilege-drift:test

# Not implemented yet: wired up by later issues.
pilot:  ## (placeholder) run the pilot, Phase 2
	@echo "pilot: not implemented yet (see Phase 2)" >&2; exit 1

run-cell:  ## (placeholder) run one experiment cell, Phase 1
	@echo "run-cell: not implemented yet (see Phase 1)" >&2; exit 1

analyse:  ## (placeholder) reproduce every number, Phase 4
	@echo "analyse: not implemented yet (see Phase 4)" >&2; exit 1
