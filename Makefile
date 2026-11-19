# uv-managed Makefile. `make check` is exactly what CI runs (.github/workflows/ci.yml).
.DEFAULT_GOAL := help
.PHONY: help setup format lint test check data data-summary subsets subsets-check clean docker-build docker-test list-cells run-cell check-cell pilot analyse

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

data:  ## Download ToolPrivBench (pinned revision, hash-checked) into data/raw/
	uv run python scripts/fetch_toolprivbench.py

data-summary:  ## Regenerate docs/data_summary.md from data/raw/ (needs `make data`)
	uv run python scripts/data_summary.py

subsets:  ## Write the frozen scenario subset and seed schedule under prereg/ (needs `make data`)
	uv run python scripts/make_subsets.py

subsets-check:  ## Fail if prereg/ subsets or seed schedule differ from a fresh regeneration
	uv run python scripts/make_subsets.py --check

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

list-cells:  ## List the 18 grid cells with their numbers and ids
	uv run privilege-drift list-cells

run-cell:  ## Run the unfinished runs of one cell: make run-cell CELL=llama_p0_none [LIMIT=5]
	@test -n "$(CELL)" || { echo "usage: make run-cell CELL=<cell id> [LIMIT=<n>]" >&2; exit 2; }
	uv run privilege-drift run-cell $(CELL) $(if $(LIMIT),--limit $(LIMIT),)

check-cell:  ## Run the three integrity checks on one cell: make check-cell CELL=llama_p0_none
	@test -n "$(CELL)" || { echo "usage: make check-cell CELL=<cell id>" >&2; exit 2; }
	uv run privilege-drift check-cell $(CELL)

analyse:  ## (placeholder) reproduce every number, Phase 4
	@echo "analyse: not implemented yet (see Phase 4)" >&2; exit 1
