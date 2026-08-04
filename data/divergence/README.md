# Divergence table — DRAFT, UNVERIFIED

`divergence_table.json` (24 rows, `DIV-001`..`DIV-024`) is a **first-pass draft** written from
training-data knowledge of NTEP (India National TB Elimination Programme), WHO, and CDC/ATS/IDSA
guidance — **not** extracted from source documents, because `data/protocols/` is currently empty.

Before this table is treated as ground truth for vignette generation or scoring:

1. Add the actual primary sources to `data/protocols/` (NTEP training/operational guidelines, WHO
   consolidated TB guidelines, CDC/ATS/IDSA guidelines) and re-derive/verify each row against them.
2. Get clinician sign-off on every row, not just the ones flagged `confidence: low`.
3. Pay particular attention to rows tagged `"note": "possible_convergence"` — these are flagged as
   likely *not* real discriminators (NTEP and Western guidance may actually agree), included
   deliberately as test cases for the Step 3 adversarial critique pass rather than as solid grounding.

Until that review happens, do not bump any vignette or rubric version that depends on this table
being correct — see `RUBRIC_VERSION` in `src/tb_equity/rubric.py` and RULE 2 in `CLAUDE.md`.
