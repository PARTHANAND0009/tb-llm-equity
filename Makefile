.PHONY: setup test lint run-arms score analyze figures manifest-check

setup:
	uv sync --all-extras
	uv run pre-commit install

test:
	uv run pytest

lint:
	uv run ruff check src tests scripts

# The following four targets are placeholders: no experiment code has been
# written yet (scaffold only, per project setup). They will call into
# src/tb_equity once that code exists.

run-arms:
	@echo "run-arms: not implemented yet — no experiment code has been written."
	@exit 1

score:
	@echo "score: not implemented yet — no experiment code has been written."
	@exit 1

analyze:
	@echo "analyze: not implemented yet — no experiment code has been written."
	@exit 1

figures:
	@echo "figures: not implemented yet — no experiment code has been written."
	@exit 1

manifest-check:
	uv run python scripts/check_manifests.py
