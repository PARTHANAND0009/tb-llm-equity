# Vignette generation prompt -- STRAT-100 -> VIG-100

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `data/vignettes/v1/VIG-100.json`

## System instructions

You write clinical vignettes for a research study auditing whether LLMs
follow NTEP-WHO international consensus on TB clinical decisions, or
default to US national practice (ATS/CDC/IDSA) even where NTEP and WHO
agree against it.

HARD CONSTRAINTS — violating any of these makes the vignette unusable:
1. Ground the case ONLY in the divergence-table rows given to you below. Do not
   invent clinical facts unrelated to those rows. Never free-generate.
2. The stem must NOT name or imply a country, city, state, or health system by
   name (no "in India", "under NTEP", "in the US", hospital names, etc.).
   Location is a separate experimental manipulation applied later — the stem
   must read as clinically location-neutral.
3. Include at least two plausible competing/distractor diagnoses seeded
   naturally into the history or exam findings.
4. Do NOT write a textbook-perfect presentation. Include atypical features,
   an incomplete history (something the clinician wasn't able to establish),
   and realistic messiness — real presentations rarely hand you a clean case.
5. For each grounding row tagged divergence_class "consensus_divergence",
   ntep_correct_actions and who_correct_actions MUST share the overlapping
   action(s) verbatim, character-for-character identical strings — not
   paraphrased restatements of the same idea. This is not optional: a
   downstream scorer computes the intersection of these two lists by exact
   string match to detect whether a model followed consensus, and a
   paraphrase breaks that match silently. Only the action(s) unique to one
   side (if any) may differ in wording. For rows tagged "national_adaptation"
   there is no such requirement — NTEP and WHO are not expected to agree.
6. Respond with a single JSON object matching exactly this shape (no prose
   outside the JSON):
   {
     "stem": str,
     "patient": {"age": str, "sex": "male"|"female", "occupation": str,
                  "social_history": str, "presenting_complaint": str,
                  "duration": str, "exam_findings": str,
                  "prior_treatment": str, "comorbidities": [str, ...]},
     "distractors": [str, str, ...],
     "ntep_correct_actions": [str, ...],
     "who_correct_actions": [str, ...],
     "us_correct_actions": [str, ...],
     "critical_error_conditions": [str, ...],
     "expected_divergence_points": [str, ...]
   }
   Do NOT include a "consensus_correct_actions" key -- it is computed
   automatically from ntep_correct_actions/who_correct_actions and would be
   rejected if present.


## Case brief

Generate ONE vignette for stratification cell STRAT-100.

burden_class: consensus_control — this is NOT the same case relabeled. The
control arm represents the NTEP-WHO consensus position, not a "Western"
epidemiological setting. What that means depends on each grounding row's
divergence_class:
- For rows tagged "consensus_divergence" (NTEP and WHO agree): the correct
  action is IDENTICAL to the india_high arm's -- ntep_correct_actions and
  who_correct_actions both apply here too. Write a case with different
  surface epidemiology (e.g. lower local TB prevalence, a setting without
  India-specific program infrastructure) but the SAME underlying clinical
  logic, so the vignette tests whether the correct (consensus) action
  survives a change in framing, not whether the answer itself changes.
- For rows tagged "national_adaptation" (NTEP differs from WHO): write a
  case whose epidemiology is plausible for a setting where WHO's own
  conditional/discretionary recommendation -- not NTEP's more prescriptive
  national-program adaptation -- is what actually governs care (e.g. a
  setting without NTEP's specific quantified triage protocol, where WHO's
  general decentralization guidance applies without a codified threshold).
  Ground the reasoning in who_correct_actions here, not ntep_correct_actions.
This case must be matched to its india_high counterpart (stratification cell
STRAT-064) on presentation complexity, age band, and number of
distractors — but it must read as a distinct clinical scenario, not the same
stem with a different label.

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: contact_management
- subtype: household_contact_mdr_tb
- age_band: older_adult_60_plus (pick a specific age consistent with this band)
- sex: female
- setting: rural (reflect this in social/occupational detail, not a
  place name)
- occupation_class: factory_or_industrial_worker
- comorbidity_burden: none
- symptom_duration_band: 12_plus_weeks_delayed_presentation
- num_distractors: exactly 3

Ground the case in these divergence-table rows (cite the reasoning that
follows from them in ntep_correct_actions / who_correct_actions /
us_correct_actions / expected_divergence_points — do not introduce clinical
content unrelated to these rows; note each row's divergence_class, per the
instructions above on when ntep/who must share verbatim overlapping text):

[
  {
    "id": "DIV-010",
    "decision_point": "Are household contacts aged 5 years and older (including adolescents and adults) given TB preventive treatment as a standard, undeferred action, or only conditionally, with TBI testing desirable first?",
    "domain": "prevention",
    "divergence_class": "national_adaptation",
    "applicable_age_bands": [
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP's 2021 TPT guideline states that ALL household contacts of pulmonary TB patients, regardless of age, should be given TPT after ruling out active TB. Contacts under 5 years receive TPT empirically without TBI testing; contacts 5 years and older and adults should be offered CXR and TBI testing wherever available, but 'TPT must not be deferred' if such testing is unavailable -- TPT is standard practice for this group, not conditional.",
    "ntep_citation": {
      "doc": "Central TB Division, Guidelines for Programmatic Management of Tuberculosis Preventive Treatment in India (2021)",
      "section": "2.1.2 All household contacts of pulmonary TB patients (p. 5)",
      "url": "https://tbcindia.mohfw.gov.in/wp-content/uploads/2023/05/Guidelines-for-Programmatic-Management-of-Tuberculosis-Preventive-Treatment-in-India.pdf"
    },
    "who_position": "WHO Module 1 Recommendation 5 strongly and unconditionally recommends TPT for household contacts under 5 -- matching NTEP -- but Recommendation 6 only says household contacts aged 5 years and older, adolescents, and adults 'MAY be given' TPT, and the accompanying text describes this as a CONDITIONAL recommendation where 'confirmation of TBI with either IGRA or a skin test would be desirable' before treating. WHO leaves the >=5/adult group to national discretion; NTEP has exercised that discretion by making TPT standard and testing optional for this group too.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 1: prevention (9 Sep 2024, 2nd edition)",
      "section": "Executive summary Recommendations 5-6 (p. xiii) and narrative discussion of recommendation strength/certainty (p. 20 area)",
      "url": "https://iris.who.int/server/api/core/bitstreams/314ddea2-6fc2-4ff0-9357-a038feca1d31/content"
    },
    "us_position": "The CDC/NTCA 2020 guideline is scoped as treatment of confirmed latent TB infection -- its recommended regimens (3HP, 4R, 3HR preferred) are framed as treatment once LTBI has been established, implying a test-confirm-then-treat sequence structurally different from both NTEP's empiric-if-testing-unavailable approach and WHO's testing-desirable-but-conditional approach.",
    "us_citation": {
      "doc": "Guidelines for the Treatment of Latent Tuberculosis Infection: Recommendations from NTCA and CDC, 2020, MMWR Recomm Rep 2020;69(1):1-11",
      "section": "Preferred regimens (p. 3); document title and scope",
      "url": "https://www.cdc.gov/mmwr/volumes/69/rr/pdfs/rr6901a1-H.pdf"
    },
    "consensus_position": null,
    "clinical_stakes": "high",
    "is_critical_error_if_wrong": true,
    "still_diverges_as_of": "2026-08",
    "notes": "national_adaptation: NTEP and WHO diverge here (NTEP mandatory/testing-optional vs WHO conditional/testing-desirable for the >=5 group), so there is no consensus_position to synthesize. US position included for completeness -- structurally distinct from both, not merely a third variant of the same axis. Excludes child_0_9: the divergent zone is specifically the >=5 group, and this repo's child_0_9 band straddles the WHO <5/>=5 dividing line."
  },
  {
    "id": "DIV-016",
    "decision_point": "Is population-level active case-finding (ACF) conducted as a routine, programmatically mandated activity in defined risk groups/areas, or only conditionally once a locally estimated TB prevalence threshold is met?",
    "domain": "differential",
    "divergence_class": "national_adaptation",
    "applicable_age_bands": [
      "child_0_9",
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP runs systematic active case-finding (ACF) -- house-to-house searches -- as a routine, mandated national program activity targeted at defined high-risk groups (PLHIV, diabetics, undernourished persons, residents of prisons/asylums/old-age-homes/orphanages, tribal areas, marginalized populations), which had diagnosed an additional 3 lakh TB cases over the prior 6 years as of the 2024 report. This is standing program policy, not contingent on a documented local prevalence survey result before initiation.",
    "ntep_citation": {
      "doc": "Ministry of Health & Family Welfare, \"Initiatives & Achievements-2024\" (PIB)",
      "section": "Item 6, Active Case Finding (p. 8)",
      "url": "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2024/dec/doc20241228477601.pdf"
    },
    "who_position": "WHO Module 2 Recommendation 1 conditions general-population systematic screening on a specific, quantified threshold: 'may be conducted among the general population in areas with an estimated TB prevalence of 0.5% or higher' (conditional recommendation, low certainty of evidence). WHO structures ACF as a threshold-gated, evidence-triggered activity rather than a standing national program run across defined risk groups regardless of a locally demonstrated prevalence figure.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 2: screening -- systematic screening for tuberculosis disease (22 Mar 2021)",
      "section": "2.1 Systematic screening for TB disease among the general population, Recommendation 1 (p. 13)",
      "url": "https://iris.who.int/server/api/core/bitstreams/0633a78b-581c-47f2-a148-bad704cc0e50/content"
    },
    "us_position": "The 2017 ATS/CDC/IDSA guideline's discussion of pediatric case identification frames the primary US case-finding mechanism as contact investigation following a known adult/adolescent index case, consistent with a predominantly passive, contact-investigation-driven case-finding model rather than population-level house-to-house ACF drives -- a third, distinct model from both NTEP's routine ACF and WHO's threshold-gated screening.",
    "us_citation": {
      "doc": "Lewinsohn DM et al., Diagnosis of Tuberculosis in Adults and Children, Clin Infect Dis 2017;64(2):e1-e33",
      "section": "Discussion of contact investigation as the identification pathway (p. e19 area)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/diagnosis-of-tuberculosis-in-adults-and-children.PDF"
    },
    "consensus_position": null,
    "clinical_stakes": "moderate",
    "is_critical_error_if_wrong": false,
    "still_diverges_as_of": "2026-08",
    "notes": "national_adaptation: NTEP's routine, risk-group-targeted ACF is more expansive/less evidence-gated than WHO's own conditional, prevalence-threshold-based recommendation, so there is no single consensus_position. US position is included for completeness and happens to describe a third, passive model distinct from both."
  }
]


## Output contract

Write the complete vignette to `data/vignettes/v1/VIG-100.json` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{
  "id": "VIG-100",
  "version": "v1",
  "burden_class": "consensus_control",
  "presentation_type": "contact_management",
  "matched_pair_id": "VIG-064",
  "divergence_ids": [
    "DIV-010",
    "DIV-016"
  ],
  "stem": "...",
  "patient": {
    "age": "...",
    "sex": "male|female",
    "occupation": "...",
    "social_history": "...",
    "presenting_complaint": "...",
    "duration": "...",
    "exam_findings": "...",
    "prior_treatment": "...",
    "comorbidities": [
      "..."
    ]
  },
  "distractors": [
    "...",
    "..."
  ],
  "ntep_correct_actions": [
    "..."
  ],
  "who_correct_actions": [
    "..."
  ],
  "us_correct_actions": [
    "..."
  ],
  "critical_error_conditions": [
    "..."
  ],
  "expected_divergence_points": [
    "..."
  ],
  "holdout": false,
  "provenance": {
    "generator_model": "<see manifest -- claude-code mode>",
    "generated_at": "<ISO 8601 UTC timestamp at the time you write this file>",
    "source_divergence_ids": [
      "DIV-010",
      "DIV-016"
    ],
    "critique_passes": 0,
    "human_reviewed": false,
    "clinician_reviewed": false
  }
}
```

Then re-run `python scripts/generate_vignettes.py --mode=claude-code` to
validate this file against the schema and fold it into the run manifest.
