# Divergence table — WHO comparator (rebuilt 2026-08-06)

`divergence_table.json` (6 rows, `DIV-008`, `DIV-010`, `DIV-016`, `DIV-017`,
`DIV-020`, `DIV-021` — non-contiguous IDs are intentional, see below) compares
NTEP against the **WHO consolidated guidelines on tuberculosis**, not a US
("Western") guideline. This replaces the 2026-08-05 table, which used
ATS/CDC/IDSA as the comparator. See:

- `data/protocols/FETCH_LOG.md` — every fetch attempt, success and failure,
  with URLs and what each source was used for.
- `SUMMARY.md` — composition stats, why the comparator changed, and the
  6 surviving rows.
- `UNVERIFIED.md` — every one of the original 19 rows' disposition (11
  converged with WHO, 5 dropped as absence claims), plus the 2 new rows'
  provenance and candidates checked and found convergent.

## Why the row IDs have gaps

Rows that converged with WHO or were dropped as absence claims keep their
original `DIV-0NN` ID in `UNVERIFIED.md` rather than being renumbered, so a
reader can trace any ID back to its disposition. The surviving/reinstated
rows (DIV-008, DIV-010, DIV-016, DIV-017) also kept their original IDs for
the same reason. The two new rows continue the sequence as DIV-020/DIV-021.

## Why only 6 rows

Every axis Task 1 named as a likely source of new divergence — universal DST
scope/timing, weight-band FDC dosing, contact TPT eligibility breadth,
differentiated/decentralized care, DR-TB regimen choice — was checked
against a WHO primary source actually fetched this session, and most of
them converged. That is reported honestly rather than padded: see
`SUMMARY.md`'s "What converged" section for the full list with citations.
Fewer, fully defensible rows was the explicit instruction over a padded
table.

**Before this table is treated as fully ground truth for vignette
generation or scoring**, it still needs clinician sign-off — primary-source
citation rules out the "drafted from memory" failure mode, but citation
accuracy is not the same as clinical accuracy, and a domain expert should
still review every row. Two rows (DIV-020, DIV-021) carry an explicit
in-table caveat that their NTEP-side citation may already be out of date
(NTEP may have adopted the WHO position in a document not yet found) — these
should be re-verified before reuse in a future vignette-generation run.

Until clinician review happens, do not bump any vignette or rubric version
that depends on this table being correct — see `RUBRIC_VERSION` in
`src/tb_equity/rubric.py` and RULE 2 in `CLAUDE.md`.
