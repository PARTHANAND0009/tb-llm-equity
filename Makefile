.PHONY: setup test lint run-arms score analyze figures manifest-check \
        stratify generate-vignettes generate-vignettes-claude-code critique-vignettes \
        review-packet clinician-review

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

# The following four targets are placeholders: no evaluation-arm/scoring
# code has been written yet. They will call into src/tb_equity once that
# code exists.

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
