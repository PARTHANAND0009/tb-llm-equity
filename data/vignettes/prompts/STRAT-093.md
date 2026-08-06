# Vignette generation prompt -- STRAT-093 -> VIG-093

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `data/vignettes/v1/VIG-093.json`

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

Generate ONE vignette for stratification cell STRAT-093.

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
STRAT-045) on presentation complexity, age band, and number of
distractors — but it must read as a distinct clinical scenario, not the same
stem with a different label.

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: comorbid
- subtype: tb_hiv
- age_band: child_0_9 (pick a specific age consistent with this band)
- sex: male
- setting: urban (reflect this in social/occupational detail, not a
  place name)
- occupation_class: healthcare_worker
- comorbidity_burden: significant
- symptom_duration_band: 2_4_weeks
- num_distractors: exactly 2

Ground the case in these divergence-table rows (cite the reasoning that
follows from them in ntep_correct_actions / who_correct_actions /
us_correct_actions / expected_divergence_points — do not introduce clinical
content unrelated to these rows; note each row's divergence_class, per the
instructions above on when ntep/who must share verbatim overlapping text):

[
  {
    "id": "DIV-019",
    "decision_point": "Is cotrimoxazole preventive therapy (CPT) given to all people living with HIV who have active TB, regardless of CD4 count?",
    "domain": "comorbidity",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": [
      "child_0_9",
      "adolescent_10_17",
      "adult_18_59",
      "older_adult_60_plus"
    ],
    "ntep_position": "NTEP's differentiated-care intake documentation tracks CPT status as a standard field for every HIV-reactive TB patient (alongside ART status), and NTEP's TPT addendum lists a cotrimoxazole-containing fixed-dose formulation as 'a preferred formulation in PLHIV' without conditioning it on a CD4 threshold -- consistent with the WHO position of universal CPT for all HIV-positive TB patients regardless of CD4 count.",
    "ntep_citation": {
      "doc": "Central TB Division, National Guidance on Differentiated TB Care (March 2025); 1HP TPT addendum (Dec 2024)",
      "section": "Differentiated Care intake form, comorbidity/HIV section (p. 86); 1HP addendum dosage footnote (p. 2)",
      "url": "https://tbcindia.mohfw.gov.in/wp-content/uploads/2025/07/National-Guidance-on-Differential-TB-Care_Final_March-2025-3.pdf"
    },
    "who_position": "WHO's long-standing policy (referenced directly within the US guideline itself, see us_citation) recommends cotrimoxazole for ALL HIV-infected people with active TB, regardless of CD4 count -- a universal, unconditional recommendation not gated on immune status.",
    "who_citation": {
      "doc": "WHO policy on collaborative TB/HIV activities, as quoted in Nahid P et al. 2016 (no dedicated WHO consolidated-guidelines module on CPT was fetched this session -- this WHO position is sourced via the US guideline's own explicit citation of it, not an independently read WHO primary document)",
      "section": "Quoted in: Nahid P et al., Treatment of Drug-Susceptible Tuberculosis, Clin Infect Dis 2016;63(7):e147-e195, HIV/TB co-treatment discussion (p. 11)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/treatment-of-drug-susceptible-tuberculosis.pdf"
    },
    "us_position": "The 2016 ATS/CDC/IDSA guideline states explicitly that although WHO recommends cotrimoxazole for all HIV-infected people with active TB regardless of CD4 count, 'in high-income countries, co-trimoxazole is primarily used in HIV-infected patients with CD4 counts <200 cells/uL' -- a materially narrower, CD4-gated indication.",
    "us_citation": {
      "doc": "Nahid P et al., Treatment of Drug-Susceptible Tuberculosis, Clin Infect Dis 2016;63(7):e147-e195",
      "section": "HIV/TB co-treatment discussion (p. 11)",
      "url": "https://www.thoracic.org/statements/resources/tb-opi/treatment-of-drug-susceptible-tuberculosis.pdf"
    },
    "consensus_position": "Cotrimoxazole preventive therapy is given to all HIV-positive TB patients regardless of CD4 count, not gated on immune status -- WHO's universal position and NTEP's CD4-unconditioned practice agree.",
    "clinical_stakes": "high",
    "is_critical_error_if_wrong": false,
    "still_diverges_as_of": "2026-08",
    "notes": "Unusual but strong citation structure: the WHO-vs-high-income-country contrast is stated explicitly within the US source itself, making the divergence highly legible even though who_citation is a secondary quotation rather than a directly-read WHO primary document. Flagged so a future session can replace this with a direct WHO/UNAIDS primary-source citation if one is fetched."
  },
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
  }
]


## Output contract

Write the complete vignette to `data/vignettes/v1/VIG-093.json` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{
  "id": "VIG-093",
  "version": "v1",
  "burden_class": "consensus_control",
  "presentation_type": "comorbid",
  "matched_pair_id": "VIG-045",
  "divergence_ids": [
    "DIV-019",
    "DIV-002"
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
      "DIV-019",
      "DIV-002"
    ],
    "critique_passes": 0,
    "human_reviewed": false,
    "clinician_reviewed": false
  }
}
```

Then re-run `python scripts/generate_vignettes.py --mode=claude-code` to
validate this file against the schema and fold it into the run manifest.
