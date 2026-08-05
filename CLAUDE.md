# tb-llm-equity — project rules

This file governs every later task in this repo. These rules are not
suggestions — follow them in all future work here, without being re-asked.

## Project

An equity audit of LLM diagnostic reasoning on TB cases, comparing model
behavior against NTEP (India's National TB Elimination Programme) protocols
versus the WHO consolidated guidelines on tuberculosis (the "comparator"),
via paired vignettes.

## Repo layout

```
data/protocols/     raw NTEP + WHO + CDC source docs
data/divergence/    structured NTEP-vs-WHO divergence table
data/vignettes/     vignette JSON files, versioned
data/vignettes/prompts/  per-cell generation prompts (--mode=claude-code only)
data/responses/     cached raw model responses (--mode=api only)
results/            scored outputs, stats, figures
results/manifests/  one JSON manifest per experiment run
src/tb_equity/      package code
notebooks/          Colab-compatible notebooks for open-weight models
tests/
```

Python 3.11, dependencies managed with `uv` (`pyproject.toml` / `uv.lock`).

## RULE 1 — REPRODUCIBILITY

Every experiment run writes `results/manifests/<run_id>.json` containing:
model identifiers with version strings, temperature, top_p, max_tokens,
seed, prompt template hash (sha256), vignette set version, git commit sha,
UTC timestamp, and total token counts. The required field list lives at
`src/tb_equity/manifest.py::REQUIRED_MANIFEST_FIELDS`.

**No run without a manifest.** `make manifest-check` (backed by
`scripts/check_manifests.py`) validates every file in `results/manifests/`
against this schema and must pass before results are considered usable.

## RULE 2 — FROZEN RUBRIC

The scoring rubric lives at `src/tb_equity/rubric.py` and is version-tagged
via `RUBRIC_VERSION`. Once results exist for a given rubric version, that
version's scoring logic is immutable — never silently edit it after seeing
results. Any change to scoring dimensions or logic requires bumping
`RUBRIC_VERSION` and re-scoring **all** arms under the new version.

## RULE 3 — ANONYMITY

No school name, city, or state may appear in any file under `data/` or
`results/`, or in any generated text — IRIS evaluates anonymously. The
blocklist lives at `config/blocklist.txt` (one identifying string per line,
case-insensitive substring match) and is enforced by the pre-commit hook
`scripts/check_anonymity.py` (wired up in `.pre-commit-config.yaml`, runs on
files under `data/` and `results/`). Keep the blocklist current as new
identifying strings are discovered.

## RULE 4 — CACHE EVERYTHING

All API responses are cached to disk under `data/responses/`, keyed by
`sha256(model + prompt + params)`. Re-runs must hit cache — never re-pay for
inference. Store the full raw response object returned by the API, not just
parsed/extracted fields.

## RULE 5 — GENERATOR/EVALUATOR SEPARATION

The model family used to generate or critique vignettes must never be a
model family under evaluation. `config/models.yaml` holds `generation.model`
/ `generation.family` (the single model that generates and critiques
vignettes) and `evaluation.models` (the roster under evaluation, each with
its own `family`). Call `tb_equity.config.require_generation_model()` at the
start of any script that generates/critiques vignettes — it raises
`GenerationNotConfiguredError` if no generator is set yet, and
`GeneratorEvaluatorOverlapError` if `generation.family` also appears in
`evaluation.models[].family`. Keep `config/models.yaml` up to date as models
are added.

## RULE 6 — DETERMINISTIC FIRST

Every scored dimension must have a deterministic, rule-based scorer.
LLM-judge scoring is a supplementary layer, reported separately, and must
never be merged into the headline number.

## RULE 7 — HOLDOUT

Vignettes are held out at generation time, tagged `holdout=true`, and
excluded from all analysis until a final confirmation run. The holdout count
is proportional to the vignette set size (`TOTAL_HOLDOUT` /
`TOTAL_VIGNETTES` in `scripts/build_stratification_plan.py`) — currently 15
of 100.

## Generation modes

`scripts/generate_vignettes.py` supports two modes. RULE 5 applies to
**both** — `require_generation_model()` runs regardless of mode, so
`config/models.yaml`'s `generation.model`/`generation.family` must be set
either way, and must not overlap `evaluation.models`.

- **`--mode=api`** (default) — calls the configured generator over its
  provider API through `tb_equity.llm_client.CachingLLMClient` (sha256-cached
  per RULE 4). Requires the provider's API key to be set in the environment.
- **`--mode=claude-code`** — no API key required. Writes the per-cell
  grounding prompt to `data/vignettes/prompts/<cell_id>.md` instead of
  calling an API; a coding agent (e.g. Claude Code) reads each prompt file
  and acts as the generator directly, hand-writing the resulting vignette to
  `data/vignettes/<version>/<VIG-###>.json` per that file's embedded output
  contract. Re-running `--mode=claude-code` skips cells that already have a
  vignette file, validates whatever vignette files exist against
  `tb_equity.schema.Vignette` (same location-leak check as `--mode=api`),
  and writes a manifest — so it's safe to run repeatedly while an agent works
  through the prompt files over multiple sessions. Token counts in the
  manifest are 0 in this mode (no metered API call happens inside the
  script); `generation.family`/`generation.model` still identify who is
  acting as the generator for RULE 5 purposes.

`scripts/critique_vignettes.py` currently only supports the API path.

## Tooling

- `make setup` — `uv sync --all-extras` + install pre-commit hooks
- `make test` — `uv run pytest`
- `make lint` — `uv run ruff check src tests scripts`
- `make stratify` — (re)generate `data/vignettes/stratification_plan.{json,md}`
- `make generate-vignettes` — run the vignette generation pipeline in
  `--mode=api` (requires `generation.model`/`generation.family` set in
  `config/models.yaml` first, plus that provider's API key)
- `make generate-vignettes-claude-code` — same, but `--mode=claude-code`:
  writes prompts to `data/vignettes/prompts/` for a coding agent to answer by
  hand, no API key needed (see "Generation modes" below)
- `make critique-vignettes` — run the adversarial critique pass over a
  generated vignette set
- `make review-packet` — render `data/vignettes/REVIEW_PACKET.md`
- `make clinician-review` — render `data/vignettes/CLINICIAN_REVIEW.md`
- `make run-arms` — run evaluation arms (not yet implemented)
- `make score` — deterministic + LLM-judge scoring (not yet implemented)
- `make analyze` — statistical analysis (not yet implemented)
- `make figures` — generate figures (not yet implemented)
- `make manifest-check` — validate `results/manifests/*.json` against RULE 1

## Status

The vignette generation pipeline (schema, stratification plan, grounded
generation, adversarial critique, review-packet rendering) is implemented in
`src/tb_equity/` and `scripts/`, but has not been run against a live model:
`config/models.yaml` has no `generation.model` configured yet.
`generate_vignettes.py` and `critique_vignettes.py` both fail loudly
(`GenerationNotConfiguredError`) until a generator model/family is set —
this applies to `generate_vignettes.py` regardless of `--mode`.

`data/divergence/divergence_table.json` was rebuilt (2026-08-06) against the
WHO consolidated guidelines on tuberculosis as the comparator, replacing an
earlier version that used ATS/CDC/IDSA ("Western") guidance — WHO and NTEP
turned out to already agree on the highest-stakes original row, which meant
that table was really testing "2017 US guidance vs 2025 Indian guidance,"
not a health-equity question. It has 6 rows (`comparator_position`/
`comparator_citation`/`comparator_source` fields, not `western_*`), each
cited on both sides against a primary source actually fetched into
`data/protocols/` — short of the 10-16 rows anticipated because most of the
original 19 rows converged with WHO once re-sourced and rows without a real
citation on both sides were dropped rather than shipped weak (see
`data/divergence/UNVERIFIED.md` for what converged/was cut and why,
`data/divergence/SUMMARY.md` for composition stats). Still needs clinician
sign-off before being treated as ground truth — see
`data/divergence/README.md`.

The stratification plan (`scripts/build_stratification_plan.py`) covers 100
vignette slots across five `presentation_type` values — the original
pulmonary/extrapulmonary/comorbid/drug_resistant plus `contact_management`
(added to ground TPT/LTBI-focused divergence rows that don't fit an
active-disease presentation) — each split across `burden_class`
india_high/`comparator_control`, with every one of the 6 divergence rows
grounding at least one vignette (`tests/test_divergence_coverage.py`), each
capped at `MAX_DIVERGENCE_IDS_PER_VIGNETTE` (3) rows per vignette and
age-band-filtered so a row never grounds a vignette outside its
`applicable_age_bands`. Each `comparator_control` cell carries a
`matched_pair_id` linking it to one `india_high` cell matched on
presentation complexity, age band, and distractor count.

No evaluation-arm/scoring code has been written yet.
