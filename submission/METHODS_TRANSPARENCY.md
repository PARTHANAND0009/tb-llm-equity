# Methods transparency

This document states plainly what was automated and what was human-decided
in this study, per the project's own integrity discipline (`CLAUDE.md`).
It is written to be read alongside `results/PREREGISTRATION.md`, not as a
substitute for it.

## What was automated

- **Vignette drafting.** The 100 vignettes in `data/vignettes/v1/` were
  drafted by an LLM coding agent (Claude, acting as `generation.model:
  claude-code-agent` / `generation.family: anthropic` per
  `config/models.yaml`) working case-by-case from the per-cell grounding
  prompts in `data/vignettes/prompts/`, each of which specifies the
  divergence-table row(s) the case must ground in and the hard constraints
  (no location leakage, ≥2 distractors, verbatim NTEP/WHO action overlap on
  `consensus_divergence` rows, etc.).
- **Inference harness.** The four-arm prompt expansion
  (`scripts/expand_arms.py`) — baseline / location / epidemiological
  framing / protocol retrieval — is pure deterministic templating with no
  model call involved.
- **Scoring pipeline.** Deterministic scoring against
  `consensus_correct_actions`, `ntep_correct_actions`,
  `who_correct_actions`, `us_correct_actions`, and
  `critical_error_conditions` (RULE 6: every scored dimension has a
  rule-based scorer; LLM-judge scoring, where used, is a supplementary
  layer reported separately, never merged into the headline number).
- **Statistics and figures.** Not yet run as of this document's writing;
  when run, the mixed-effects models, multiple-comparison correction, and
  figure generation described in `results/PREREGISTRATION.md` are code,
  not manual judgment calls.

## What was human-decided

- **Divergence table verification against primary sources.** Every row in
  `data/divergence/divergence_table.json` is cited against a primary NTEP,
  WHO, or US (ATS/CDC/IDSA) source document fetched into
  `data/protocols/`; `divergence_class` (`consensus_divergence` vs.
  `national_adaptation`) was assigned by reading those sources, not
  inferred.
- **Rubric design.** `src/tb_equity/rubric.py` (RULE 2: frozen once results
  exist for a given `RUBRIC_VERSION`).
- **Arm design.** The four-arm escalation (baseline → location →
  epidemiological base rates → retrieved protocol text) and the
  `PGC_k ≥ 0.5`-plus-significance "substantially closes the gap"
  interpretation rule in `results/PREREGISTRATION.md`, fixed before any
  data existed.
- **Interpretation rules**, including the primary consensus-deviation
  outcome and secondary US-alignment outcome definitions, and the
  divergence-class stratification of the analysis (see
  `results/PREREGISTRATION.md` Amendments, 2026-08-06).
- **Matched-pair design and its correction.** `matched_pair_id` pairing
  logic and the divergence-class-alignment fix applied on 2026-08-06 (see
  `results/PREREGISTRATION.md` Amendments) were human-specified corrections
  to a human-designed covariate structure.
- **Clinician review** (see below).

## Generator/evaluator separation (RULE 5)

`config/models.yaml` sets `generation.family: anthropic` — the only model
family used to generate or critique vignettes. `evaluation.models` (the
roster to be run against the finished vignette set in Phase 4) is
constrained by `tb_equity.config.require_generation_model()` to never
include `anthropic`: any attempt to add an Anthropic model to
`evaluation.models` raises `GeneratorEvaluatorOverlapError` at config-load
time, before any run can start.

**Rationale.** The model that writes and critiques a test cannot also sit
the test without confounding the result: if the generator family were also
under evaluation, any advantage or bias it shows on the vignettes it wrote
would be inseparable from an evaluation artifact rather than a genuine
finding about that model's clinical reasoning. Excluding Anthropic from the
evaluation roster is not a comment on Anthropic models' capability — it is
a structural requirement for the comparison between the remaining models to
mean anything.

## Clinician review

Every vignette in `data/vignettes/v1/` (all 100) was reviewed by:

- **Reviewer:** Dr. Ojasvi Anand
- **Credentials:** MBBS
- **Institution:** SSR Medical College
- **Review date:** 2026-08-06
- **Verdict:** approved
- **Edits requested:** 0
- **Scope:** all 100 vignettes in `data/vignettes/v1/` (v1 set)
- **Notes:** none recorded

This is recorded in each vignette's `provenance.clinician_review` block
(`src/tb_equity/schema.py::ClinicianReview`) and reflected in
`provenance.human_reviewed` / `provenance.clinician_reviewed`, both `true`
for all 100 vignettes.

**Scope of this review, stated accurately.** Dr. Anand holds an MBBS — a
general medical qualification — not a TB-specialist, pulmonology, or
infectious-disease credential. This review confirms the vignettes read as
clinically plausible, internally coherent cases with no location leakage,
not that a specialist has independently re-verified the finer clinical
detail of every subtype, in particular the drug-resistant-TB regimen
specifics and paediatric presentations, where specialist judgment matters
most. **A specialist review of the pre-XDR-TB and paediatric subsets is
planned as an additional validation step** before those subsets' results
are treated as final; it has not yet occurred as of this document's
writing. This document will be updated when it does.
