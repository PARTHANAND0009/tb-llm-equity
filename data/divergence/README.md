# Divergence table — three-way NTEP / WHO / US structure (2026-08-06)

`divergence_table.json` (17 rows) now carries three positions per row —
`ntep_position`, `who_position`, `us_position` — plus `divergence_class`
(`consensus_divergence` when NTEP and WHO agree and only the US differs;
`national_adaptation` when NTEP differs from WHO) and, for
`consensus_divergence` rows, a `consensus_position` synthesizing what NTEP
and WHO jointly hold. This replaces the same-day, two-way (NTEP vs. WHO)
version of this table.

## Why a third position

The two-way (NTEP vs. WHO) rebuild found that 11 of the original 19 rows
converged: NTEP and WHO agree on universal DST, contact TPT breadth, 1HP
adoption, MDR contact regimens, and empiric TPT for PLHIV/under-5s, among
others. Dropping those rows would have thrown away the actual finding: NTEP
tracks international consensus closely, and it's the still-current
2016/2017 ATS/CDC/IDSA guidance that has fallen behind. Re-adding the
original US citation to each of those 11 rows turns "NTEP and WHO agree" (a
dead end for a two-way table) into "does a model follow consensus or
default to US practice" (a live, testable question) — see:

- `data/protocols/FETCH_LOG.md` — every fetch attempt, success and failure.
- `SUMMARY.md` — composition stats, the reframed research question, and the
  highest-stakes rows in each `divergence_class`.
- `UNVERIFIED.md` — full disposition history: which rows converged and were
  reinstated, which remain dropped as absence claims, and why.

## Row IDs

Non-contiguous IDs (DIV-001 through DIV-012, then DIV-016, 017, 019, 020,
021) are intentional — every ID traces back through this table's several
rebuilds, and a reader can look up any ID's full history in `UNVERIFIED.md`.
DIV-013, 014, 015, and 018 remain dropped as absence claims (no WHO or US
position exists to cite on the relevant axis) and do not appear in the live
table.

## Using divergence_class

- **`consensus_divergence`** (11 rows) is the **primary dataset**: score
  responses against `consensus_correct_actions` (NTEP ∩ WHO) as the primary
  outcome, and separately check `us_correct_actions` alignment to test the
  US-default hypothesis directly.
- **`national_adaptation`** (6 rows) is **secondary**: NTEP and WHO
  genuinely differ here, so there is no consensus to score against —
  `consensus_position` is `null` by design for these rows. Use
  `ntep_correct_actions` vs `who_correct_actions` the way the table's
  original two-way design intended.

**Before this table is treated as fully ground truth for vignette
generation or scoring**, it still needs clinician sign-off — primary-source
citation rules out the "drafted from memory" failure mode, but citation
accuracy is not the same as clinical accuracy. Several rows carry an
explicit lower-confidence flag in their own `notes` field (DIV-003, DIV-008,
DIV-009's US-side currency, DIV-011, DIV-019's WHO citation being a
secondary quotation, DIV-020, DIV-021) — read those before treating a row as
unqualified ground truth.

Until clinician review happens, do not bump any vignette or rubric version
that depends on this table being correct — see `RUBRIC_VERSION` in
`src/tb_equity/rubric.py` and RULE 2 in `CLAUDE.md`.
