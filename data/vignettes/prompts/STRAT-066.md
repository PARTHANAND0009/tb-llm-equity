# Vignette generation prompt -- STRAT-066 -> VIG-066

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `data/vignettes/v1/VIG-066.json`

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

Generate ONE vignette for stratification cell STRAT-066.

burden_class: india_high — this case represents TB as it presents in a
high-TB-burden population: community/household exposure is plausible and
unremarkable, and the grounding should reflect NTEP program realities
(molecular-first diagnostics where available, weight-band dosing, mandated
program steps like notification/DBT/bidirectional screening where the
grounding rows call for them).

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: contact_management
- subtype: household_contact_ds_tb
- age_band: adolescent_10_17 (pick a specific age consistent with this band)
- sex: female
- setting: rural (reflect this in social/occupational detail, not a
  place name)
- occupation_class: agricultural_worker
- comorbidity_burden: significant
- symptom_duration_band: 4_8_weeks
- num_distractors: exactly 3

Ground the case in these divergence-table rows (cite the reasoning that
follows from them in ntep_correct_actions / who_correct_actions /
us_correct_actions / expected_divergence_points — do not introduce clinical
content unrelated to these rows; note each row's divergence_class, per the
instructions above on when ntep/who must share verbatim overlapping text):

[
  {
    "id": "DIV-005",
    "decision_point": "For diagnosing TB infection (TBI/LTBI), is IGRA preferred over TST when the person has a history of BCG vaccination?",
    "domain": "diagnosis",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "child_0_9",
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP treats TST and IGRA as interchangeable options for TBI testing, to be offered 'wherever available' -- TPT eligibility and initiation are not gated on which test is used, or on using either test at all, for the highest-priority groups (see DIV-010/011).",
    "ntep_citation": {
      "doc": "Central TB Division, Guidelines for Programmatic Management of Tuberculosis Preventive Treatment in India (2021)",
      "section": "3.3.1 Tuberculin Skin Test / 3.3.2 Interferon-Gamma Release Assay (p. 10)",
      "url": "https://tbcindia.mohfw.gov.in/wp-content/uploads/2023/05/Guidelines-for-Programmatic-Management-of-Tuberculosis-Preventive-Treatment-in-India.pdf"
    },
    "who_position": "WHO Module 1 Recommendation 17: 'Either a TST or an IGRA can be used to test for TB infection' (strong recommendation), with the accompanying GDG discussion stating explicitly that 'a history of BCG vaccination has a limited effect on interpretation of TST results later in life; hence, BCG vaccination should not be a determining factor in selecting a test.'",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 1: prevention, 2nd ed (9 Sep 2024)",
      "section": "Recommendation 17 (p. 19-20); GDG discussion on BCG and TST specificity (p. 138, Annex 4)",
      "url": "https://iris.who.int/server/api/core/bitstreams/314ddea2-6fc2-4ff0-9357-a038feca1d31/content"
    },
    "us_position": "The 2017 ATS/CDC/IDSA guideline's Recommendation 1a explicitly recommends IGRA rather than TST for individuals with a history of BCG vaccination (strong recommendation, moderate-quality evidence), precisely because BCG vaccination confounds TST interpretation.",
    "us_citation": {
      "doc": "Lewinsohn DM et al., Diagnosis of Tuberculosis in Adults and Children, Clin Infect Dis 2017;64(2):e1-e33",
      "section": "Recommendation 1a (p. e11)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/diagnosis-of-tuberculosis-in-adults-and-children.PDF"
    },
    "consensus_position": "TST and IGRA are equivalent options for TBI testing regardless of BCG vaccination history -- BCG history should not determine which test is chosen. Both NTEP and WHO hold this position explicitly.",
    "clinical_stakes": "moderate",
    "is_critical_error_if_wrong": false,
    "still_diverges_as_of": "2026-08"
  },
  {
    "id": "DIV-012",
    "decision_point": "Is the 1-month daily rifapentine-isoniazid (1HP) regimen a programmatically available TPT option?",
    "domain": "prevention",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "As of a December 2024 addendum, NTEP has formally adopted 1HP (28 daily doses of isoniazid + rifapentine) as a TPT option for persons aged >=13 years, including PLHIV, household contacts of drug-sensitive TB, and other expanded risk groups.",
    "ntep_citation": {
      "doc": "Central TB Division, Guidance document on shorter one-month daily isoniazid and rifapentine (1HP) TPT regimen (Dec 2024)",
      "section": "Full document (4 pages)",
      "url": "https://tbcindia.nikshay.in/wp-content/uploads/2024/12/Technical-and-Operational-Guidance-on-1HP-TPT-regimen_addendum-to-National-PMTPT-guidelines.pdf"
    },
    "who_position": "WHO Module 1 Recommendation 20: 'a 1-month regimen of daily rifapentine plus isoniazid' (1HP) 'may be used' as an alternative TPT option regardless of HIV status (conditional recommendation, low-to-moderate certainty) -- already WHO policy since the 2020 guideline update, predating NTEP's own Dec 2024 addendum by four years.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 1: prevention (9 Sep 2024)",
      "section": "Recommendation 20 (p. 21)",
      "url": "https://iris.who.int/server/api/core/bitstreams/314ddea2-6fc2-4ff0-9357-a038feca1d31/content"
    },
    "us_position": "The CDC/NTCA 2020 guideline -- the standing US regimen guideline -- cites the same underlying 1HP evidence (the BRIEF-TB/A5279 trial) only in its bibliography and does not list 1HP among its recommended/preferred/alternative regimens.",
    "us_citation": {
      "doc": "Guidelines for the Treatment of Latent Tuberculosis Infection: Recommendations from NTCA and CDC, 2020, MMWR Recomm Rep 2020;69(1):1-11",
      "section": "References (1HP trial cited as background evidence only, not as a listed regimen)",
      "url": "https://www.cdc.gov/mmwr/volumes/69/rr/pdfs/rr6901a1-H.pdf"
    },
    "consensus_position": "1HP (1-month daily rifapentine plus isoniazid) is an available TPT regimen option -- WHO has recommended it since 2020, and NTEP formally adopted it in Dec 2024; both currently list it as a usable regimen, while the standing US guideline does not.",
    "clinical_stakes": "moderate",
    "is_critical_error_if_wrong": false,
    "still_diverges_as_of": "2026-08",
    "notes": "A 'not yet adopted' style divergence that could close if CDC issues an updated regimen guideline -- re-verify before reuse in a future vignette-generation run. Scoped to adolescent_10_17 and above per NTEP's own stated >=13-year eligibility; excluded from child_0_9 given this repo's band granularity."
  }
]


## Output contract

Write the complete vignette to `data/vignettes/v1/VIG-066.json` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{
  "id": "VIG-066",
  "version": "v1",
  "burden_class": "india_high",
  "presentation_type": "contact_management",
  "matched_pair_id": "VIG-098",
  "divergence_ids": [
    "DIV-005",
    "DIV-012"
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
      "DIV-005",
      "DIV-012"
    ],
    "critique_passes": 0,
    "human_reviewed": false,
    "clinician_reviewed": false
  }
}
```

Then re-run `python scripts/generate_vignettes.py --mode=claude-code` to
validate this file against the schema and fold it into the run manifest.
