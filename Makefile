# uv-managed Makefile. `make check` is exactly what CI runs (.github/workflows/ci.yml).
.DEFAULT_GOAL := help
.PHONY: help setup format lint test check data data-summary subsets subsets-check update-golden pilot-smoke clean docker-build docker-test list-cells run-cell check-cell pilot analyse

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

update-golden:  ## Rewrite tests/golden/pipeline_cell.json after an intended change (review the diff!)
	UPDATE_GOLDEN=1 uv run pytest tests/test_pipeline.py -k golden_metrics -q

clean:  ## Remove caches and build artifacts (never touches runs/ or data/)
	rm -rf .mypy_cache .ruff_cache .pytest_cache .coverage htmlcov dist build
	find . -type d -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} +

docker-build:  ## Build the harness image locally (no push)
	docker build --target runtime -t agent-privilege-drift:dev .

docker-test:  ## Run the test suite inside the test image
	docker build --target test -t agent-privilege-drift:test .
	docker run --rm agent-privilege-drift:test

# GRID picks the grid file; the default is the experiment's configs/grid.yaml.
GRID_FLAG = $(if $(GRID),--grid $(GRID),)
PILOT_GRID = configs/pilot_grid.yaml

pilot:  ## Run the pilot: 9 Llama cells on 10 scenarios outside the experiment subset (hours; resumable; plug in)
	@for c in $$(uv run privilege-drift list-cells --grid $(PILOT_GRID) | awk '{print $$2}'); do \
		uv run privilege-drift run-cell $$c --grid $(PILOT_GRID) || exit 1; \
		uv run privilege-drift check-cell $$c --grid $(PILOT_GRID) || exit 1; \
	done

pilot-smoke:  ## Small first pass over all 9 pilot cells (3 runs each, ~10 min) to check the setup before `make pilot`
	@for c in $$(uv run privilege-drift list-cells --grid $(PILOT_GRID) | awk '{print $$2}'); do \
		uv run privilege-drift run-cell $$c --limit 3 --grid $(PILOT_GRID) || exit 1; \
	done

list-cells:  ## List the grid's cells with their numbers and ids: make list-cells [GRID=configs/pilot_grid.yaml]
	uv run privilege-drift list-cells $(GRID_FLAG)

run-cell:  ## Run the unfinished runs of one cell: make run-cell CELL=llama_p0_none [LIMIT=5] [GRID=...]
	@test -n "$(CELL)" || { echo "usage: make run-cell CELL=<cell id> [LIMIT=<n>] [GRID=<file>]" >&2; exit 2; }
	uv run privilege-drift run-cell $(CELL) $(if $(LIMIT),--limit $(LIMIT),) $(GRID_FLAG)

check-cell:  ## Run the three integrity checks on one cell: make check-cell CELL=llama_p0_none [GRID=...]
	@test -n "$(CELL)" || { echo "usage: make check-cell CELL=<cell id> [GRID=<file>]" >&2; exit 2; }
	uv run privilege-drift check-cell $(CELL) $(GRID_FLAG)

analyse:  ## Regenerate every analysis number, table and figure from runs/ into results/ (RQ1, RQ3)
	uv run python scripts/analyse.py
