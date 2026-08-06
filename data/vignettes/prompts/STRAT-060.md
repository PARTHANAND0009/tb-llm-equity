# Vignette generation prompt -- STRAT-060 -> VIG-060

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `data/vignettes/v1/VIG-060.json`

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

Generate ONE vignette for stratification cell STRAT-060.

burden_class: india_high — this case represents TB as it presents in a
high-TB-burden population: community/household exposure is plausible and
unremarkable, and the grounding should reflect NTEP program realities
(molecular-first diagnostics where available, weight-band dosing, mandated
program steps like notification/DBT/bidirectional screening where the
grounding rows call for them).

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: drug_resistant
- subtype: pre_xdr_tb
- age_band: older_adult_60_plus (pick a specific age consistent with this band)
- sex: female
- setting: rural (reflect this in social/occupational detail, not a
  place name)
- occupation_class: factory_or_industrial_worker
- comorbidity_burden: significant
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
    "id": "DIV-009",
    "decision_point": "For a household/close contact of a patient with fluoroquinolone-susceptible MDR/RR-TB, is a fixed standardized preventive regimen given, or is treatment itself only conditionally recommended with an individualized regimen if given?",
    "domain": "resistance",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "child_0_9",
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP's 2024 TPT addendum specifies a fixed, standardized preventive regimen for household contacts of drug-resistant index cases: 6 months of daily levofloxacin (6Lfx) for contacts of fluoroquinolone-susceptible MDR-TB, or 4 months of daily rifampicin (4R) for contacts of isoniazid mono/poly-resistant TB -- offered as a routine part of programmatic TPT.",
    "ntep_citation": {
      "doc": "Central TB Division, Guidance document on 1HP TPT regimen (addendum to the 2021 PMTPT guidelines, Dec 2024)",
      "section": "TPT target group, strategy, and treatment options table (p. 1-2)",
      "url": "https://tbcindia.nikshay.in/wp-content/uploads/2024/12/Technical-and-Operational-Guidance-on-1HP-TPT-regimen_addendum-to-National-PMTPT-guidelines.pdf"
    },
    "who_position": "WHO Module 1 Recommendation 21 (new in the 2024 edition, based on the pooled V-QUIN/TB-CHAMP trials): 'In contacts exposed to multidrug- or rifampicin-resistant tuberculosis, 6 months of daily levofloxacin should be used as TB preventive treatment' (strong recommendation, moderate certainty) -- a fixed, standardized regimen, not merely a conditional recommendation to treat at all.",
    "who_citation": {
      "doc": "WHO consolidated guidelines on tuberculosis, Module 1: prevention, 2nd ed (9 Sep 2024)",
      "section": "Recommendation 21 (p. 27)",
      "url": "https://iris.who.int/server/api/core/bitstreams/314ddea2-6fc2-4ff0-9357-a038feca1d31/content"
    },
    "us_position": "The 2019 ATS/CDC/ERS/IDSA guideline only conditionally recommends offering LTBI treatment to MDR-TB contacts at all, versus observation alone ('conditional recommendation, very low certainty in the evidence') -- and if treatment is given, the regimen and duration (6-12 months of a later-generation fluoroquinolone alone or with a second drug) are individualized to the source case's susceptibility pattern rather than fixed.",
    "us_citation": {
      "doc": "Nahid P et al., Treatment of Drug-Resistant Tuberculosis: An Official ATS/CDC/ERS/IDSA Clinical Practice Guideline, Am J Respir Crit Care Med 2019;200(10):e93-e142",
      "section": "MDR-TB contact management recommendation",
      "url": "https://academic.oup.com/ajrccm/article/200/10/e93/8497038"
    },
    "consensus_position": "Household/close contacts of fluoroquinolone-susceptible MDR/RR-TB receive a fixed, standardized 6-month daily levofloxacin regimen as routine preventive treatment, not an individualized regimen contingent on a conditional decision to treat -- NTEP's 2024 addendum and WHO's 2024 Recommendation 21 now agree on this exactly (WHO's update supersedes the older, more discretionary 2018 WHO position this row was originally checked against).",
    "clinical_stakes": "critical",
    "is_critical_error_if_wrong": true,
    "still_diverges_as_of": "2026-08",
    "notes": "US citation fetched via WebFetch against the journal page rather than a locally archived PDF (thoracic.org's direct PDF link 404'd/redirected -- see FETCH_LOG.md); no newer (2025) US-side update specific to MDR-TB contact TPT was found (the 2025 ATS/CDC/ERS/IDSA update located this session addressed active MDR-TB treatment regimen choice, not contact preventive therapy -- see UNVERIFIED.md), so the 2019 citation is the most current available. A vignette should not treat 'observation only, no preventive treatment' as consensus-correct."
  }
]


## Output contract

Write the complete vignette to `data/vignettes/v1/VIG-060.json` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{
  "id": "VIG-060",
  "version": "v1",
  "burden_class": "india_high",
  "presentation_type": "drug_resistant",
  "matched_pair_id": null,
  "divergence_ids": [
    "DIV-002",
    "DIV-009"
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
      "DIV-009"
    ],
    "critique_passes": 0,
    "human_reviewed": false,
    "clinician_reviewed": false
  }
}
```

Then re-run `python scripts/generate_vignettes.py --mode=claude-code` to
validate this file against the schema and fold it into the run manifest.
