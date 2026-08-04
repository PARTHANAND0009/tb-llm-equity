# Divergence table — rebuilt from primary sources (2026-08-05)

`divergence_table.json` (19 rows, `DIV-001`..`DIV-019`) was rebuilt from primary
source documents actually fetched and read in `data/protocols/` — replacing
the earlier training-knowledge draft. See:

- `data/protocols/FETCH_LOG.md` — every fetch attempt, success and failure, with
  URLs and what each source was used for.
- `SUMMARY.md` — composition stats and the 10 highest-stakes verified rows.
- `UNVERIFIED.md` — confirmed convergences dropped from the table, and candidate
  rows that didn't get a citation on both sides and so were left out.

**Before this table is treated as fully ground truth for vignette generation or
scoring**, it still needs clinician sign-off — primary-source citation rules out
the "drafted from memory" failure mode, but citation accuracy is not the same
as clinical accuracy, and a domain expert should still review every row.

19 rows falls short of the 40-60 target given in the original task; `UNVERIFIED.md`
explains why (citation rigor over row count) and lists the priority fetches for
extending the table in a follow-up session.

Until clinician review happens, do not bump any vignette or rubric version that
depends on this table being correct — see `RUBRIC_VERSION` in `src/tb_equity/rubric.py`
and RULE 2 in `CLAUDE.md`.
