# Unverified / dropped claims

Companion to `divergence_table.json` and `FETCH_LOG.md`. Every claim below was
either (a) confirmed as a **convergence** and dropped per Task 2's instruction
("re-check every row currently tagged possible_convergence and either confirm
the convergence — drop the row — or find the specific axis on which they
still diverge"), or (b) a candidate row that could not be given a real
citation on both sides within this session's research budget, so it did not
go in the table. Nothing here should be used for vignette generation until
it is either promoted (with a real citation) or formally closed out.

## Confirmed convergences (dropped, not carried forward)

### MDR/RR-TB regimen composition (old draft DIV-005, "possible_convergence")

The old draft flagged "oral BPaLM vs individualized regimen" as a likely
false divergence. **Confirmed convergent as of 2025**, definitively:

- NTEP: National Guidelines for Management of DR-TB (27-3-2025) makes the
  6-month BPaLM regimen the first-choice treatment for eligible MDR/RR-TB
  patients aged >=14 years (p. 30, `NTEP_DR-TB_Guidelines_2025-03-27.pdf`).
- US: the ATS/CDC/ERS/IDSA guideline update (Saukkonen et al., Am J Respir
  Crit Care Med 2025;211(1), doi:10.1164/rccm.202410-2096ST) now strongly
  recommends the same 6-month BPaL (RR-, FQ-resistant) or BPaLM (RR-,
  FQ-susceptible) regimen for ages >=14y, superseding the 2019 guideline's
  individualized-regimen-only position (fetched via WebFetch against the
  IDSA guideline summary page — see FETCH_LOG.md).

Both programs landed on the same standardized 6-month regimen in the same
calendar year. Do not regenerate a vignette grounded in "the US treats
MDR-TB with an individualized regimen, NTEP with a fixed short regimen" —
that axis closed in 2025. The residual programmatic difference (NTEP
delivers BPaLM through a centralized, Nikshay-linked national program with
mandated directly-observed therapy; the US delivers it through individual
clinical practice) was considered as a replacement row (see below) but not
included — see "Dropped candidate rows."

### HIV testing recommendation itself (old draft DIV-023, "possible_convergence")

The old draft already flagged this as a likely false divergence ("if used,
ground the vignette in the linkage-to-care mechanism...not in whether HIV
testing is recommended at all"). Not independently re-verified this session
with a fresh primary-source read on the linkage-to-ART-care mechanism on
either side, so it is dropped rather than carried forward on the strength of
the old draft's own caveat. The **cotrimoxazole preventive therapy** angle
(DIV-019 in the rebuilt table) is a related, but independently and directly
verified, divergence — use that instead of resurrecting a testing-recommendation
row.

### TB in pregnancy — regimen selection (old draft DIV-020, "possible_convergence")

Not re-investigated this session. The old draft's own assessment (core
regimen guidance for drug-sensitive TB in pregnancy is aligned between NTEP
and ATS/CDC/IDSA) was not contradicted by anything found this session, so it
stays dropped. If revisited, ground any new row in antenatal-care
coordination/monitoring specifics, not regimen choice.

### Adherence-monitoring technology, "99DOTS" (old draft DIV-011, "possible_convergence")

Confirmed as likely convergent, though not with a dedicated US-side
citation. NTEP's 2025 Differentiated TB Care guidance frames current
adherence support as "digital platforms like Ni-kshay and AI-driven tools"
rather than the older 99DOTS-specific framing
(`NTEP_Differentiated_TB_Care_2025-03.pdf`), which is directionally the same
move toward digital/technology-assisted adherence monitoring the old draft
attributed to the US (video-observed therapy). No row added; if the US side
is ever independently sourced, this could become a real "specific technology
stack differs" row rather than a "does technology-assisted monitoring exist"
row.

## Dropped candidate rows (no citation on one or both sides)

These were drafted during Task 2 research but removed before finalizing
`divergence_table.json` because at least one side's citation was missing,
inferred-only-from-omission at a lower confidence than the table's existing
absence-based rows, or relied on a document that failed to fetch.

1. **Bidirectional TB-diabetes screening as a *mandated national policy*
   (2012 policy decision, 2017 National Framework for Joint TB-Diabetes
   Collaborative Activities).** The primary source
   (`tbcindia.gov.in/WriteReadData/National framework for joint TB diabetes
   23 Aug 2017.pdf`) could not be fetched — the `tbcindia.gov.in` domain does
   not resolve from this environment (see FETCH_LOG.md). Only secondary
   sources (news/journal articles) corroborate this. **DIV-018** in the
   table instead grounds the diabetes-comorbidity divergence in NTEP's 2025
   Differentiated TB Care triage thresholds, which *were* directly read and
   cited — a narrower but fully verified claim.

2. **DR-TB regimen delivery/administration model** (NTEP's mandatory
   directly-observed therapy, minimum 6 days/week, via a community-health-officer-assigned
   treatment supporter, for all DR-TB regimens including BPaLM — p. 30 of
   the DR-TB guidelines) **vs. a US-side equivalent.** No US-side citation
   describing an analogous (or contrasting) administration/supervision
   requirement was found this session. If pursued later, look for CDC's full
   provisional BPaL/BPaLM guidance document (only its "Dear Colleague
   Letter" landing page was fetched this session, which does not contain a
   supervision/DOT policy — see FETCH_LOG.md) or a current ATS/CDC/IDSA
   treatment-adherence statement.

3. **DR-TB (BPaLM) follow-up monitoring schedule** (NTEP's Table 3.4: monthly
   clinical review, CBC/ECG at day 15/30/monthly, visual acuity at week
   9/13/26, monthly culture from month 2 — `NTEP_DR-TB_Guidelines_2025-03-27.pdf`
   p. 36) **vs. a US-side monitoring cadence.** Same gap as #2 — the CDC BPaL
   provisional guidance document with monitoring specifics was not
   successfully fetched.

4. **TB meningitis / CNS TB regimen duration and corticosteroid protocol.**
   NTEP's side is well documented (2HRZE + 10HRE = 12 months, dexamethasone
   0.4mg/kg/day IV taper over 8-12 weeks — ICMR STW document). The 2016
   ATS/CDC/IDSA guideline (condensed/summary PDF actually fetched) only
   states that the continuation phase "is extended...for tuberculous
   meningitis, and bone, joint, and spinal tuberculosis" without giving the
   specific duration or steroid protocol in the condensed version — so this
   may be a **convergence** (both extend duration for CNS TB) rather than a
   divergence, but it cannot be confirmed either way without the full-text
   guideline. Do not draft a vignette claiming the two systems diverge on
   CNS TB treatment duration until this is resolved.

5. **Private-sector engagement structures (PPSA / free-drug-to-private-patients
   schemes).** Present in the old (unverified) draft as DIV-010. Not
   independently re-verified against a primary source this session beyond
   incidental mentions in the Differentiated TB Care document ("Leverage
   Private Infrastructure," "Participation in NTEP Initiatives" — too thin
   to cite as the substance of a row). Needs a dedicated fetch of NTEP's
   private-provider-engagement guidance.

6. **Confidentiality/disclosure norms given community stigma.** Present in
   the old draft as DIV-021. Not investigated this session at all — no
   primary source attempted.

7. **Infection control / home isolation resourcing.** Present in the old
   draft as DIV-016. Not investigated this session.

8. **Severe acute malnutrition assessment as its own divergence axis**
   (distinct from the diabetes-triage row). NTEP's BMI <14 kg/m2 (or <16
   with edema) threshold is documented in the same Box 4.3 table used for
   DIV-018, but no US-side citation for a comparable (or contrasting)
   malnutrition-severity assessment tool in TB care was found. Folded as
   supporting detail into DIV-013's social-support framing rather than made
   a standalone row.

## What this means for the 40-60 row target

`divergence_table.json` ships with **19 rows**, all with a real citation
(document, section/page, URL) on both the `ntep_position` and
`western_position` sides, verified against a primary source actually
fetched and read this session (13 PDFs + several HTML pages — see
`FETCH_LOG.md`). Reaching 40-60 rows at the same citation standard needs
more fetches, not more inference from what's already in hand — most of the
easy mileage from the 13 documents already downloaded has been extracted.
Priority next fetches: the full ATS/CDC/ERS/IDSA 2019 and 2025 DR-TB
guideline PDFs (only WebFetch-summarized this session, not archived), CDC's
full provisional BPaL/BPaLM guidance, the 2017 NTEP-diabetes framework via
an alternate URL/mirror (tbcindia.gov.in is unreachable from this
environment), and a dedicated NTEP private-sector-engagement document.
