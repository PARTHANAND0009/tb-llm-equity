# Divergence table summary

`divergence_table.json` restructured **2026-08-06** as a three-way table:
every row now carries `ntep_position`, `who_position`, and `us_position`
simultaneously, tagged `divergence_class`. See the table's own
`warning`/`row_count_note` fields, and `UNVERIFIED.md`'s "table restructured
as three-way" section, for the full rationale.

**17 rows.** Every row cited on the NTEP and WHO sides against a primary
source actually fetched and read (`data/protocols/FETCH_LOG.md`); `us_position`
is cited wherever a real US-side document addresses the point, and left
explicitly `null` (not inferred) for the 2 rows where none was fetched
(DIV-020, DIV-021).

## Why this reframe

The prior (WHO-only) rebuild found that NTEP converges with WHO on 11 of the
original 19 axes — universal DST, contact TPT breadth, 1HP adoption, MDR
contact regimens, empiric TPT for PLHIV and under-5s, and more. That is not
a null result. It means India's national programme is closely aligned with
international consensus, and the still-current 2016/2017 ATS/CDC/IDSA
guidance — not NTEP — is the outlier both WHO and India have moved past.
The study question is reframed accordingly:

> Do frontier LLMs follow international consensus on TB clinical decisions,
> or do they default to US national practice even where WHO and India's
> national programme agree against it?

This is a stronger equity claim than the prior framing: the US accounts for
a fraction of a percent of global TB cases; India alone accounts for roughly
25%. A model that anchors on US guidance where consensus says otherwise
systematically disadvantages the large majority of the world's TB patients,
not just India's.

## divergence_class

- **`consensus_divergence`** (11 rows) — NTEP and WHO agree; US guidance
  differs. This is the **primary dataset** for the reframed study: it lets a
  vignette test directly whether a model's response tracks consensus or
  defaults to US practice.
- **`national_adaptation`** (6 rows) — NTEP differs from WHO (WHO leaves the
  point to national discretion, or the two programs made different
  operational choices). **Secondary analysis**: this is the residual "India
  vs the world" axis from the prior framing, kept because it's still a real,
  well-cited difference — just not the primary hypothesis anymore.

## Composition

### By divergence_class

| divergence_class | count |
|---|---|
| consensus_divergence | 11 |
| national_adaptation | 6 |
| **total** | **17** |

### By domain

| domain | consensus_divergence | national_adaptation | total |
|---|---|---|---|
| diagnosis | 5 (001, 002, 003, 004, 005) | 1 (021) | 6 |
| treatment | 2 (006, 007) | 2 (008, 020) | 4 |
| prevention | 2 (011, 012) | 1 (010) | 3 |
| resistance | 1 (009) | 0 | 1 |
| comorbidity | 1 (019) | 0 | 1 |
| differential | 0 | 1 (016) | 1 |
| monitoring | 0 | 1 (017) | 1 |
| **total** | **11** | **6** | **17** |

### By clinical_stakes

| clinical_stakes | consensus_divergence | national_adaptation |
|---|---|---|
| critical | 3 (001, 002, 009) | 0 |
| high | 4 (003, 006, 011, 019) | 2 (010, 017) |
| moderate | 4 (004, 005, 007, 012) | 4 (008, 016, 020, 021) |

5 rows are additionally flagged `is_critical_error_if_wrong: true`: DIV-001,
DIV-002, DIV-006, DIV-009 (all `consensus_divergence`), and DIV-010 (the
`national_adaptation` table's only critical-error-flagged row, despite being
`high` rather than `critical` stakes).

## The highest-stakes consensus_divergence rows (primary dataset)

1. **DIV-001** (critical) — **Flagship row.** Initial diagnostic test for
   presumptive pulmonary TB: NTEP and WHO both give molecular-first testing
   a strong recommendation (WHO Module 3, Recs 1-2, high certainty); the
   2017 US guideline treats smear+culture as mandatory with only a
   conditional, low-quality-evidence recommendation for NAAT.
2. **DIV-002** (critical) — Scope of rapid rifampicin-resistance testing:
   NTEP's Universal DST and WHO Module 3's Recs 1-2 both mandate testing for
   every patient; the 2017 US guideline limits it to four risk criteria.
3. **DIV-009** (critical) — TPT for household contacts of MDR/RR-TB: NTEP's
   2024 addendum and WHO's 2024 Module 1 Recommendation 21 now both mandate
   a fixed 6-month levofloxacin regimen; the 2019 US guideline only
   conditionally recommends treating at all, with an individualized regimen.
4. **DIV-006** (high, critical-error-flagged) — Dosing schedule: NTEP and
   WHO Module 4 (2025) are both daily-only throughout treatment; the 2016 US
   guideline conditionally permits intermittent continuation-phase dosing.
5. **DIV-003** (high) — Extrapulmonary specimen testing: NTEP and WHO Module
   3's specimen-specific recommendations both put molecular testing first
   across specimen types; the US guideline's NAAT stance stays
   pulmonary-focused (lower-confidence row — inferred US silence, not a
   stated contrary rule).
6. **DIV-011** (high) — TPT for PLHIV: NTEP and WHO both state TBI testing
   is not a prerequisite; the US guideline's regimens are scoped to
   confirmed LTBI (inferential — see table notes).
7. **DIV-019** (high) — Cotrimoxazole for HIV-positive TB patients: NTEP and
   WHO's universal, CD4-unconditioned policy vs. the US guideline's own
   text, which states the US restricts CPT to CD4 <200 — one of the
   best-grounded rows in the table, since the contrast is stated explicitly
   within the US source itself.
8. **DIV-004** (moderate) — Culture not mandatory in parallel with
   molecular testing: NTEP and WHO both reserve culture for the downstream
   resistance cascade; the 2017 US guideline mandates culture on every
   specimen regardless of NAAT result.
9. **DIV-005** (moderate) — TST/IGRA interchangeability regardless of BCG
   history: NTEP and WHO both treat the tests as equivalent; the 2017 US
   guideline recommends IGRA specifically for BCG-vaccinated individuals.
10. **DIV-007** (moderate) — Dosing mechanism: NTEP and WHO's own
    operational handbook both use weight-band FDC tablet counts; the 2016 US
    guideline calculates mg/kg per patient — a mechanism-level difference,
    not a marginal band-cutoff variation.
11. **DIV-012** (moderate) — 1HP regimen availability: WHO has recommended
    it since 2020 and NTEP adopted it in Dec 2024; the standing 2020 US
    guideline doesn't list it as a regimen option.

## national_adaptation rows (secondary dataset)

1. **DIV-010** (high, critical-error-flagged) — Household contact TPT
   breadth for ages 5+/adolescents/adults: NTEP makes this standard,
   testing-optional practice; WHO's own Recommendation 6 is only
   conditional, with TBI-test confirmation "desirable." No consensus to
   synthesize — this is NTEP going further than WHO's own recommendation.
2. **DIV-017** (high) — Differentiated/decentralized care thresholds: NTEP's
   Box 4.3 gives quantified vital-sign/lab thresholds; WHO recommends
   decentralization as a direction without specifying thresholds. Notably,
   WHO and the US guideline land in a similar place here (neither specifies
   a quantified threshold) — NTEP is the outlier on this particular row.
3. **DIV-008** (moderate) — Treatment-extension discretion: NTEP explicitly
   authorizes physician judgment; WHO's regimen is fixed-duration with an
   explicit anti-extension recommendation for the intensive phase.
4. **DIV-016** (moderate) — Active case-finding: NTEP runs ACF as routine
   national policy; WHO Module 2 conditions general-population screening on
   a specific prevalence threshold (>=0.5%).
5. **DIV-020** (moderate, paediatric) — 4-month vs 6-month regimen for
   non-severe paediatric TB: WHO Module 4 recommends 4 months (strong,
   moderate certainty); NTEP's Aug 2022 guideline still specifies only 6
   months. Time-sensitive — NTEP may have since updated.
6. **DIV-021** (moderate, paediatric) — Treatment-decision algorithm: WHO
   Module 5 offers an optional structured/scored tool (interim, conditional,
   very low certainty); NTEP relies on unstructured clinical judgment.

## What remains dropped

DIV-013 (Nikshay Poshan Yojana DBT), DIV-014 (Ni-kshay Mitra donor program),
DIV-015 (Nikshay notification platform), and DIV-018 (universal vs
risk-gated diabetes screening) remain dropped as absence claims — WHO's
consolidated guidelines leave social-protection mechanisms, national IT
architecture, and (within the modules fetched) diabetes-screening policy
entirely to member-state discretion, so there is no WHO position to cite on
either side. See `UNVERIFIED.md` for full detail.
