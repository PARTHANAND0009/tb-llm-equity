# Checkpoint 2b-v Step E — structured-vs-free-form re-pilot

12 vignettes x 2 models x 2 elicitation arms. Pre-specified rule
(stated in the Checkpoint 2b-v CRITICAL ANALYSIS CHANGE, before this ran):
control_rate >= 70% AND gap >= 20pp -> H1 (divergence-specific avoidance);
gap < 20pp -> H2 (general granularity effect); otherwise directional, non-definitive.

## H1/H2 headline (structured arm only)

| model | control coverage | divergence coverage | gap (pp) | verdict |
|---|---|---|---|---|
| epfl | 51.9% | 50.0% | +1.9 | H2_general_granularity |
| meta | 56.1% | 33.3% | +22.7 | directional_nondefinitive |

## Divergence-axis coverage, per model per arm

(fraction of consensus_divergence axis instances addressed at all -- consensus,
us, or hedged -- as opposed to not_addressed; NOT the same as the
consensus-alignment rate.)

| model | arm | coverage | n addressed | n total |
|---|---|---|---|---|
| epfl | structured | 50.0% | 18 | 36 |
| meta | structured | 33.3% | 12 | 36 |
| epfl | freeform | 11.1% | 4 | 36 |
| meta | freeform | 8.3% | 3 | 36 |

## Entailment-control coverage, per model per arm per control

| model | arm | control | paired row | coverage | n addressed | n total |
|---|---|---|---|---|---|---|
| epfl | structured | E-001 | DIV-001 | 16.7% | 2 | 12 |
| epfl | structured | E-006 | DIV-006 | 100.0% | 2 | 2 |
| epfl | structured | E-007a | DIV-007 | 0.0% | 0 | 11 |
| epfl | structured | E-007b | DIV-007 | 90.9% | 10 | 11 |
| meta | structured | E-001 | DIV-001 | 33.3% | 4 | 12 |
| meta | structured | E-006 | DIV-006 | 100.0% | 2 | 2 |
| meta | structured | E-007a | DIV-007 | 0.0% | 0 | 11 |
| meta | structured | E-007b | DIV-007 | 90.9% | 10 | 11 |
| epfl | freeform | E-001 | DIV-001 | 66.7% | 8 | 12 |
| epfl | freeform | E-006 | DIV-006 | 0.0% | 0 | 2 |
| epfl | freeform | E-007a | DIV-007 | 0.0% | 0 | 11 |
| epfl | freeform | E-007b | DIV-007 | 0.0% | 0 | 11 |
| meta | freeform | E-001 | DIV-001 | 33.3% | 4 | 12 |
| meta | freeform | E-006 | DIV-006 | 0.0% | 0 | 2 |
| meta | freeform | E-007a | DIV-007 | 0.0% | 0 | 11 |
| meta | freeform | E-007b | DIV-007 | 0.0% | 0 | 11 |

## Conditional alignment among ADDRESSED divergence axes (structured arm)

Excludes not_addressed entirely -- among responses that DID commit to a
position, what did they say.

| model | consensus | ntep | who | us | hedged | n addressed |
|---|---|---|---|---|---|---|
| epfl | 0 | 0 | 0 | 17 | 1 | 18 |
| meta | 0 | 0 | 0 | 12 | 0 | 12 |

## REACHABLE distribution and silence rate (DIV-006/DIV-007 axes only)

UNREACHED should fire against these repaired stems now (the reachability flag
exists specifically to catch drug-mention-without-deferral text this axis
shouldn't have been able to reach before the Step B stem repair). **If it stays
at zero here, investigate before trusting the flag** -- don't read a zero as a
clean bill of health by default.

| model | arm | n reached | n ambiguous | n unreached | silence (ambiguous=silent) | silence (ambiguous excluded) |
|---|---|---|---|---|---|---|
| epfl | structured | 13 | 0 | 0 | 23.1% | 23.1% |
| meta | structured | 12 | 1 | 0 | 30.8% | 25.0% |
| epfl | freeform | 7 | 3 | 3 | 100.0% | 100.0% |
| meta | freeform | 4 | 7 | 2 | 100.0% | 100.0% |

## Generation-time stats (captured on GPU by the notebook)

| model | revision | arm | n | mean output tokens | truncation rate | wall-clock/gen (s) | batch_size_used |
|---|---|---|---|---|---|---|---|
| epfl | 783c241b18b8 | structured | 12 | 292.5 | 0.0% (12) | 15.96 | 4 |
| meta | db1f81ad4b8c | structured | 12 | 280.9 | 0.0% (12) | 5.92 | 4 |
| epfl | 783c241b18b8 | freeform | 12 | 219.2 | 0.0% (12) | 10.44 | 4 |
| meta | db1f81ad4b8c | freeform | 12 | 420.8 | 0.0% (12) | 7.22 | 4 |

## Granite batch-size question

**No `ibm` data in this run** -- Granite's cell did not complete (e.g. OOM'd during model loading itself, before any generation), so there is nothing to report here yet. This is a missing observation, not a restoration failure -- don't conflate the two.

## What surprised us / contradicts the pre-specified rule

_Fill in by hand after reading the tables above — this script does not editorialize._
