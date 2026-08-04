# Divergence table summary

`divergence_table.json` rebuilt 2026-08-05 from 13 primary-source PDFs + several
HTML pages actually fetched and read this session (list: `FETCH_LOG.md`).
19 rows, every row cited on both sides. See `UNVERIFIED.md` for confirmed
convergences that were dropped and candidate rows that didn't make the cut.

## Composition

### By domain

| domain | count |
|---|---|
| diagnosis | 5 |
| treatment | 3 |
| prevention | 3 |
| comorbidity | 2 |
| social_support | 2 |
| resistance | 1 |
| differential | 1 |
| monitoring | 1 |
| notification | 1 |
| **total** | **19** |

### By clinical_stakes

| clinical_stakes | count |
|---|---|
| critical | 4 |
| high | 8 |
| moderate | 7 |

6 of the 19 rows are additionally flagged `is_critical_error_if_wrong: true`
(a model getting this specific point wrong is itself a scorable critical
error, not just a missed nuance): DIV-001, DIV-002, DIV-006, DIV-009,
DIV-010, DIV-018.

### By divergence_type

| divergence_type | count |
|---|---|
| protocol_specific | 10 |
| resource_dependent | 7 |
| epidemiology_specific | 2 |
| prevalence_dependent | 0 |

## The 10 highest-stakes verified divergences

1. **DIV-001** (critical) — Initial diagnostic test for presumptive pulmonary
   TB: NTEP's molecular-first cascade vs. the still-standing 2017 ATS/CDC/IDSA
   guideline's mandatory smear+culture with only conditional, low-quality-evidence
   support for NAAT.
2. **DIV-002** (critical) — Scope of rapid molecular resistance testing:
   NTEP's universal DST (every patient, within 15 days) vs. ATS/CDC/IDSA's
   testing limited to four specific risk criteria.
3. **DIV-009** (critical) — TPT for household contacts of MDR/RR-TB: NTEP's
   standardized fixed 6Lfx/4R regimens vs. the 2019 US guideline's only
   conditional recommendation to treat at all (vs. observation alone).
4. **DIV-010** (critical) — Household contact TPT eligibility: NTEP now
   covers all ages with treatment proceeding even without TBI testing, not
   limited to child contacts under 6 as the prior (unverified) draft claimed.
5. **DIV-006** (high, critical-error-flagged) — DS-TB regimen dosing
   schedule: NTEP is daily-only throughout; the US guideline conditionally
   allows thrice-/twice-weekly continuation-phase dosing in low-risk
   patients.
6. **DIV-018** (high, critical-error-flagged) — Diabetes comorbidity
   screening: NTEP applies structured glycemic thresholds to TB patients
   broadly via its 2025 triage tool; the US guideline gates glucose/HbA1c
   testing on ADA risk factors (age, BMI, family history, race/ethnicity).
7. **DIV-003** (high) — Extrapulmonary TB specimen testing: NTEP's
   upfront-NAAT-across-specimen-types approach vs. the more
   culture/histology-anchored US framework (lower-confidence row — see notes
   in the table).
8. **DIV-008** (high) — Treatment extension for slow responders: NTEP leaves
   this to case-by-case physician discretion; the US guideline has a
   specific evidence-based rule (cavitation + 2-month-culture-positive -> 9
   months total).
9. **DIV-011** (high) — TPT for PLHIV: NTEP does not require TBI testing
   before starting; the US guideline's regimen recommendations are framed
   around confirmed LTBI.
10. **DIV-013** (high) — Nikshay Poshan Yojana nutritional DBT: Rs
    1000/month (revised from Rs 500/month, effective 1 Nov 2024) with no
    documented US equivalent.

## Corrections to the prior (unverified) draft

Two specific facts the user flagged for verification were confirmed **wrong**
in the prior training-knowledge draft:

- **Nikshay Poshan Yojana benefit amount**: was Rs 500/month, confirmed
  **revised to Rs 1000/month effective 1 November 2024** (PIB/MoHFW,
  "Initiatives & Achievements-2024," p. 8). See DIV-013.
- **TPT eligibility for household contacts**: the draft claimed NTEP limits
  preventive therapy to child contacts under 6. **Confirmed false** — NTEP's
  2021 TPT guideline already covered household contacts of all ages, and a
  December 2024 addendum added the 1HP regimen (age >=13) plus standardized
  regimens for contacts of drug-resistant index cases. See DIV-010, DIV-009,
  DIV-012.

One row was confirmed **convergent** and dropped rather than kept as a
divergence: MDR/RR-TB regimen composition. Both NTEP (March 2025) and the US
ATS/CDC/ERS/IDSA guideline (2025 update) now recommend the same 6-month
BPaLM/BPaL regimen as first-line for eligible patients — see `UNVERIFIED.md`
for the full writeup.
