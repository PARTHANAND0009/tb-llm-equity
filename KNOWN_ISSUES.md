# Known issues

Problems identified but deliberately not fixed yet, recorded here so they
aren't lost. Each entry says why it matters and what fixing it would touch.

## 1. MODEL_REGISTRY mixes quantization methods across the roster

`config/models.yaml`'s `evaluation.models` (the four `colab_hf` open-weight
models) uses AWQ 4-bit for three models (Llama-3.1-8B, Qwen3-8B,
Mistral-7B-v0.3) and bitsandbytes NF4 for the fourth (Meditron3-8B), because
no pre-quantized AWQ checkpoint of Meditron3-8B exists on the Hub (checked
2026-08-06 -- searched, none found).

**Why it matters.** `results/PREREGISTRATION.md` frames the Llama-3.1-8B vs.
Meditron3-8B pair as a pre-specified secondary analysis isolating the effect
of clinical continued-pretraining, holding architecture and general
pretraining constant. Quantization method is not held constant across that
pair: AWQ and bitsandbytes NF4 are different quantization algorithms with
different error characteristics, so any difference observed between Llama
and Meditron is now confounded by quantization method as well as by
continued-pretraining. This weakens (does not necessarily invalidate, but
does weaken) the secondary analysis's core claim.

**Not fixed now because:** there is no free/zero-cost way to get an AWQ
checkpoint of Meditron3-8B without quantizing it ourselves (compute cost,
and a self-quantized checkpoint would introduce its own uncertainty). Options
worth evaluating before the full run: (a) quantize Meditron3-8B to AWQ
ourselves and validate it doesn't degrade quality noticeably vs. NF4, (b) run
both Llama and Meditron in NF4 instead of AWQ for symmetry (costs the AWQ
speed advantage on the other three-model comparisons, but only Llama needs a
second run), or (c) accept the confound and state it explicitly as a
limitation when reporting the secondary analysis. No decision made yet.

## 2. Corrupted two-column PDF extraction; DIV-016 over-represented in Arm 4

Protocol excerpts injected into Arm 4 prompts are extracted from
`data/protocols/*.txt` (plain-text dumps of the source PDFs) via
`scripts/expand_arms.py`'s anchor-and-excerpt logic. Two specific problems,
verified directly against `data/prompts/*/arm4.txt`:

- **DIV-008 and DIV-017 excerpts are garbled** where the source PDF page is a
  two-column table or figure layout. Example, DIV-017 (from `VIG-020/arm4.txt`,
  citing "National Guidance on Differentiated TB Care", Box 4.3/Figure 4.1):
  the extracted text interleaves a figure caption, a page header
  ("NATIONAL GUIDANCE ON DIFFERENTIATED TB CARE 27"), and column-wrapped
  table labels ("Mandatory Activities / Suggestive Activities / Discretionary
  Activities") with body prose, mid-sentence. DIV-008 similarly picks up a
  drug-dosage table's column headers ("Regimen for DS-TB / IP / CP / Drugs /
  Doses") spliced into continuation prose. The underlying `.txt` protocol
  dumps were produced by naive PDF text extraction, which reads two-column
  layouts left-to-right across the page rather than column-by-column.
- **DIV-016 (population-level active case-finding) is disproportionately
  represented in Arm 4**, appearing in 24 of 100 Arm 4 prompts (verified via
  `data/prompts/manifest.json`'s `protocol_chunks_injected`). DIV-016 is a
  programmatic/administrative decision (whether ACF is conducted routinely
  in defined risk groups) rather than a bedside clinical decision, which
  makes it a structurally easy anchor match (its source text is short,
  generic, and keyword-matches many vignettes' grounding) but a comparatively
  weak test of clinical reasoning at the point of care.

**Why it matters.** A model given garbled table text may fail to use it not
because it defaults to US practice, but because the injected context itself
is unusable -- conflating a retrieval-quality failure with the study's actual
question (RULE 6 territory: this needs to be distinguishable in scoring, not
silently averaged in). DIV-016 over-representation means Arm 4's aggregate
result is more heavily weighted toward one administrative decision point than
the divergence table's 17 rows would suggest, which could bias the Arm 4
aggregate before any model even runs.

**Not fixed now because:** fixing PDF extraction properly (column-aware
extraction, e.g. re-running with a layout-aware tool, or hand-cleaning the
affected source `.txt` files) and rebalancing anchor selection to avoid
over-representing structurally-easy rows are both real scope, not one-line
fixes, and neither blocks the pilot (whose purpose is throughput/parseability,
not scientific results). Must be resolved before Arm 4 results are
interpreted for the full run: at minimum, flag garbled-excerpt vignettes so
scoring can separate "model ignored garbled context" from "model defaulted to
US practice despite clean context."
