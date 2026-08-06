# Vignette generation prompt -- STRAT-098 -> VIG-098

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `data/vignettes/v1/VIG-098.json`

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

Generate ONE vignette for stratification cell STRAT-098.

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
STRAT-066) on presentation complexity, age band, and number of
distractors — but it must read as a distinct clinical scenario, not the same
stem with a different label.

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: contact_management
- subtype: plhiv_tpt
- age_band: adolescent_10_17 (pick a specific age consistent with this band)
- sex: female
- setting: rural (reflect this in social/occupational detail, not a
  place name)
- occupation_class: agricultural_worker
- comorbidity_burden: mild
- symptom_duration_band: 4_8_weeks
- num_distractors: exactly 3

Ground the case in these divergence-table rows (cite the reasoning that
follows from them in ntep_correct_actions / who_correct_actions /
us_correct_actions / expected_divergence_points — do not introduce clinical
content unrelated to these rows; note each row's divergence_class, per the
instructions above on when ntep/who must share verbatim overlapping text):

[
  {
    "id": "DIV-017",
    "decision_point": "Is there a standardized, quantified, threshold-based national triage protocol that mandates referral to a higher-level facility when specific vital-sign/lab red flags are met, or is decentralization pursued as a general policy direction without a codified triage threshold?",
    "domain": "monitoring",
    "divergence_class": "national_adaptation",
    "applicable_age_bands": [
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP's Differentiated TB Care framework specifies explicit, quantified red-flag criteria (e.g., SpO2 <94%, respiratory rate >24/min, systolic BP <90 or >140 mmHg, random blood glucose >=200 mg/dl with symptoms or HbA1c >=6.5%, BMI <14 kg/m2, CD4 <100 cells/uL) that mandate escalation/referral to a higher-tier facility as a mandatory activity.",
    "ntep_citation": {
      "doc": "Central TB Division, National Guidance on Differentiated TB Care (March 2025)",
      "section": "Box 4.3, Differentiated TB Care Evaluation, Triaging & Management (p. 19)",
      "url": "https://tbcindia.mohfw.gov.in/wp-content/uploads/2025/07/National-Guidance-on-Differential-TB-Care_Final_March-2025-3.pdf"
    },
    "who_position": "WHO Module 4 recommends the general direction of decentralization -- ambulatory rather than hospital-based care for MDR-TB (Recommendation 2.1, conditional, very low certainty), a decentralized model of care over a centralized one (Recommendation 2.2, conditional, very low certainty), and decentralized models for children/adolescents in high-burden settings (Recommendation 3.1, conditional, very low certainty) -- but none of these recommendations specify a quantified vital-sign or laboratory threshold for who is safe to manage at a decentralized/lower-tier facility versus who must be escalated.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 4: treatment and care (15 Apr 2025)",
      "section": "Recommendations 2.1, 2.2, 3.1 (p. 178-179)",
      "url": "https://iris.who.int/server/api/core/bitstreams/f663f086-5d97-4355-beea-0635d47f1227/content"
    },
    "us_position": "The 2016 ATS/CDC/IDSA guideline discusses baseline evaluation and monitoring for adverse effects and treatment response, but leaves hospitalization/referral decisions to individualized clinical judgment rather than a codified, quantified, nationally standardized threshold-based triage protocol -- structurally similar to WHO's lack of a specified threshold, though for a different reason (individualized judgment vs. general policy direction).",
    "us_citation": {
      "doc": "Nahid P et al., Treatment of Drug-Susceptible Tuberculosis, Clin Infect Dis 2016;63(7):e147-e195",
      "section": "Recommended baseline and follow-up evaluations discussion (p. 7)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/treatment-of-drug-susceptible-tuberculosis.pdf"
    },
    "consensus_position": null,
    "clinical_stakes": "high",
    "is_critical_error_if_wrong": false,
    "still_diverges_as_of": "2026-08",
    "notes": "national_adaptation: WHO and NTEP genuinely differ on specificity here, so there is no consensus_position. Notably, WHO and the US guideline land in a similar place (neither specifies a quantified threshold), which makes NTEP the outlier on this particular row rather than the US -- worth keeping distinct from the consensus_divergence rows where the pattern runs the other way. Excludes child_0_9: NTEP's cited thresholds use adult-calibrated ranges."
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

Write the complete vignette to `data/vignettes/v1/VIG-098.json` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{
  "id": "VIG-098",
  "version": "v1",
  "burden_class": "consensus_control",
  "presentation_type": "contact_management",
  "matched_pair_id": "VIG-066",
  "divergence_ids": [
    "DIV-017",
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
      "DIV-017",
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
