.PHONY: setup test lint run-arms score analyze figures manifest-check \
        stratify generate-vignettes generate-vignettes-claude-code critique-vignettes \
        review-packet clinician-review expand-arms

setup:
	uv sync --all-extras
	uv run pre-commit install

test:
	uv run pytest

lint:
	uv run ruff check src tests scripts

# The vignette generation pipeline (schema, stratification, generation,
# critique, rendering) is implemented in scripts/ and src/tb_equity/. It has
# not been run against a live model yet — config/models.yaml has no
# generation.model configured (see CLAUDE.md RULE 5) — so generate-vignettes
# and critique-vignettes will fail loudly until a generator is chosen.

stratify:
	uv run python scripts/build_stratification_plan.py

generate-vignettes:
	uv run python scripts/generate_vignettes.py --mode=api

# No API key required -- writes per-cell prompts to data/vignettes/prompts/
# for a coding agent to answer by hand. Safe to re-run repeatedly; see
# CLAUDE.md "Generation modes".
generate-vignettes-claude-code:
	uv run python scripts/generate_vignettes.py --mode=claude-code

critique-vignettes:
	uv run python scripts/critique_vignettes.py

review-packet:
	uv run python scripts/render_review_packet.py

clinician-review:
	uv run python scripts/render_clinician_review.py

# Phase 3 arm expansion: pure deterministic templating, no model call. Fails
# loudly if data/vignettes/<version>/ is empty -- generate-vignettes (or
# generate-vignettes-claude-code) must run first. See CLAUDE.md.
expand-arms:
	uv run python scripts/expand_arms.py

run-arms:
	@echo "run-arms: not implemented yet — no experiment code has been written."
	@exit 1

# Deterministic RUBRIC_VERSION scoring (src/tb_equity/rubric.py) plus the
# Stage 2 primary analysis (src/tb_equity/analysis.py), combined into one
# script since scoring every response IS the input to every reported
# breakdown here. Requires real responses under data/responses/ (copied back
# from a Colab run of notebooks/open_weight_inference.ipynb) — fails loudly
# against zero data rather than writing an empty report.
score analyze:
	uv run python scripts/analyze_results.py

figures:
	@echo "figures: not implemented yet — no experiment code has been written."
	@exit 1

manifest-check:
	uv run python scripts/check_manifests.py
