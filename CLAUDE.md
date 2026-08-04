# tb-llm-equity — project rules

This file governs every later task in this repo. These rules are not
suggestions — follow them in all future work here, without being re-asked.

## Project

An equity audit of LLM diagnostic reasoning on TB cases, comparing model
behavior against NTEP (India's National TB Elimination Programme) protocols
versus WHO/CDC ("Western") protocols, via paired vignettes.

## Repo layout

```
data/protocols/     raw NTEP + WHO + CDC source docs
data/divergence/    structured NTEP-vs-Western divergence table
data/vignettes/     vignette JSON files, versioned
data/responses/     cached raw model responses
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

20 vignettes are held out at generation time, tagged `holdout=true`, and
excluded from all analysis until a final confirmation run.

## Tooling

- `make setup` — `uv sync --all-extras` + install pre-commit hooks
- `make test` — `uv run pytest`
- `make lint` — `uv run ruff check src tests scripts`
- `make stratify` — (re)generate `data/vignettes/stratification_plan.{json,md}`
- `make generate-vignettes` — run the vignette generation pipeline (requires
  `generation.model`/`generation.family` set in `config/models.yaml` first)
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
`config/models.yaml` has no `generation.model` configured yet, and
`data/divergence/divergence_table.json` is a **draft** written from training
knowledge, not yet verified against primary sources in `data/protocols/`
(currently empty) or signed off by a clinician — see
`data/divergence/README.md`. `generate_vignettes.py` and
`critique_vignettes.py` both fail loudly (`GenerationNotConfiguredError`)
until a generator model/family is set. No evaluation-arm/scoring code has
been written yet.
