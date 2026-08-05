# Divergence table summary

`divergence_table.json` rebuilt **2026-08-06** with the comparator changed
from ATS/CDC/IDSA ("Western") guidance to the **WHO consolidated guidelines
on tuberculosis** (Modules 1, 2, 3, 4, 5, plus the Module 4 operational
handbook). See the table's own `warning`/`row_count_note` fields, and
`UNVERIFIED.md`'s "2026-08-06: comparator changed from ATS/CDC/IDSA to WHO"
section, for the full rationale and the complete accounting of what
survived, what converged, and what was dropped as an absence claim.

**6 rows**, every row cited on both sides against a primary source actually
fetched and read this session (see `data/protocols/FETCH_LOG.md`). This is
well below the 10-16 rows anticipated going in. That is not a shortfall to
paper over: of the original 19 rows, **11 converged with WHO** once
re-sourced (DIV-001, 002, 003, 004, 005, 006, 007, 009, 011, 012, 019) and
**5 more were dropped as absence claims** (DIV-013, 014, 015, 018, plus
DIV-017 which was investigated and reinstated with a real citation — see
below). Two new paediatric-specific rows were added (DIV-020, DIV-021)
where WHO's newer guidance gives NTEP genuine room to diverge. Every axis
Task 1 asked to be checked for a new divergence (universal DST scope/timing,
weight-band dosing, contact TPT breadth, differentiated care, DR-TB regimen
choice) was checked against a fetched WHO source; most converged and are
documented as such rather than silently omitted.

## Why the comparator changed

The prior (2026-08-05) table scored NTEP mostly against a 2016 (treatment)
/2017 (diagnosis) ATS/CDC/IDSA US clinical practice guideline. That table's
own notes on DIV-001 already showed WHO Module 3 (2024) giving molecular-first
diagnosis a strong, high-certainty recommendation — meaning NTEP and WHO
already agreed on the single highest-stakes original row, and the surviving
"divergence" was really NTEP-vs-WHO-consensus vs. a US guideline that
international consensus had moved past. Continuing on that comparator would
have made the study's real question "do models follow 2017 US guidance or
2025 Indian guidance," not a health-equity question about protocol
adaptation to burden and resourcing. Switching to WHO as the comparator, and
dropping every row where NTEP and WHO turn out to agree, isolates what's
actually left: places where India's high-burden national program has made a
different operational choice than WHO's own global guidance.

## Composition

### By domain

| domain | count |
|---|---|
| treatment | 3 |
| prevention | 1 |
| differential | 1 |
| monitoring | 1 |
| diagnosis | 1 |
| **total** | **6** |

(DIV-021 is tagged `diagnosis`; DIV-020 and DIV-008 are `treatment`; DIV-010
is `prevention`; DIV-016 is `differential`; DIV-017 is `monitoring`.)

### By clinical_stakes

| clinical_stakes | count |
|---|---|
| high | 3 |
| moderate | 3 |

DIV-010 is the only row additionally flagged `is_critical_error_if_wrong:
true`.

### By divergence_type

| divergence_type | count |
|---|---|
| protocol_specific | 4 |
| resource_dependent | 2 |
| epidemiology_specific | 0 |
| prevalence_dependent | 0 |

### By applicable_age_bands

| row | child_0_9 | adolescent_10_17 | adult_18_59 | older_adult_60_plus |
|---|---|---|---|---|
| DIV-008 |  |  | x | x |
| DIV-010 |  | x | x | x |
| DIV-016 | x | x | x | x |
| DIV-017 |  | x | x | x |
| DIV-020 | x | x |  |  |
| DIV-021 | x | x |  |  |

Two rows (DIV-020, DIV-021) are paediatric-only; two (DIV-008, DIV-017)
exclude child_0_9 because their comparator citations use adult-calibrated
thresholds or documents; DIV-016 is the only row applicable across every
age band.

## The 6 surviving rows

1. **DIV-010** (high, critical-error-flagged) — Household contact TPT
   breadth: NTEP makes TPT standard (testing optional) for ALL household
   contacts regardless of age; WHO Module 1 only strongly/unconditionally
   recommends this for contacts under 5 — for contacts 5+/adolescents/adults
   WHO's own Recommendation 6 is conditional, with TBI-test confirmation
   "desirable."
2. **DIV-017** (high) — Differentiated/decentralized care operationalization:
   NTEP's Box 4.3 gives quantified vital-sign/lab thresholds mandating
   referral; WHO Module 4 recommends decentralization as a policy direction
   (conditional, very low certainty) without specifying thresholds.
   Reinstated from an absence-claim drop once a real WHO position was found.
3. **DIV-020** (moderate, paediatric) — 4-month vs 6-month regimen for
   non-severe paediatric TB: WHO Module 4 gives a strong, moderate-certainty
   recommendation for a 4-month regimen (3mo-16y, non-severe); NTEP's most
   recent paediatric guideline (Aug 2022) still specifies only the 6-month
   regimen. Flagged as time-sensitive — NTEP may have since adopted this.
4. **DIV-021** (moderate, paediatric) — Treatment-decision algorithm for
   bacteriologically-unconfirmed paediatric TB: WHO Module 5 offers an
   optional structured/scored algorithm (interim, conditional, very low
   certainty); NTEP relies on unstructured clinical judgment plus imaging
   pattern recognition.
5. **DIV-016** (moderate) — Active case-finding: NTEP runs ACF as routine
   national program policy across defined risk groups; WHO Module 2
   conditions general-population screening on a specific prevalence
   threshold (>=0.5%), a more evidence-gated posture.
6. **DIV-008** (moderate) — Treatment-extension discretion: NTEP explicitly
   leaves continuation-phase extension to physician judgment for slow
   responders; WHO's regimen is fixed-duration and explicitly discourages
   extending even the intensive phase on 2-month bacteriology.

## What converged (dropped, not weaknesses being hidden)

See `UNVERIFIED.md` for full citations. Short list: molecular-first
diagnosis (DIV-001), universal rifampicin-resistance DST (DIV-002), upfront
NAAT on extrapulmonary specimens (DIV-003), culture-not-mandatory-in-parallel
(DIV-004), TST/IGRA interchangeability regardless of BCG (DIV-005),
daily-only dosing (DIV-006), weight-band FDC dosing mechanism (DIV-007),
fixed 6-month levofloxacin for MDR/RR-TB contacts (DIV-009), no-testing-prerequisite
for PLHIV/under-5 TPT (DIV-011), 1HP availability (DIV-012), and universal
cotrimoxazole for HIV-positive TB patients (DIV-019). Also checked and found
convergent, never added as rows: DR-TB regimen choice (both use WHO's
BPaLM) and paediatric specimen-collection technique (both use gastric
aspirate/induced sputum for children who can't produce sputum — this is
exactly the clinical fact Task 2's Bug B fix needs vignette-writers to get
right, even though it isn't itself a divergence).

## What was dropped as an absence claim

DIV-013 (Nikshay Poshan Yojana DBT), DIV-014 (Ni-kshay Mitra donor program),
and DIV-015 (Nikshay notification platform) — WHO's consolidated guidelines
leave social-protection mechanisms and national IT/notification architecture
entirely to member-state discretion, so there is no WHO position to cite on
either side of these. DIV-018 (universal vs risk-gated diabetes screening)
was dropped because the actual WHO-adjacent source for that policy (the
WHO/IUATLD 2011 TB-diabetes collaborative framework) was not one of the
modules Task 1 specified for fetching, and no equivalent recommendation
exists in Modules 1-5.
