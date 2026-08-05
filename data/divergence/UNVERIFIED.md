# Unverified / dropped claims

Companion to `divergence_table.json` and `FETCH_LOG.md`. Every claim below was
either (a) confirmed as a **convergence** and dropped per Task 2's instruction
("re-check every row currently tagged possible_convergence and either confirm
the convergence — drop the row — or find the specific axis on which they
still diverge"), or (b) a candidate row that could not be given a real
citation on both sides within this session's research budget, so it did not
go in the table. Nothing here should be used for vignette generation until
it is either promoted (with a real citation) or formally closed out.

## 2026-08-06: comparator changed from ATS/CDC/IDSA to WHO

Everything below this heading documents what happened to the 19-row,
ATS/CDC/IDSA-comparator table (`rebuilt_on: "2026-08-05"`) when the
comparator was switched to the WHO consolidated guidelines. See
`divergence_table.json`'s `warning` and `row_count_note` fields for the
full rationale. Short version: DIV-001 (molecular-first diagnosis) already
converged under WHO Module 3 in the prior table's own notes field, which is
what triggered the re-sourcing — the study was at risk of measuring
"2017 US guidance vs 2025 Indian guidance" rather than a health-equity
question. Everything in the sections immediately below (from the older
2026-08-05 table version) is superseded by this pass and kept only for
audit history.

### Dropped: NTEP-WHO convergence

Each of these converged once re-sourced against a WHO module actually
fetched and read this session. "Converged" means a specific WHO
recommendation (not an inference) matches NTEP's position — these are not
absence claims.

- **DIV-001** (molecular-first diagnosis over smear+culture). WHO Module 3
  (20 Mar 2024) Recommendations 1-5 (p. 5): Xpert MTB/RIF or Xpert Ultra
  "should be used as an initial diagnostic test for TB and rifampicin-resistance
  detection... rather than smear microscopy/culture and phenotypic DST" —
  strong recommendation, high certainty, for adults; strong/moderate for
  children. Matches NTEP's upfront-NAAT workflow exactly. This was already
  flagged as the likely first casualty before re-sourcing began, and it was.
- **DIV-002** (universal rifampicin-resistance DST for every patient, not
  risk-gated). Same WHO Module 3 Recommendation 1 (p. 5) mandates
  rifampicin-resistance detection at the initial test for ALL adults with
  signs/symptoms of pulmonary TB — no risk-factor gate, unlike the old
  2017 ATS/CDC/IDSA comparator. Matches NTEP's "Universal DST" definition.
  WHO's own End TB Strategy language ("universal drug susceptibility
  testing", Module 3 p. 1) reinforces this as deliberate WHO policy, not
  an accident of the Xpert recommendation's wording.
- **DIV-003** (upfront NAAT on extrapulmonary specimens). WHO Module 3
  Recommendations 6-10 (p. 5-6 area) recommend Xpert Ultra as the initial
  test, rather than smear/culture, on CSF, pleural fluid, pericardial
  fluid, synovial fluid, urine, and other EP specimen types — matching
  NTEP's upfront-NAAT-on-any-accessible-EP-specimen approach. The old
  row's western_position was already flagged as inferred/weak; the WHO
  citation is directly on point and stronger.
- **DIV-004** (culture reached only downstream of a NAAT-positive result,
  not mandatory in parallel). Same WHO Module 3 Recommendation 1 (p. 5):
  Xpert "rather than smear microscopy/culture and phenotypic DST" as the
  initial test — WHO does not mandate parallel culture on every specimen
  either, unlike the old 2017 ATS/CDC/IDSA comparator's Recommendation 6.
- **DIV-005** (TST/IGRA treated as interchangeable regardless of BCG
  history). WHO Module 1 (9 Sep 2024) Recommendation 17 (p. 19-20 area):
  "Either a TST or an IGRA can be used to test for LTBI" (strong
  recommendation), with the accompanying GDG discussion stating explicitly
  that "a history of BCG vaccination has a limited effect on interpretation
  of TST results later in life; hence, BCG vaccination should not be a
  determining factor in selecting a test." This is the opposite of the old
  2017 ATS/CDC/IDSA comparator's BCG-gated IGRA preference, and matches
  NTEP's interchangeable-options framing.
- **DIV-006** (daily dosing throughout, no intermittent continuation-phase
  option). WHO Module 4 (15 Apr 2025) Recommendation 1.2 (p. 4): daily
  dosing throughout is the recommended frequency (strong, high certainty),
  and Recommendation 1.3: thrice-weekly dosing "is not recommended in both
  the intensive and continuation phases" (conditional, very low certainty).
  WHO has moved further toward daily-only than even NTEP's position implies
  is mandatory elsewhere; this fully converges with NTEP's no-intermittent-option
  policy, superseding the old 2016 ATS/CDC/IDSA comparator, which
  conditionally permitted thrice/twice-weekly continuation dosing.
- **DIV-007** (weight-band FDC tablet-count dosing vs per-kg calculation).
  WHO's own operational handbook companion to Module 4 publishes a weight-band
  FDC dosing table structurally identical in mechanism to NTEP's (Annex 4.1,
  "Dosages of anti-TB medicines by weight band for treatment of DS-TB", p. 371,
  `WHO_Module4_OperationalHandbook_2025.pdf`, bands 25-<30/30-<35/35-<50/50-<65/65+ kg).
  WHO Module 4 Recommendation 1.4 also recommends FDCs over separate
  formulations. The exact kg cutoffs differ slightly from NTEP's bands, but
  per Task 1's instruction not to preserve a row by hunting for a marginal
  sub-difference, that is not treated as a surviving divergence.
- **DIV-009** (fixed 6-month levofloxacin regimen for MDR/RR-TB contacts,
  not merely conditionally-recommended/individualized). WHO Module 1
  Recommendation 21 (p. 27): "6 months of daily levofloxacin should be used
  as TB preventive treatment" for contacts exposed to MDR/RR-TB — strong
  recommendation, moderate certainty, based on the V-QUIN/TB-CHAMP trials.
  This is a 2024 WHO update that supersedes the old 2019 ATS/CDC/ERS/IDSA
  comparator's conditional/individualized stance and now matches NTEP's
  fixed 6Lfx regimen exactly.
- **DIV-011** (TBI testing not required before TPT for PLHIV or child
  contacts under 5). WHO Module 1 narrative (p. 20 area): "A positive test
  for TBI before starting TPT for MDR/RR-TB is not required for child
  contacts or people with immunocompromising conditions," and the general
  TPT section states testing "not be a prerequisite for starting TPT in
  people with HIV and in household contacts aged <5 years." Matches NTEP's
  position exactly.
- **DIV-012** (1HP as a programmatically available TPT option). WHO Module 1
  Recommendation 20 (p. 21): a 1-month regimen of daily rifapentine plus
  isoniazid (1HP) "may be used" (conditional, low-moderate certainty) —
  already WHO policy since the 2020 update, predating NTEP's Dec 2024
  addendum. The old row's premise (US guidance hadn't adopted 1HP) is true
  but irrelevant once WHO, not the US, is the comparator: WHO already had it.
- **DIV-019** (cotrimoxazole preventive therapy for all HIV-positive TB
  patients regardless of CD4 count). The 2016 ATS/CDC/IDSA guideline text
  itself (cited in the old row) already stated that WHO recommends CPT for
  all HIV-positive TB patients regardless of CD4 — i.e., NTEP's universal
  CPT position was already known to match WHO's, and the divergence was
  only ever against the narrower US practice pattern. Confirmed convergent
  under the new comparator.

### Dropped: absence-claim rows (per explicit instruction / consistent extension)

Per Task 1(c), DIV-013, DIV-014, and DIV-017 were to be dropped outright
because their old `western_position` was an absence claim (a document that
simply never mentioned the topic), unless a real WHO position could be
found, in which case they could be reinstated with that citation.

- **DIV-013** (Nikshay Poshan Yojana direct benefit transfer). No WHO
  position found — WHO consolidated guidelines do not specify or mandate a
  cash-transfer mechanism; this is a national social-protection policy
  choice WHO leaves entirely to member states. Dropped, not reinstated.
- **DIV-014** (Ni-kshay Mitra community-donor program). Same reasoning as
  DIV-013 — no WHO position on community-donor food-basket programs.
  Dropped, not reinstated.
- **DIV-017** (quantified triage/referral thresholds). **Reinstated** — see
  `divergence_table.json`. WHO Module 4 Recommendations 2.1/2.2/3.1 (p. 178-179)
  give the general policy direction (decentralize care) without a
  quantified vital-sign/lab threshold, which is a genuine, citable contrast
  with NTEP's specific Box 4.3 thresholds, not an absence claim.

Two more rows were dropped by extending the same absence-claim principle on
our own initiative, since neither could be defended under Task 1's citation
discipline once WHO became the comparator:

- **DIV-015** (Nikshay as a single case-based platform linking notification
  to DBT disbursement). No WHO position found — WHO's consolidated
  guidelines do not specify or mandate a particular national notification
  IT architecture; this is left entirely to national discretion, the same
  as DIV-013/014. Dropped.
- **DIV-018** (universal glucose/HbA1c screening for all TB patients vs
  ADA-risk-factor-gated screening). The old western_position's citation
  (2016 ATS/CDC/IDSA) is gone with the comparator change, and no equivalent
  WHO recommendation on universal vs risk-gated diabetes screening for TB
  patients was found in Modules 1-5 (the actual source for this policy is
  the WHO/IUATLD 2011 "Collaborative framework for care and control of
  tuberculosis and diabetes," which was not one of the modules Task 1
  specified for fetching). Dropped rather than cited to a document not
  actually read this session. If revisited, fetch that framework document
  directly before reinstating.

### New rows added

**DIV-020** (paediatric 4-month non-severe regimen) and **DIV-021**
(paediatric treatment-decision algorithm) were added — see
`divergence_table.json`. Both are paediatric-specific, sourced from WHO
Module 4/5, and both carry an explicit caveat in the table's own `notes`
field about being time-sensitive/interim WHO recommendations that should be
re-verified before reuse.

### Candidates checked and found NOT to diverge (not added as rows)

Recorded here so this ground isn't re-covered in a future session:

- **DR-TB regimen choice (BPaLM).** NTEP has adopted WHO's BPaLM regimen as
  "treatment of choice for eligible patients" (`NTEP_DR-TB_Guidelines_2025-03-27.txt`),
  matching WHO Module 4 Recommendation 1.1 (conditional, very low
  certainty). Converges; not a row.
- **Paediatric specimen collection (gastric aspirate / induced sputum for
  children unable to produce sputum).** Both NTEP's paediatric guideline
  and WHO Module 3/5 recommend the same alternative specimen types for
  children. Converges; not a row. (This *was* the source of Task 2's Bug B
  smoke-test failure — a 7-year-old vignette asked about sputum NAAT — but
  the fix there is age-appropriate vignette writing, not a new divergence
  row, since NTEP and WHO already agree on what the right specimen is.)
- **Paediatric weight-band dosing cutoffs.** Same reasoning as DIV-007 —
  WHO's operational handbook publishes paediatric weight-band dosing tables
  too; exact kg cutoffs were not compared in detail since Task 1
  specifically warns against hunting for marginal sub-differences.

## Confirmed convergences (dropped, not carried forward) — 2026-08-05 pass, superseded above

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
