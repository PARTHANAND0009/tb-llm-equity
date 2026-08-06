# Vignette generation prompt -- STRAT-016 -> VIG-016

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `data/vignettes/v1/VIG-016.json`

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

Generate ONE vignette for stratification cell STRAT-016.

burden_class: india_high — this case represents TB as it presents in a
high-TB-burden population: community/household exposure is plausible and
unremarkable, and the grounding should reflect NTEP program realities
(molecular-first diagnostics where available, weight-band dosing, mandated
program steps like notification/DBT/bidirectional screening where the
grounding rows call for them).

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: pulmonary
- subtype: None
- age_band: older_adult_60_plus (pick a specific age consistent with this band)
- sex: female
- setting: rural (reflect this in social/occupational detail, not a
  place name)
- occupation_class: migrant_worker
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
    "id": "DIV-002",
    "decision_point": "Is rapid molecular rifampicin-resistance testing (DST) performed for every newly diagnosed TB patient, or only for patients meeting specific risk criteria?",
    "domain": "diagnosis",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "child_0_9",
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP defines 'Universal DST' as universal access to rapid drug-resistance testing for at least rifampicin (and further testing for at least fluoroquinolones once RR is detected) for ALL TB patients, preferably before treatment initiation and within a maximum of 15 days of diagnosis -- not contingent on any individual risk factor.",
    "ntep_citation": {
      "doc": "Central TB Division, National Guidelines for Management of Drug Resistant TB (27-3-2025)",
      "section": "Definitions -- 'Universal DST' (p. 19)",
      "url": "https://tbcindia.mohfw.gov.in/wp-content/uploads/2025/03/National-Guidelines-for-Management-of-DR-TB_27-3-2025.pdf"
    },
    "who_position": "WHO Module 3 Recommendation 1 mandates rifampicin-resistance detection as part of the initial test for ALL adults (and Recommendation 2, all children) with signs and symptoms of pulmonary TB -- no risk-factor gate. WHO's own End TB Strategy language explicitly calls for 'universal drug susceptibility testing,' reinforcing this as deliberate global policy rather than an incidental feature of the Xpert recommendation's wording.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 3: diagnosis (20 Mar 2024)",
      "section": "Recommendations 1-2 (p. 5); End TB Strategy reference (p. 1)",
      "url": "https://iris.who.int/server/api/core/bitstreams/b9125fa4-dcc0-418a-9421-56c28275461d/content"
    },
    "us_position": "The 2017 ATS/CDC/IDSA guideline recommends rapid molecular DST for rifampin (with or without isoniazid) only for AFB-smear-positive or NAAT-positive patients who ALSO meet at least one of: prior TB treatment; birth in or >=1 year residence in a country with at least moderate TB incidence (>=20/100,000) or high primary MDR-TB prevalence (>=2%); contact of an MDR-TB patient; or HIV infection -- a risk-targeted approach, not a universal one.",
    "us_citation": {
      "doc": "Lewinsohn DM et al., Diagnosis of Tuberculosis in Adults and Children, Clin Infect Dis 2017;64(2):e1-e33",
      "section": "Rapid molecular drug-susceptibility testing recommendation (p. e3)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/diagnosis-of-tuberculosis-in-adults-and-children.PDF"
    },
    "consensus_position": "Rapid rifampicin-resistance testing is performed on every diagnosed TB patient as a matter of course, not gated on individual risk factors -- both NTEP ('Universal DST') and WHO (Module 3, Recs 1-2) treat this as universal, unconditional practice.",
    "clinical_stakes": "critical",
    "is_critical_error_if_wrong": true,
    "still_diverges_as_of": "2026-08",
    "notes": "A vignette with none of the four US risk criteria present should not have rapid RR-DST as an expected action under the us_correct_actions framing, but should under both ntep_correct_actions and who_correct_actions -- this is exactly the kind of case that discriminates consensus-following from US-default behavior."
  },
  {
    "id": "DIV-004",
    "decision_point": "Is mycobacterial culture a mandatory parallel test for every patient with suspected TB, or reserved for the resistance-detection cascade after a positive molecular test?",
    "domain": "diagnosis",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "child_0_9",
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "In NTEP's standard workflow, culture is reached only as the second step of a cascade after an initial NAAT-positive result (for LPA/liquid culture resistance testing) -- it is not a universally mandated parallel test performed on every presumptive-TB patient regardless of the NAAT result.",
    "ntep_citation": {
      "doc": "NTEP Knowledge Base, \"Principles of TB Diagnosis under NTEP\", Central TB Division",
      "section": "Upfront NAAT cascade description",
      "url": "https://ntep.in/node/394/CP-principles-tb-diagnosis-under-ntep"
    },
    "who_position": "WHO Module 3 Recommendation 1 states Xpert should be used 'rather than smear microscopy/culture and phenotypic DST' as the initial test -- WHO does not mandate parallel culture on every specimen either; culture is reserved for the resistance-detection cascade and specific downstream indications, the same structure NTEP uses.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 3: diagnosis (20 Mar 2024)",
      "section": "Recommendation 1 (p. 5)",
      "url": "https://iris.who.int/server/api/core/bitstreams/b9125fa4-dcc0-418a-9421-56c28275461d/content"
    },
    "us_position": "The 2017 ATS/CDC/IDSA guideline's Recommendation 6 calls for both liquid and solid mycobacterial culture 'for every specimen obtained from an individual with suspected TB disease,' describing culture as the gold-standard microbiologic test regardless of NAAT or smear result.",
    "us_citation": {
      "doc": "Lewinsohn DM et al., Diagnosis of Tuberculosis in Adults and Children, Clin Infect Dis 2017;64(2):e1-e33",
      "section": "Recommendation 6 (p. e16)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/diagnosis-of-tuberculosis-in-adults-and-children.PDF"
    },
    "consensus_position": "Culture is not a mandatory parallel test on every presumptive-TB specimen; it is reserved for the resistance-detection cascade downstream of an initial molecular result -- both NTEP and WHO structure the workflow this way.",
    "clinical_stakes": "moderate",
    "is_critical_error_if_wrong": false,
    "still_diverges_as_of": "2026-08"
  },
  {
    "id": "DIV-006",
    "decision_point": "Is the first-line drug-sensitive TB regimen given daily throughout treatment, or can the continuation phase use intermittent (thrice- or twice-weekly) dosing?",
    "domain": "treatment",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP's stated principle (except for confirmed DR-TB) is to administer daily fixed-dose combination first-line ATT in appropriate weight bands under direct observation, for both the intensive phase (2HRZE) and continuation phase (4HRE) -- there is no programmatic intermittent-dosing option for drug-sensitive TB.",
    "ntep_citation": {
      "doc": "ICMR/Dept. of Health Research (MoHFW), Standard Treatment Workflow: Drug Sensitive-TB Treatment as per NTEP (March 2022)",
      "section": "Regimen for Drug-Sensitive TB cases: 2HRZE/4HRE",
      "url": "https://www.icmr.gov.in/icmrobject/uploads/STWs/1725964686_2_ntep_18032022.pdf"
    },
    "who_position": "WHO Module 4 Recommendation 1.2: daily dosing throughout the course of therapy is the optimal frequency, wherever feasible (strong recommendation, high certainty). Recommendation 1.3: the use of thrice-weekly dosing 'is not recommended in both the intensive and continuation phases of therapy, and daily dosing remains the recommended dosing frequency' (conditional recommendation, very low certainty).",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 4: treatment and care (15 Apr 2025)",
      "section": "Recommendations 1.2 and 1.3 (p. 4)",
      "url": "https://iris.who.int/server/api/core/bitstreams/f663f086-5d97-4355-beea-0635d47f1227/content"
    },
    "us_position": "The 2016 ATS/CDC/IDSA guideline strongly recommends daily intensive-phase dosing (Recommendation 3a), but conditionally permits thrice-weekly (Recommendation 3b) or, when DOT is difficult, twice-weekly (Recommendation 3c) dosing in the continuation phase for patients who are HIV-negative and at low relapse risk (noncavitary and/or smear-negative disease).",
    "us_citation": {
      "doc": "Nahid P et al., Official ATS/CDC/IDSA Clinical Practice Guidelines: Treatment of Drug-Susceptible Tuberculosis, Clin Infect Dis 2016;63(7):e147-e195",
      "section": "Recommendations 3a, 3b, 3c (p. 6)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/treatment-of-drug-susceptible-tuberculosis.pdf"
    },
    "consensus_position": "Drug-susceptible TB treatment is daily throughout, intensive and continuation phase alike -- neither NTEP nor WHO offers an intermittent-dosing option; WHO's 2025 update explicitly recommends against thrice-weekly dosing in either phase.",
    "clinical_stakes": "high",
    "is_critical_error_if_wrong": true,
    "still_diverges_as_of": "2026-08",
    "notes": "A vignette should not accept an intermittent continuation-phase regimen as consensus-correct -- it is a us_correct_actions-only option, and only for low-relapse-risk, HIV-negative patients even there. Scoped to adult age bands: the cited NTEP/US documents are both adult-focused DS-TB treatment workflows."
  }
]


## Output contract

Write the complete vignette to `data/vignettes/v1/VIG-016.json` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{
  "id": "VIG-016",
  "version": "v1",
  "burden_class": "india_high",
  "presentation_type": "pulmonary",
  "matched_pair_id": null,
  "divergence_ids": [
    "DIV-002",
    "DIV-004",
    "DIV-006"
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
      "DIV-002",
      "DIV-004",
      "DIV-006"
    ],
    "critique_passes": 0,
    "human_reviewed": false,
    "clinician_reviewed": false
  }
}
```

Then re-run `python scripts/generate_vignettes.py --mode=claude-code` to
validate this file against the schema and fold it into the run manifest.
