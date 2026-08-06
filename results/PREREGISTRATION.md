# Preregistration

Committed 2026-08-06, before any vignette is generated (`data/vignettes/v1/`
is empty as of this commit — see `git log` for the commit this file lands
in relative to the first `VIG-*.json` file, if any). RULE 7 in `CLAUDE.md`
(holdout) and RULE 2 (frozen rubric) govern this study alongside the design
fixed here. Nothing in this document may be edited after any scored result
exists without an explicit, logged amendment noting what changed and why —
silent edits defeat the point of preregistering.

## Research question

Do frontier LLMs deviate more from India's national TB protocol (NTEP) than
from WHO consolidated guidance on the same clinical decisions, and — where
they do — is that deviation closable by contextual cues, or does it require
protocol retrieval?

This is deliberately two questions, not one. The first (do models deviate
more from NTEP than WHO) establishes whether there is a gap at all. The
second (what closes it) is the actual point of the study: a gap that closes
with a one-line location cue is a different failure mode, with a different
fix, than a gap that only closes when the model is handed the protocol text
directly.

## Design

Four arms per vignette, applied to the same underlying clinical case:

- **Arm 1 — baseline.** The vignette stem as generated: no country, city,
  state, or health-system name (enforced by `leaks_location()` in
  `scripts/generate_vignettes.py` at generation time, per RULE 3 and the
  location-neutrality constraint in `SYSTEM_PROMPT_TEMPLATE`). The model
  reasons with no locating information at all.
- **Arm 2 — stated location.** The same stem, prepended or appended with a
  bare location statement (e.g., "This patient is being seen in India.").
  No epidemiological content, no protocol text — just a place name.
- **Arm 3 — epidemiological base rates.** The same stem, with explicit
  epidemiological framing appropriate to the vignette's `burden_class`
  (e.g., local TB incidence/prevalence figures, drug-resistance prevalence,
  relevant program-context statistics) but no protocol citation and no
  verbatim guideline text.
- **Arm 4 — retrieved protocol text.** The same stem, with the specific NTEP
  protocol passage(s) relevant to the vignette's grounding divergence
  row(s) (`ntep_citation` in `divergence_table.json`) provided directly in
  context.

Arms are cumulative in what they add (2 ⊂ 3 ⊂ 4 is not required in content,
but each arm is strictly more informative than the last about what the
"right" answer is), which is what makes the interpretation rule below
possible: closing behavior localizes to the specific arm where enough
information was added.

Every vignette is evaluated across all four arms, for every model in
`config/models.yaml`'s `evaluation.models` roster, at the seed(s) configured
for the run. `matched_pair_id` pairing (india_high ↔ comparator_control,
Task 3's stratification plan) is preserved as a covariate in analysis, not
collapsed — the arm contrast is within-vignette, the burden_class contrast
is between matched pairs.

## Interpretation rule (fixed in advance)

Let `gap_k` = (NTEP-protocol deviation rate in Arm k) − (WHO-protocol
deviation rate in Arm k), measured on the same set of vignettes in both
arms. `gap_1` is the baseline gap Arms 2-4 are trying to close. For each
arm k ∈ {2, 3, 4}, define the **proportion of gap closed**:

```
PGC_k = (gap_1 − gap_k) / gap_1
```

**"Substantially closes the gap" is defined, before any data exists, as:**
`PGC_k ≥ 0.5` **and** the reduction (`gap_1 − gap_k`) is statistically
significant at α = 0.05 (95% CI on the reduction excludes 0, via a
mixed-effects logistic regression with arm as a fixed effect and
vignette/model as random effects, or McNemar's test on the matched
within-vignette Arm-1-vs-Arm-k pairs if the mixed-effects model does not
converge). Both conditions must hold — a large but non-significant PGC, or
a significant but small (<50%) PGC, does not count as "substantially
closes."

Applying this threshold arm-by-arm, in order:

1. **Arm 2 substantially closes the gap** → the model has the relevant
   knowledge but doesn't apply it without a contextual cue. This is a
   **prompting-level failure**: the fix is telling the model where it is,
   not teaching it anything new.
2. **Arm 3 closes it but Arm 2 does not** → the model needs explicit
   epidemiological framing, not merely a place name, to apply
   burden-appropriate reasoning. The failure mode is one level deeper than
   #1: naming India isn't enough, the model needs to be told what naming
   India implies clinically.
3. **Only Arm 4 closes it** → the specific protocol content is not reliably
   present in the model's parametric knowledge (or is present but not
   retrieved/applied even under maximal contextual framing short of the
   text itself). This is a **knowledge-absence failure requiring
   retrieval** — the fix is RAG/tool use against the actual protocol, not
   better prompting.
4. **Nothing closes it** (no arm reaches `PGC_k ≥ 0.5` with significance) →
   the failure is **not context-addressable** by any of the three
   interventions tested here. Reported as such, not forced into one of the
   three categories above — this is a genuine, distinct outcome, not a
   residual bucket to be explained away.

Rule 1-4 is evaluated **per divergence row** (`DIV-008`, `DIV-010`,
`DIV-016`, `DIV-017`, `DIV-020`, `DIV-021` as of this commit — see
`data/divergence/divergence_table.json`) and **per model**, not only in
aggregate — a model could show a prompting-level failure on one row and a
knowledge-absence failure on another, and the aggregate number would hide
that. Aggregate PGC is reported as a summary statistic, not the primary
finding.

## Outcomes

- **Primary outcome:** NTEP protocol deviation rate — the proportion of
  `ntep_correct_actions` a model's response fails to take, or the
  proportion of vignettes where the model's response matches
  `comparator_correct_actions` instead of (or in addition to failing)
  `ntep_correct_actions`, scored deterministically per RULE 6 against
  `critical_error_conditions` / `expected_divergence_points`. Reported per
  arm, per burden_class, per model.
- **Secondary outcomes:**
  - Critical error rate — proportion of responses tripping a
    `critical_error_conditions` flag, reported separately from the
    non-critical deviation rate (a model can be non-deviant on the letter
    of `ntep_correct_actions` while still committing a critical error, and
    the two must not be blended into one number).
  - Per-divergence-row difficulty — deviation rate broken out by
    `divergence_ids`, since Task 2's grounding cap (≤3 rows/vignette,
    age-band-filtered) was built specifically to make this attributable.
  - Seed variance — for any model/arm/row combination run at multiple
    seeds, the spread in deviation rate across seeds, reported so that a
    single-seed anomaly is never mistaken for a stable effect.

## Multiple comparisons

The primary outcome (aggregate NTEP deviation rate, Arm 1 vs. the interpretation-rule
classification) is not subject to a multiple-comparisons correction — it is
a single pre-specified test. All **secondary** outcome tests (per-row
difficulty comparisons, per-model comparisons, seed-variance tests) are
corrected using the Benjamini-Hochberg procedure at FDR = 0.05, applied
within each family of secondary tests (e.g., all per-row comparisons form
one family; do not pool across unrelated families before correcting).

## Holdout

Per RULE 7, vignettes tagged `holdout=true` in the stratification plan (15
of 100 as of Task 3's rebuild — see `scripts/build_stratification_plan.py`)
are excluded from every analysis in this study, including exploratory and
pilot analyses, until a single final confirmation run. That run is the only
point at which holdout vignettes are scored, and it happens once — not
iteratively while tuning the rubric or the arm prompts against holdout
feedback, which would defeat its purpose.

## Why TB-only with a protocol-context contrast, not a multi-disease prevalence contrast

The original design (session 1 of this project) contemplated a
multi-disease prevalence contrast — TB vs. snakebite vs. dengue — to test
whether LLM reasoning tracked disease-prevalence context across several
conditions at once. That design was narrowed to TB-only with a four-arm
protocol-context contrast for two reasons:

1. **Depth over breadth given the actual evidence base.** A credible
   divergence table requires primary-source citations on both sides for
   every row (RULE-equivalent citation discipline applied throughout Task
   1). Building and verifying that citation base for TB alone, against both
   NTEP and WHO's full modular guideline set, was already a multi-session
   effort (`data/protocols/FETCH_LOG.md`) that ended at 6 well-grounded
   rows rather than a padded table. Repeating that process credibly for
   snakebite and dengue protocols would have tripled the citation burden
   for a design that was ultimately testing the same underlying question
   (does context change protocol-appropriate reasoning) on three unrelated
   clinical domains, diluting depth on any one of them.
2. **The four-arm design needs a within-disease protocol-text arm (Arm 4),
   which a prevalence-only contrast doesn't test.** The multi-disease
   version could only ever answer "does the model reason differently when
   told the disease is more common here" — a prevalence-framing question.
   It could not distinguish a prompting-level failure from a
   knowledge-absence failure, because it never gave the model the actual
   protocol text to see whether that closes the gap when nothing else does.
   The TB-only redesign adds exactly that arm, which is what makes the
   interpretation rule above possible. A multi-disease study could be
   layered on top of this design in a future preregistration, but it would
   need Arm 4 done properly for each disease, not appended as an
   afterthought.

## Amendments

### 2026-08-06 (same day, later): reframed around NTEP-WHO consensus vs. US default

Written before any vignette existed and before any data was collected —
`data/vignettes/v1/` was empty at the time this amendment was appended, the
same condition under which the original document above was committed. This
is an amendment, not a correction: nothing above is edited in place, per
this document's own rule; everything below records what changed and why.

**What happened.** The divergence table above (data/divergence, "6 of 100"
vignette slots and "`DIV-008`, `DIV-010`, `DIV-016`, `DIV-017`, `DIV-020`,
`DIV-021`" as referenced in this document's original text) was the product
of re-sourcing the original 19-row NTEP-vs-US table against WHO's
consolidated guidelines. That re-sourcing pass found that NTEP and WHO
**converge** on 11 of the original 19 axes — universal drug-susceptibility
testing, molecular-first diagnosis, contact TPT breadth for MDR/RR-TB,
1HP adoption, empiric TPT for PLHIV and household contacts under 5, and
more. This was an unanticipated empirical result at the time the original
research question (above) was written: that question presumed NTEP-vs-WHO
divergence was itself the object of study, and did not anticipate that most
of the original table would turn out to be NTEP-WHO agreement instead.

**Why this changes the research question, not just the data.** Convergence
between NTEP and WHO is not a null result to route around — it is the
finding. It means India's national programme is closely aligned with
international consensus, and the still-current 2016/2017 ATS/CDC/IDSA
guidance — not NTEP — is the outlier both India and WHO have moved past.
Treating the 11 converged rows as dead weight and analyzing only the
residual 6 NTEP-vs-WHO differences would have thrown away the stronger,
more legible claim sitting in the data: the US accounts for a fraction of a
percent of global TB cases, India alone accounts for roughly 25%, so a
model that defaults to US guidance where WHO and NTEP already agree against
it systematically disadvantages the large majority of the world's TB
patients, not just India's.

**Revised research question**, replacing the one stated at the top of this
document: do frontier LLMs follow NTEP-WHO international consensus on TB
clinical decisions, or do they default to US national practice even where
WHO and India's national TB programme agree against it?

**Divergence table restructure.** Every row now carries three positions —
`ntep_position`, `who_position`, `us_position` — plus a `divergence_class`:
`consensus_divergence` (NTEP and WHO agree, US differs — the 11 reinstated
rows, primary dataset) or `national_adaptation` (NTEP differs from WHO —
6 rows, unchanged in substance from the version described earlier in this
document, secondary dataset). 17 rows total. See
`data/divergence/SUMMARY.md` and `data/divergence/UNVERIFIED.md` for the
full disposition history of every row.

**Revised primary outcome**, replacing "NTEP protocol deviation rate"
above: **consensus deviation rate** — the proportion of
`consensus_correct_actions` (the verbatim intersection of
`ntep_correct_actions` and `who_correct_actions`, computed automatically by
`tb_equity.schema.Vignette`) a model's response fails to take, scored only
on `consensus_divergence`-grounded vignettes, since `consensus_position` —
and therefore `consensus_correct_actions` — is only meaningfully defined
where NTEP and WHO agree.

**New secondary outcome: US-alignment rate** — the proportion of responses
that match `us_correct_actions` specifically where `us_correct_actions`
differs from the consensus position (i.e., on `consensus_divergence` rows,
where matching the US action means NOT matching consensus). This is the
outcome that directly tests the reframed hypothesis: a high US-alignment
rate on exactly the rows where WHO and NTEP agree against US practice is
direct evidence of default-to-US-practice behavior, not just a generic
protocol-deviation number that can't distinguish "wrong in some
idiosyncratic way" from "wrong in the specific direction of US guidance."

**divergence_class stratifies every analysis** from this point forward:
`consensus_divergence` rows test the primary hypothesis (consensus
deviation rate, US-alignment rate); `national_adaptation` rows test the
original secondary hypothesis from this document's "Research question"
section (does the model track NTEP's specific adaptation vs. WHO's more
conditional/discretionary position) and are analyzed separately, not pooled
into the primary consensus-deviation number. The stratification plan
(`scripts/build_stratification_plan.py`) targets roughly 75% of cells
grounded primarily in `consensus_divergence` rows and 25% in
`national_adaptation` rows, matching the relative importance of the two
hypotheses.

**Unchanged.** The four-arm design (baseline / location / epidemiological
base rates / retrieved protocol text) and the `PGC_k ≥ 0.5`-plus-significance
threshold for "substantially closes the gap" are unchanged from the
"Design" and "Interpretation rule" sections above — only what `gap_k`
is computed against shifts, from NTEP-vs-WHO deviation to consensus
deviation on `consensus_divergence` rows (and, for `national_adaptation`
rows, the original NTEP-vs-WHO framing still applies as-is). Multiple
comparisons (Benjamini-Hochberg on secondary outcomes) and the holdout
policy (RULE 7, unchanged proportion, now 15 of 100 per Task 3's rebuild)
are also unchanged.

### 2026-08-06 (same day, later still): matched-pair re-pairing on divergence_class

Caught before any data existed or any inference ran: the 100 vignettes in
`data/vignettes/v1/` had been hand-authored and `scripts/expand_arms.py`
had already been run to produce the 400 arm prompts, but no model had been
called and no scoring had happened. This amendment records a metadata-only
correction made at that point — no vignette stem, action list, or prompt
text was regenerated or edited.

**What happened.** `matched_pair_id` (`scripts/build_stratification_plan.py
::assign_matched_pairs`) matched each consensus_control vignette to an
india_high vignette on `age_band` and `num_distractors` within the same
`presentation_type`, with no constraint on `divergence_class`. An audit of
all 30 matched pairs against the amendment above's `divergence_class`
stratification found 15 of 30 pairs spanning classes — one member grounded
in `consensus_divergence` rows, the other in `national_adaptation` rows.
Per the amendment above, `consensus_correct_actions` (and therefore the
primary consensus-deviation outcome) is only meaningfully defined on
`consensus_divergence`-grounded vignettes; `national_adaptation`-grounded
vignettes have it empty by construction. Because `matched_pair_id` is
preserved as a covariate in analysis rather than collapsed (see "Design"
above), every cross-class pair had exactly one member eligible for the
primary-outcome dataset and one silently excluded — breaking the paired
india_high-vs-consensus_control contrast on the primary outcome for half
the set.

**Re-pairing rule applied.** Each vignette's `divergence_class` is taken as
the majority class among its `divergence_ids` (ties, which did not occur in
practice, resolve to `consensus_divergence`, the primary-outcome class).
`assign_matched_pairs` now treats this as a **hard constraint**: a
consensus_control vignette may only be matched to an india_high vignette of
the same `divergence_class`. Within that constraint, candidates are ranked
by `age_band` match, then `num_distractors` match, then `presentation_type`
match (soft preferences, in that priority order — `presentation_type` was
demoted from a hard partition because the india_high `national_adaptation`
pool, 13 vignettes, is small and unevenly spread across presentation types,
and hard-partitioning on both class and type would have left several
consensus_control cells unmatched even though a same-class partner of a
different type was available). Where no unused same-class india_high
vignette exists, `matched_pair_id` is set to `null` rather than forcing a
mismatched pair — this did not occur in practice: all 30 consensus_control
vignettes found a same-class partner (19 `consensus_divergence` pairs, 11
`national_adaptation` pairs).

**Result.** 30 of 30 matched pairs are now intact (same `divergence_class`
on both sides): 19 usable for the primary consensus-deviation contrast,
11 usable for the secondary `national_adaptation` (NTEP-vs-WHO) contrast.
Zero pairs span classes. 61 of 100 vignettes' `matched_pair_id` field
changed; no other field in any vignette file was touched.
`tests/test_stratification.py::test_matched_pairs_never_span_divergence_class`
now guards this at plan time.

**Not touched.** `data/prompts/` and its manifest do not reference
`matched_pair_id` anywhere — confirmed by grep — so no re-run of
`scripts/expand_arms.py` was needed and the 400 existing prompt files and
`data/prompts/manifest.json` are unchanged by this amendment.
