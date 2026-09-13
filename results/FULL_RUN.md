# IRIS TMED — full run

3-model panel (meta, mistral, qwen), n=1 (greedy decoding), free-form (all non-holdout vignettes) + structured (subset grounding a structured_elicitation.py axis) arms. RUBRIC_VERSION frozen; instrument freeze 2026-09-20 respected.

## Excluded from this panel

**Granite (`ibm`)** -- OOM'd during model loading (before any generation) in the Checkpoint 2b-v Step E re-pilot; dropped without retry per explicit instruction.

**Meditron3-8B (`epfl`)** -- never run at all; dropped ahead of time to protect the 20 September freeze deadline after repeated Colab free-tier quota exhaustion/disconnects during this run's generation, not due to any epfl-specific failure. Notably, both excluded models were the panel's continued-pretrained-on-medical-text entries -- the final panel below is general-purpose instruction-tuned models only.

See `results/LIMITATIONS.md` for the full writeup of both exclusions, including what remains unanswered for each.

## Flags (checked automatically -- read this before anything else)

- **FLAG:** meta (freeform) addressed only 5/181 (2.8%) axis instances across ALL axes -- near-zero commitment, flagged per explicit instruction.
- **FLAG:** mistral (freeform) addressed only 1/181 (0.6%) axis instances across ALL axes -- near-zero commitment, flagged per explicit instruction.

## Conditional alignment per axis per model (PRIMARY result)

Among responses that commit to a divergence axis at all (label != not_addressed), the ntep/who/us/consensus/hedged split. 95% CI via the Wilson score interval (chosen over the normal/Wald approximation for stable behavior near 0%/100%, which per-axis rates on a modest n frequently are -- see `src/tb_equity/analysis.py::wilson_interval`). Per-axis n is stated explicitly because live-axis counts differ by row.

### structured

| model | axis | class | total n | addressed n | coverage | label | rate | 95% CI |
|---|---|---|---|---|---|---|---|---|
| meta | DIV-001 | consensus_divergence | 14 | 3 | 21.4% | us | 100.0% | [43.8%, 100.0%] |
| meta | DIV-002 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-004 | consensus_divergence | 20 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-006 | consensus_divergence | 8 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-007 | consensus_divergence | 26 | 23 | 88.5% | us | 100.0% | [85.7%, 100.0%] |
| meta | DIV-009 | consensus_divergence | 7 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-019 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-001 | consensus_divergence | 14 | 7 | 50.0% | consensus | 14.3% | [2.6%, 51.3%] |
| mistral | DIV-001 | consensus_divergence | 14 | 7 | 50.0% | hedged | 28.6% | [8.2%, 64.1%] |
| mistral | DIV-001 | consensus_divergence | 14 | 7 | 50.0% | us | 57.1% | [25.0%, 84.2%] |
| mistral | DIV-002 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-004 | consensus_divergence | 20 | 1 | 5.0% | us | 100.0% | [20.7%, 100.0%] |
| mistral | DIV-006 | consensus_divergence | 8 | 2 | 25.0% | us | 100.0% | [34.2%, 100.0%] |
| mistral | DIV-007 | consensus_divergence | 26 | 25 | 96.2% | consensus | 12.0% | [4.2%, 30.0%] |
| mistral | DIV-007 | consensus_divergence | 26 | 25 | 96.2% | hedged | 40.0% | [23.4%, 59.3%] |
| mistral | DIV-007 | consensus_divergence | 26 | 25 | 96.2% | us | 48.0% | [30.0%, 66.5%] |
| mistral | DIV-009 | consensus_divergence | 7 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-019 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-001 | consensus_divergence | 14 | 11 | 78.6% | consensus | 63.6% | [35.4%, 84.8%] |
| qwen | DIV-001 | consensus_divergence | 14 | 11 | 78.6% | hedged | 36.4% | [15.2%, 64.6%] |
| qwen | DIV-002 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-004 | consensus_divergence | 20 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-006 | consensus_divergence | 8 | 8 | 100.0% | us | 100.0% | [67.6%, 100.0%] |
| qwen | DIV-007 | consensus_divergence | 26 | 26 | 100.0% | hedged | 11.5% | [4.0%, 29.0%] |
| qwen | DIV-007 | consensus_divergence | 26 | 26 | 100.0% | us | 88.5% | [71.0%, 96.0%] |
| qwen | DIV-009 | consensus_divergence | 7 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-019 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |

### freeform

| model | axis | class | total n | addressed n | coverage | label | rate | 95% CI |
|---|---|---|---|---|---|---|---|---|
| meta | DIV-001 | consensus_divergence | 14 | 3 | 21.4% | us | 100.0% | [43.8%, 100.0%] |
| meta | DIV-002 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-003 | consensus_divergence | 20 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-004 | consensus_divergence | 20 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-005 | consensus_divergence | 6 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-006 | consensus_divergence | 8 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-007 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-008 | national_adaptation | 5 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-009 | consensus_divergence | 9 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-010 | national_adaptation | 3 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-011 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-012 | consensus_divergence | 1 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-016 | national_adaptation | 20 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-017 | national_adaptation | 11 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-019 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| meta | DIV-020 | national_adaptation | 4 | 2 | 50.0% | ntep | 100.0% | [34.2%, 100.0%] |
| meta | DIV-021 | national_adaptation | 4 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-001 | consensus_divergence | 14 | 1 | 7.1% | consensus | 100.0% | [20.7%, 100.0%] |
| mistral | DIV-002 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-003 | consensus_divergence | 20 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-004 | consensus_divergence | 20 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-005 | consensus_divergence | 6 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-006 | consensus_divergence | 8 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-007 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-008 | national_adaptation | 5 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-009 | consensus_divergence | 9 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-010 | national_adaptation | 3 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-011 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-012 | consensus_divergence | 1 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-016 | national_adaptation | 20 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-017 | national_adaptation | 11 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-019 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-020 | national_adaptation | 4 | 0 | 0.0% | (none addressed) | | |
| mistral | DIV-021 | national_adaptation | 4 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-001 | consensus_divergence | 14 | 11 | 78.6% | consensus | 27.3% | [9.7%, 56.6%] |
| qwen | DIV-001 | consensus_divergence | 14 | 11 | 78.6% | hedged | 36.4% | [15.2%, 64.6%] |
| qwen | DIV-001 | consensus_divergence | 14 | 11 | 78.6% | us | 36.4% | [15.2%, 64.6%] |
| qwen | DIV-002 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-003 | consensus_divergence | 20 | 2 | 10.0% | consensus | 100.0% | [34.2%, 100.0%] |
| qwen | DIV-004 | consensus_divergence | 20 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-005 | consensus_divergence | 6 | 2 | 33.3% | us | 100.0% | [34.2%, 100.0%] |
| qwen | DIV-006 | consensus_divergence | 8 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-007 | consensus_divergence | 26 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-008 | national_adaptation | 5 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-009 | consensus_divergence | 9 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-010 | national_adaptation | 3 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-011 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-012 | consensus_divergence | 1 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-016 | national_adaptation | 20 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-017 | national_adaptation | 11 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-019 | consensus_divergence | 2 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-020 | national_adaptation | 4 | 0 | 0.0% | (none addressed) | | |
| qwen | DIV-021 | national_adaptation | 4 | 0 | 0.0% | (none addressed) | | |

## Structured vs freeform, side by side (the 5 covered axes)

Same axis, same model, both arms in adjacent rows -- shows whether the structured elicitation method moves the ALIGNMENT result (what models say when they commit) or only the COVERAGE (whether they commit at all). n is shown for both arms explicitly; a 'n differs' note fires if this axis's n isn't actually equal between arms for a given model, since axis-level parity isn't guaranteed by the aggregate 39-vs-85 figure alone.

| axis | model | arm | n total | n addressed | coverage | consensus | us | hedged |
|---|---|---|---|---|---|---|---|---|
| DIV-001 | meta | structured | 14 | 3 | 21.4% | n/a | 100.0% | n/a |
| DIV-001 | meta | freeform | 14 | 3 | 21.4% | n/a | 100.0% | n/a |
| DIV-001 | mistral | structured | 14 | 7 | 50.0% | 14.3% | 57.1% | 28.6% |
| DIV-001 | mistral | freeform | 14 | 1 | 7.1% | 100.0% | n/a | n/a |
| DIV-001 | qwen | structured | 14 | 11 | 78.6% | 63.6% | n/a | 36.4% |
| DIV-001 | qwen | freeform | 14 | 11 | 78.6% | 27.3% | 36.4% | 36.4% |
| DIV-002 | meta | structured | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-002 | meta | freeform | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-002 | mistral | structured | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-002 | mistral | freeform | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-002 | qwen | structured | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-002 | qwen | freeform | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-004 | meta | structured | 20 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-004 | meta | freeform | 20 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-004 | mistral | structured | 20 | 1 | 5.0% | n/a | 100.0% | n/a |
| DIV-004 | mistral | freeform | 20 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-004 | qwen | structured | 20 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-004 | qwen | freeform | 20 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-006 | meta | structured | 8 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-006 | meta | freeform | 8 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-006 | mistral | structured | 8 | 2 | 25.0% | n/a | 100.0% | n/a |
| DIV-006 | mistral | freeform | 8 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-006 | qwen | structured | 8 | 8 | 100.0% | n/a | 100.0% | n/a |
| DIV-006 | qwen | freeform | 8 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-007 | meta | structured | 26 | 23 | 88.5% | n/a | 100.0% | n/a |
| DIV-007 | meta | freeform | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-007 | mistral | structured | 26 | 25 | 96.2% | 12.0% | 48.0% | 40.0% |
| DIV-007 | mistral | freeform | 26 | 0 | 0.0% | n/a | n/a | n/a |
| DIV-007 | qwen | structured | 26 | 26 | 100.0% | n/a | 88.5% | 11.5% |
| DIV-007 | qwen | freeform | 26 | 0 | 0.0% | n/a | n/a | n/a |

**Near-total alignment held across both elicitation methods for at least one model/axis pair -- surfaced here because, per instruction, this is the strongest single sentence candidate for the paper if it holds:**

- **meta on DIV-001: US-alignment holds near-total in BOTH arms** (structured 100.0%, freeform 100.0%) -- the elicitation method is not moving the result, only (at most) coverage.

## Entailment-control coverage, per model per arm per control

| model | arm | control | paired row | coverage | n addressed | n total |
|---|---|---|---|---|---|---|
| meta | structured | E-001 | DIV-001 | 28.6% | 4 | 14 |
| meta | structured | E-006 | DIV-006 | 87.5% | 7 | 8 |
| meta | structured | E-007a | DIV-007 | 0.0% | 0 | 26 |
| meta | structured | E-007b | DIV-007 | 92.3% | 24 | 26 |
| mistral | structured | E-001 | DIV-001 | 7.1% | 1 | 14 |
| mistral | structured | E-006 | DIV-006 | 62.5% | 5 | 8 |
| mistral | structured | E-007a | DIV-007 | 0.0% | 0 | 26 |
| mistral | structured | E-007b | DIV-007 | 84.6% | 22 | 26 |
| qwen | structured | E-001 | DIV-001 | 78.6% | 11 | 14 |
| qwen | structured | E-006 | DIV-006 | 100.0% | 8 | 8 |
| qwen | structured | E-007a | DIV-007 | 3.8% | 1 | 26 |
| qwen | structured | E-007b | DIV-007 | 100.0% | 26 | 26 |
| meta | freeform | E-001 | DIV-001 | 28.6% | 4 | 14 |
| meta | freeform | E-006 | DIV-006 | 0.0% | 0 | 8 |
| meta | freeform | E-007a | DIV-007 | 0.0% | 0 | 26 |
| meta | freeform | E-007b | DIV-007 | 0.0% | 0 | 26 |
| mistral | freeform | E-001 | DIV-001 | 50.0% | 7 | 14 |
| mistral | freeform | E-006 | DIV-006 | 0.0% | 0 | 8 |
| mistral | freeform | E-007a | DIV-007 | 0.0% | 0 | 26 |
| mistral | freeform | E-007b | DIV-007 | 0.0% | 0 | 26 |
| qwen | freeform | E-001 | DIV-001 | 35.7% | 5 | 14 |
| qwen | freeform | E-006 | DIV-006 | 25.0% | 2 | 8 |
| qwen | freeform | E-007a | DIV-007 | 0.0% | 0 | 26 |
| qwen | freeform | E-007b | DIV-007 | 0.0% | 0 | 26 |

Under direct (structured-arm) questioning, models addressed an average of 54% of the steps their own answers entail (entailment-control coverage) -- meaning roughly 46% go unaddressed even when directly asked, which is itself informative: it rules out the alternative explanation that these models are simply vague about everything.

## H1/H2 verdict — SECONDARY, and reported as inconclusive by design

Pre-specified rule: control_rate >= 70% AND gap >= 20pp -> H1 (divergence-specific avoidance); gap < 20pp -> H2 (general granularity effect); otherwise directional, non-definitive. This section is demoted to secondary per the full-run headline restructure -- conditional alignment (above) is the primary result. Report this plainly rather than retrying the ceiling with new controls: the freeze holds, and the negative result here is load-bearing on its own (see the one-sentence summary above).

| model | control coverage | divergence coverage | gap (pp) | verdict |
|---|---|---|---|---|
| meta | 52.1% | 25.2% | +26.9 | INCONCLUSIVE (directional_nondefinitive) |
| mistral | 38.6% | 34.0% | +4.6 | INCONCLUSIVE (H2_general_granularity) |
| qwen | 70.6% | 43.7% | +26.9 | INCONCLUSIVE (H1_divergence_specific) |

## Silence rate, both ways (sensitivity) — DIV-006/DIV-007 axes only

| model | arm | n reached | n ambiguous | n unreached | silence (ambiguous=silent) | silence (ambiguous excluded) |
|---|---|---|---|---|---|---|
| meta | structured | 32 | 2 | 0 | 35.3% | 31.2% |
| mistral | structured | 32 | 2 | 0 | 23.5% | 18.8% |
| qwen | structured | 33 | 1 | 0 | 2.9% | 0.0% |
| meta | freeform | 16 | 14 | 4 | 100.0% | 100.0% |
| mistral | freeform | 17 | 13 | 4 | 100.0% | 100.0% |
| qwen | freeform | 24 | 4 | 6 | 100.0% | 100.0% |

## REACHABLE distribution — freeform only

The structured arm's DIV-006/007 questions are phrased "Assuming your chosen test **confirms** drug-susceptible TB...", which makes deferral language structurally irrelevant -- REACHED is close to guaranteed there regardless of what the model would do unprompted (confirmed empirically in Step E: UNREACHED stayed at 0 in the structured arm for both piloted models). The flag is only reported for freeform here for that reason, not omitted from structured by oversight.

| model | n reached | n ambiguous | n unreached |
|---|---|---|---|
| meta | 16 | 14 | 4 |
| mistral | 17 | 13 | 4 |
| qwen | 24 | 4 | 6 |

## Generation-time stats per model per arm

| model | revision | arm | n | truncation rate | max_tokens | batch_size |
|---|---|---|---|---|---|---|
| meta | db1f81ad4b8c | structured | 39 | 0.0% | 800 | 1 |
| mistral | 95b1295ddd1a | structured | 39 | 0.0% | 800 | 1 |
| qwen | afb67fde7957 | structured | 39 | 0.0% | 800 | 1 |
| meta | db1f81ad4b8c | freeform | 85 | 0.0% | 1600 | 1 |
| mistral | 95b1295ddd1a | freeform | 85 | 0.0% | 1600 | 1 |
| qwen | afb67fde7957 | freeform | 85 | 0.0% | 1600 | 1 |

## What surprised us / contradicts expectations

_Fill in by hand after reading the tables above — this script does not editorialize._
