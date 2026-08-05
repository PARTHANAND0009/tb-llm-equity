# tb-llm-equity — project rules

This file governs every later task in this repo. These rules are not
suggestions — follow them in all future work here, without being re-asked.

## Project

An equity audit of LLM diagnostic reasoning on TB cases. As of the
2026-08-06 reframe, the core question is not "does NTEP differ from WHO" but
**does a model follow NTEP-WHO international consensus, or does it default
to US national practice even where WHO and India's national TB programme
(NTEP) agree against it?** Every divergence-table row carries three
positions (NTEP / WHO / US); `divergence_class` marks whether a row tests
that primary hypothesis (`consensus_divergence`: NTEP and WHO agree, US
differs) or the secondary one (`national_adaptation`: NTEP differs from
WHO). See `data/divergence/SUMMARY.md` for why.

## Repo layout

```
data/protocols/     raw NTEP + WHO + US (ATS/CDC/IDSA) source docs
data/divergence/    structured NTEP/WHO/US three-way divergence table
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

## Phase 3: arm expansion

`scripts/expand_arms.py` turns each generated vignette into four
evaluation-arm prompts (baseline / location / epidemiological framing /
protocol retrieval — see `results/PREREGISTRATION.md` "Design"). It is pure
deterministic templating: no model call, no generator, RULE 5 does not
apply. It **cannot be run until vignettes exist** —
`data/vignettes/<version>/` must contain at least one `VIG-*.json` file, or
it fails loudly with a message saying generation must run first, rather
than silently doing nothing. As of this commit `data/vignettes/v1/` is
empty, so this has only been exercised against
`tests/fixtures/example_vignettes/`, not real data.

Every arm is built by strict append-only concatenation on top of Arm 1's
fixed instruction block + stem, which is what makes the instruction block
byte-identical across all four arms and Arm 2/3/4 each contain their parent
arm's text verbatim (Arm 3 and Arm 4 both branch off Arm 2, not off each
other — see the module docstring). For `consensus_control` vignettes, Arm 2
locates the case at a US teaching hospital (not India) and Arm 4 retrieves
ATS/CDC/IDSA text (not NTEP) — the symmetric mirror needed to test whether
a model's US-practice answer changes once it's told it's actually in a US
setting. Protocol retrieval (Arm 4) matches each grounding row's citation
`doc` string to a locally fetched file in `data/protocols/` via a keyword
table, extracts a bounded excerpt, and falls back to the divergence table's
own `ntep_position`/`who_position`/`us_position` prose when no local file
matches (e.g. DIV-001's NTEP citation is a web page that was never
archived) — every fallback is logged, never silent. Injected protocol text
is capped at `MAX_PROTOCOL_TOKENS` (2000, ~4 chars/token estimate) per
vignette, and `data/prompts/manifest.json` records exactly which protocol
chunks (or fallback) were injected into each vignette's Arm 4, alongside a
sha256 hash per prompt file. A separate RULE 1 experiment manifest is
written to `results/manifests/<run_id>.json` (`model_identifiers: []`,
since no model is involved).

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
- `make expand-arms` — Phase 3 arm expansion (see above). Fails loudly if
  `data/vignettes/<version>/` is empty — generate vignettes first.
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

`data/divergence/divergence_table.json` was rebuilt twice on 2026-08-06.
First against the WHO consolidated guidelines on tuberculosis as a
two-way comparator (replacing an earlier version that used ATS/CDC/IDSA
"Western" guidance) — which found NTEP converges with WHO on 11 of the
original 19 rows, an unanticipated empirical result. Rather than drop those
11 rows as dead ends, the table was restructured a second time, same day,
into a **three-way** table: every row now carries `ntep_position`,
`who_position`, and `us_position` simultaneously, tagged `divergence_class`
(`consensus_divergence`: NTEP and WHO agree, US differs -- the 11
reinstated rows, and the primary dataset; `national_adaptation`: NTEP
differs from WHO -- 6 rows, secondary). It has 17 rows total, each cited on
the NTEP and WHO sides against a primary source actually fetched into
`data/protocols/`, with `us_position` cited wherever a real US document
addresses the point (`null`, not inferred, for the 2 rows where none was
fetched). See `data/divergence/UNVERIFIED.md` for the full disposition
history and `data/divergence/SUMMARY.md` for composition stats and the
reframed research question. Still needs clinician sign-off before being
treated as ground truth -- see `data/divergence/README.md`.

The stratification plan (`scripts/build_stratification_plan.py`) covers 100
vignette slots across five `presentation_type` values -- the original
pulmonary/extrapulmonary/comorbid/drug_resistant plus `contact_management`
(added to ground TPT/LTBI-focused divergence rows that don't fit an
active-disease presentation) -- each split across `burden_class`
india_high/`consensus_control` (renamed from `comparator_control`: the
control arm now represents the NTEP-WHO consensus position, not a
"Western"/comparator position), weighted so roughly 75% of cells ground
primarily in `consensus_divergence` rows and 25% in `national_adaptation`
rows. Every one of the 17 divergence rows grounds at least one vignette
(`tests/test_divergence_coverage.py`), each vignette capped at
`MAX_DIVERGENCE_IDS_PER_VIGNETTE` (3) rows and age-band-filtered so a row
never grounds a vignette outside its `applicable_age_bands`. Each
`consensus_control` cell carries a `matched_pair_id` linking it to one
`india_high` cell matched on presentation complexity, age band, and
distractor count.

The Phase 3 arm-expansion pipeline (`scripts/expand_arms.py`, see "Phase 3:
arm expansion" above) is implemented and unit-tested against
`tests/fixtures/example_vignettes/`, but has not been run against real
vignettes -- `data/vignettes/v1/` is still empty. No scoring/analysis code
(`make score`, `make analyze`, `make figures`) has been written yet.
