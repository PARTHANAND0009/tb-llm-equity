# Vignette generation prompt -- STRAT-086 -> VIG-086

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `data/vignettes/v1/VIG-086.json`

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

Generate ONE vignette for stratification cell STRAT-086.

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
STRAT-030) on presentation complexity, age band, and number of
distractors — but it must read as a distinct clinical scenario, not the same
stem with a different label.

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: extrapulmonary
- subtype: None
- age_band: adolescent_10_17 (pick a specific age consistent with this band)
- sex: female
- setting: rural (reflect this in social/occupational detail, not a
  place name)
- occupation_class: homemaker
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
    "id": "DIV-003",
    "decision_point": "How is extrapulmonary TB worked up microbiologically when bacteriological confirmation is difficult?",
    "domain": "diagnosis",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "child_0_9",
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP offers upfront NAAT (CBNAAT/TrueNat/LPA) on essentially any accessible extrapulmonary specimen type as the first-line microbiological tool, alongside histopathology, ADA/biochemical testing of body fluids, and imaging (CXR/CT/USG/MRI/PET). Where bacteriological confirmation still cannot be achieved despite these efforts, clinical judgment by an experienced clinician, supported by suggestive laboratory tests, may be used to diagnose EPTB.",
    "ntep_citation": {
      "doc": "Central TB Division, Training Module on Extrapulmonary TB (24-03-2023)",
      "section": "Diagnosis of EPTB / Tools for Microbiological Confirmation of EPTB (p. 26)",
      "url": "https://tbcindia.mohfw.gov.in/wp-content/uploads/2023/05/7702334778Training_Module_on_Extrapulmonary_TB_-_Book_24032023.pdf"
    },
    "who_position": "WHO Module 3's specimen-specific recommendations (Recommendations 6-10) call for Xpert Ultra as the initial diagnostic test, rather than smear microscopy/culture, directly on CSF, pleural fluid, pericardial fluid, synovial fluid, and urine -- the same upfront-NAAT-on-accessible-specimen approach NTEP uses, extended across specimen types rather than confined to pulmonary specimens.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 3: diagnosis (20 Mar 2024)",
      "section": "Recommendations 6-10 (p. 5-6)",
      "url": "https://iris.who.int/server/api/core/bitstreams/b9125fa4-dcc0-418a-9421-56c28275461d/content"
    },
    "us_position": "The 2017 ATS/CDC/IDSA guideline's NAAT recommendation (Recommendation 7) is a general, pulmonary-specimen-focused, conditional/low-quality-evidence recommendation; the guideline does not extend the same upfront-NAAT-first framing to extrapulmonary specimens, and continues to anchor extrapulmonary workup around culture and histology as the reference standard.",
    "us_citation": {
      "doc": "Lewinsohn DM et al., Diagnosis of Tuberculosis in Adults and Children, Clin Infect Dis 2017;64(2):e1-e33",
      "section": "Recommendation 7 (p. e16)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/diagnosis-of-tuberculosis-in-adults-and-children.PDF"
    },
    "consensus_position": "Extrapulmonary specimens (CSF, pleural/pericardial/synovial fluid, urine, and others) get upfront molecular testing as the first-line microbiological tool, not culture/histology-first workup -- NTEP's general EPTB approach and WHO's specimen-specific Xpert Ultra recommendations agree on this.",
    "clinical_stakes": "high",
    "is_critical_error_if_wrong": false,
    "still_diverges_as_of": "2026-08",
    "notes": "Lower-confidence than DIV-001/002: the US citation is not itself extrapulmonary-specific, so us_position is inferred from the 2017 guideline's general (pulmonary) NAAT stance and its silence on extending that framing to EP specimens, rather than from a dedicated EPTB recommendation stating a contrary rule."
  }
]


## Output contract

Write the complete vignette to `data/vignettes/v1/VIG-086.json` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{
  "id": "VIG-086",
  "version": "v1",
  "burden_class": "consensus_control",
  "presentation_type": "extrapulmonary",
  "matched_pair_id": "VIG-030",
  "divergence_ids": [
    "DIV-003"
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
      "DIV-003"
    ],
    "critique_passes": 0,
    "human_reviewed": false,
    "clinician_reviewed": false
  }
}
```

Then re-run `python scripts/generate_vignettes.py --mode=claude-code` to
validate this file against the schema and fold it into the run manifest.
