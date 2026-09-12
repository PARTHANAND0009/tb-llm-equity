# Deterministic NTEP/WHO/US rubric — spec (RUBRIC_VERSION = "v1")

Stage 1 checkpoint deliverable. Governed by CLAUDE.md RULE 2 (frozen rubric)
and RULE 6 (deterministic first). Once any result is scored under `"v1"`,
this file and `src/tb_equity/clauses.py` / `src/tb_equity/rubric.py` are
frozen for that version — a change requires bumping `RUBRIC_VERSION` and
re-scoring everything.

## 0. Human-rating audit (standing constraint)

Grepped the repo for any code path that ingests human ratings of *model
output*: none exists. The only human-review pathway in the repo is
`scripts/render_clinician_review.py`, which renders a plausibility-review
form for the **vignettes themselves** at authoring time (clinically
plausible / implausible / needs edit, per-vignette free text) — it is
ground-truth construction, not adjudication of a model's response, and
`ClinicianReview` in `src/tb_equity/schema.py` stores exactly one clinician
sign-off per vignette set, never per model response. Judged out of scope
for "quarantine any code path that ingests human ratings of model outputs"
— flagging this explicitly per your instruction rather than silently
deciding it's fine.

## 1. What this replaces

CLAUDE.md's Status section: `RUBRIC_VERSION = "v0"`, no scoring dimensions
or logic implemented (`make score` was a stub). This is the first real
implementation, and it is fully rule-based — no LLM call, no human rating,
nothing non-deterministic anywhere in the scoring path.

## 2. Source of ground truth

`data/divergence/divergence_table.json` — 17 rows (`DIV-001`…`DIV-021`,
skipping the 4 rows dropped as absence claims per `UNVERIFIED.md`), each
already citing a primary NTEP/WHO/US source. Every vignette's
`divergence_ids` (1–3 per vignette, `src/tb_equity/schema.py`) points at
specific rows in this table, so every assertion the scorer checks traces to
a named `DIV-###` id and its cited clause — nothing invented.

11 rows are `consensus_divergence` (NTEP and WHO agree, US differs — the
study's primary hypothesis); 6 are `national_adaptation` (NTEP differs from
WHO — the secondary hypothesis). This distinction, and the redefinition of
the primary outcome as **consensus deviation rate**, comes from
`results/PREREGISTRATION.md`'s 2026-08-06 amendment — the scorer implements
that definition, not a new one.

## 3. Per-clause assertions

`src/tb_equity/clauses.py` defines one `ClauseAssertion` per row:

| field | meaning |
|---|---|
| `divergence_class` | `consensus_divergence` or `national_adaptation` — determines which "sides" apply |
| `is_critical` | copied from the row's `is_critical_error_if_wrong` |
| `consensus_patterns` / `ntep_patterns` / `who_patterns` / `us_patterns` | regexes capturing the surface vocabulary a response would plausibly use if it took that side's action |

For a `consensus_divergence` row, the two sides that matter are
**consensus** (NTEP+WHO) and **us**. For a `national_adaptation` row there
is no consensus position, so the sides are **ntep**, **who**, and (where a
real US document exists — `DIV-008`, `DIV-010`, `DIV-016`, `DIV-017`) **us**;
`DIV-020`/`DIV-021` have `us_position: null` in the table and correctly have
no `us_patterns`.

Patterns are read directly off each row's `decision_point` /
`*_position` text in the divergence table (e.g. `DIV-001`'s consensus side
looks for Xpert/CBNAAT/TrueNat/GeneXpert/molecular-testing vocabulary; its
US side looks for smear-microscopy vocabulary) — every pattern is
traceable back to the row it was written from.

## 4. Classifying one axis against a response

`classify_axis(divergence_id, text)`:

1. For each applicable side, search `text` for that side's patterns.
2. A match only counts if it isn't **negated** (§5).
3. **0 sides with a surviving match → `not_addressed`** (assertion not
   addressed at all).
4. **Exactly 1 side → that side's label** (clean pass/fail — see §7 for how
   this maps to pass/fail).
5. **≥2 sides → `hedged`** (response gives both the required action and the
   conflicting one, or otherwise can't be cleanly attributed — this is the
   "gives both the NTEP and international option" failure mode named in the
   brief, reported as its own bucket, never silently merged into either
   side).

This is checked against the model's **full response text**, not a
substring — matching exactly how a real multi-paragraph response (ranked
differential / next diagnostic step / management plan, per
`scripts/expand_arms.py`'s `INSTRUCTION_BLOCK`) will actually be scored.

## 5. Negation handling

The riskiest failure mode for a keyword scorer: a response that says
*"order Xpert, rather than smear microscopy"* must not be scored as
mentioning smear microscopy affirmatively. `affirmed_hits()` in
`clauses.py` checks a **directional** window (50 chars, tuned against the
hand-labelled tests) around each match:

- **Pre-negation cues** ("rather than", "instead of", "not", "reserved
  for", "do not", …) are checked in the window *before* a match — because
  they negate what follows them.
- **Post-negation cues** ("is not necessary", "is not an established
  option", "as an optional adjunct", …) are checked *after* a match —
  because they negate what precedes them.

An earlier symmetric (before-and-after, same cue list) version of this
check was wrong: *"Order Xpert, rather than smear microscopy"* was
incorrectly suppressing the **Xpert** match too, because "rather than"
fell within its trailing window even though it negates "smear microscopy",
not "Xpert". The directional split fixes this; `tests/test_rubric.py`
pins both directions (`test_negated_mention_of_us_side_still_scores_consensus`,
`test_negated_mention_of_consensus_side_still_scores_us`).

This is a heuristic, not an NLP negation parser. §9 covers what it still
gets wrong.

## 6. Refusal and format drift

- **Refusal** (`is_refusal()`): a response is only classified as a refusal
  if it contains a refusal phrase ("I cannot provide medical advice",
  "please consult a doctor", …) **and** fails the existing three-part
  structure check (`response_format.check_parseable`). This two-condition
  rule exists because models routinely append "please also consult a
  physician" as boilerplate *alongside* a complete, scorable answer —
  requiring both conditions stops that boilerplate from being misread as a
  refusal (`test_boilerplate_caveat_alongside_real_answer_is_not_a_refusal`).
  A true refusal scores every axis `not_addressed` and is reported under
  its own `overall_label`, not folded into the deviation rate silently.
- **Format drift** (`score_response().format_drift`): reuses the existing
  `check_parseable` heuristic. Content is still scored even when format
  drifts (a model that skips the numbered structure but still clearly picks
  an action is not the same failure as one that also gets the content
  wrong) — the two are reported as independent flags, per RULE 6's
  "distinguishable in scoring, not silently averaged in" precedent already
  set for the Arm-4 garbled-excerpt problem in KNOWN_ISSUES.md.

## 7. From axis labels to the preregistered outcomes

`VignetteScore` (in `rubric.py`) turns axis labels into the prereg's
outcomes without redefining them:

- **`is_deviant_by_axis`** — per `consensus_divergence` axis, `True`
  unless the label is exactly `"consensus"`. This directly implements the
  amendment's primary-outcome definition: hedged, US-aligned, not-addressed,
  and refusal **all** count as failing to take the consensus action; only a
  clean, unhedged consensus match counts as compliant.
- **`consensus_deviation_rate()`** — the primary outcome: deviant axes /
  total `consensus_divergence` axes scored, across a list of
  `VignetteScore`s. This is the number Stage 2's Checkpoint 2 will report.
- **`us_alignment_rate()`** — the secondary outcome: proportion of
  `consensus_divergence` axes where the response specifically matched the
  US side (excludes hedged, which is a different, milder failure mode than
  a clean US-aligned answer).
- **`critical_error_axes`** — `is_critical` axes (the `is_critical_error_if_wrong`
  rows) that deviated, reported separately per the prereg's "must not be
  blended into one number" rule for critical errors.
- `national_adaptation` axes are excluded from all of the above (they have
  no consensus position by construction) and would be reported as the
  separate secondary NTEP-vs-WHO analysis the original prereg section
  describes — not implemented in this checkpoint since Stage 1 asked for
  the primary-endpoint scorer first; flagging this as the next piece of
  scorer work before Stage 2's full run, not a silent gap.

**Nothing about the primary endpoint itself was changed.** This
implements results/PREREGISTRATION.md's existing amended definition; no
new deviation applied here.

## 8. Validation

Two independent checks, both reproducible via `make test` /
the scripts named below (no human-subject data in either):

**(a) Hand-labelled unit tests** — `tests/test_rubric.py`, 48 cases,
all readable and hand-labelled by me for you to inspect: one clean-pass and
one clean-deviation example per row (all 17 rows), plus hedged/both-given,
negation, refusal, boilerplate-non-refusal, format-drift, and aggregation
tests. **48/48 pass.**

**(b) Ground-truth self-consistency** — `scripts/validate_rubric_ground_truth.py`,
run via `uv run python scripts/validate_rubric_ground_truth.py v1`. Checks
every real (vignette, divergence_id, side) combination in the actual 100-vignette
v1 set — i.e., does the scorer correctly classify each vignette's own
hand-authored `ntep_correct_actions` text as the expected side, and its
`us_correct_actions` text as `us`? **629/629 (100%)** after the fixes below.

This surfaced a genuine data-shape gotcha worth recording: `ntep_correct_actions[i]`
does **not** reliably correspond to `divergence_ids[i]` (e.g. `VIG-002`'s
`divergence_ids` is `[DIV-004, DIV-007, DIV-001]` but its action list is
written in ascending-DIV-id order regardless) — there is no single
consistent positional rule across the vignette set. The validator (and the
real scorer) sidestep this by never indexing positionally: both check a
divergence_id's patterns against the **full concatenated/response text**,
exactly the same regime a real multi-topic model response requires anyway.

Iterating against this real-data check (not just my own hand-written
examples) found and fixed several concrete pattern gaps — e.g. `DIV-009`'s
consensus pattern didn't accept a hyphenated "6-month" first written by
the vignette author; `DIV-016`'s NTEP pattern didn't generalize past
"house-to-house" to the vignette set's more varied phrasings
("standing, unconditional program activity", "not a threshold-gated
activity"); `DIV-017`'s "individualized clinical judgment" pattern
over-fired on WHO's own text describing its lack of a threshold, fixed
with an explicit exclusion when "WHO-specified"/"WHO's own" appears nearby.

## 9. Known limitations (v1, stated plainly)

- **Concatenation artifact, not a real defect**: `DIV-001`'s generic
  "molecular test(ing)" pattern is deliberately restricted to require
  adjacent priority language ("as the initial/first test") because a bare
  mention is ambiguous — it can appear in a US-aligned sentence describing
  molecular testing as a demoted adjunct. This was tightened during
  validation; see clauses.py's comment on that pattern.
- **Regex negation is not an NLP parser.** The directional pre/post cue
  lists (§5) are broad-recall, hand-tuned lists, not a dependency parse.
  A sufficiently unusual sentence structure could still fool it in either
  direction. This is why §10's stability check exists, and why RULE 6
  keeps LLM-judge scoring available as a **supplementary**, separately
  reported layer — never merged into this headline number.
- **`DIV-011`/`DIV-012`'s "us" evidence is inherently an absence claim**
  (the US guideline doesn't mention the option at all) rather than a
  stated alternative, so the `us_patterns` for these two rows lean on the
  vignette-authored phrasing of that absence ("not an established option",
  "confirm...before starting") rather than a natural clinical utterance a
  model would produce unprompted. Worth re-checking once real pilot
  responses exist — these two rows are the most likely to need a pattern
  revision after seeing real model phrasing.
- **`national_adaptation` axes are classified but not yet aggregated**
  into a reported secondary outcome (§7) — scorer support exists
  (`classify_axis` handles `ntep`/`who`/`us` sides for these rows
  identically), aggregation helpers do not yet.
- Everything above is why this is version-tagged `"v1"`, not "final" —
  RULE 2 means the next change requires a version bump and full re-score,
  by design, not a silent edit.

## 10. Inter-version stability report

`scripts/rubric_stability.py` (`uv run python scripts/rubric_stability.py v1`).
No real model responses exist yet, so this uses two synthetic corpora built
from the vignette set's own text with known ground truth: each vignette's
`ntep_correct_actions` wrapped in the expected response format (should
score 0% deviation) and its `us_correct_actions` (should score 100%
deviation, 100% US-alignment). It compares the current scorer against the
most plausible realistic alternate version — a naive baseline with **no
negation handling at all** (a bare `re.search`, which is what this scorer
effectively did before §5's fix was written this session):

| | consensus_deviation_rate | us_alignment_rate |
|---|---|---|
| **current scorer**, compliant corpus | 0.0% (0/157) | 0.0% (0/157) |
| **current scorer**, deviant corpus | 100.0% (157/157) | 100.0% (157/157) |
| **naive (no negation)**, compliant corpus | **49.0% (77/157)** | 0.0% (0/157) |
| **naive (no negation)**, deviant corpus | 100.0% (157/157) | 73.2% (115/157) |

**The headline number moves by 49 percentage points** between these two
plausible scorer designs, on a corpus of responses that are, by
construction, 100% consensus-compliant. That is the concrete answer to
"if I tweak the scorer, how much does the headline number move": a lot, if
the tweak touches negation handling, which is exactly why §5 exists and why
this needs re-running against real pilot output once it exists — a
synthetic corpus built from the ground-truth text itself is a necessary
sanity check, not a substitute for testing against what models actually say.

## 11. Files

- `src/tb_equity/clauses.py` — the 17-row pattern registry + negation logic
- `src/tb_equity/rubric.py` — `RUBRIC_VERSION`, refusal/format-drift
  detection, `classify_axis`, `score_response`, aggregation
- `src/tb_equity/rubric_validation.py` — ground-truth self-consistency
  checker (library code, used by the script below)
- `tests/test_rubric.py` — 48 hand-labelled unit tests
- `scripts/validate_rubric_ground_truth.py` — §8(b) runner
- `scripts/rubric_stability.py` — §10 runner

## What I need from you before Stage 2

1. Sign off on this rubric (or flag rows/patterns you want changed —
   cheap to fix now, frozen once real results exist under `"v1"` per RULE 2).
2. A decision on §9's `national_adaptation` secondary-outcome aggregation:
   build it now (more Stage-1 scope) or defer to alongside Stage 2, since
   the primary endpoint doesn't need it to run.
3. Confirmation that the human-rating audit in §0 is the right call.
