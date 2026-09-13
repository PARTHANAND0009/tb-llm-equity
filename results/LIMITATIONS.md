# Known limitations

Study-level limitations that are not specific to the scoring rubric itself
(for rubric/scorer limitations, see `RUBRIC_SPEC.md` section 9). Each entry
states what happened and why, so a reader can judge how much it should
discount a given result -- not just that a limitation exists.

## Granite-4.2-8B (`ibm`) dropped from the evaluation panel (2026-09-13)

**What happened:** During the Checkpoint 2b-v Step E re-pilot,
`ibm-granite/granite-4.2-8b` OOM'd during model *loading itself* -- before
generating a single response -- on a T4 that had already loaded and unloaded
three other 8B models earlier in the same Colab session. `config/models.yaml`
already carried a `batch_size: 1` override for this model from an earlier
pilot (real 2026-09-10 evidence: Granite averaged 1562/1600 output tokens per
response, far more verbose than the rest of the roster), precisely because it
was already the roster's tightest fit on T4 memory even before this failure.

**Decision:** Excluded from the panel for the full run, not retried.
`config/models.yaml`'s `ibm` entry is kept (marked `excluded: true`,
`excluded_reason`), not deleted -- the entry, its batch_size rationale, and
its rejection-of-Ministral-3 rationale remain useful provenance even though
the model itself is out of the active panel.

**What's left unanswered:** Whether the structured elicitation arm's shorter,
constrained-format output would have let Granite run at `batch_size=4`
instead of `1` (the original point of that override). This question is now
permanently open for Granite specifically -- not answered, not going to be
retried, given the 7-day-to-freeze timeline and the two-day throughput
Granite was already tracking toward at `batch_size=1`.

**What this means for interpreting the full run:** see the next entry below
-- `epfl` was subsequently dropped too, so the final panel is 3 models, not
4 or 5.

## Meditron3-8B (`epfl`) dropped from the evaluation panel (2026-09-14)

**What happened:** Nothing epfl-specific -- it was never run. Generation
order for the full run was `meta -> qwen -> mistral -> epfl`. Colab's free
tier GPU quota was exhausted repeatedly during meta's and qwen's generation,
forcing multiple disconnect/reconnect/resume cycles (each recoverable without
data loss via the per-response checkpoint design, but costing real wall-clock
time waiting for quota to reset). By the time mistral finished, continuing on
to epfl risked missing the 20 September instrument freeze. Rather than start
a fourth model under that time pressure, `epfl` was dropped ahead of time.

**Decision:** Excluded from the full-run panel, not attempted.
`config/models.yaml`'s `epfl` entry is kept (marked `excluded: true`,
`excluded_reason`) for provenance, not deleted.

**What's left unanswered:** Everything -- `epfl` has zero full-run data, not
partial data. Unlike Granite, this is not a technical failure specific to the
model; it is a scope decision made under a hard deadline. If time allows
before the freeze, `epfl` could still be run as a genuine addition (its
config entry, revision, and batch_size rationale are all still valid and
unchanged) -- this was a deliberate deferral, not a finding.

**What this means for interpreting the full run:** All full-run results
(conditional alignment, coverage, H1/H2) are reported over a **3-model
panel** (`meta`, `qwen`, `mistral`), not the 5-model panel used in earlier
pilot planning and not the 4-model panel `ibm`'s exclusion alone would have
left. Any claim about "the panel" or cross-model patterns should be read as
3 models. Notably, **no continued-pretrained-on-medical-text model is
represented in the final panel at all** -- both Granite and Meditron3-8B,
the panel's two domain-adapted models, ended up excluded, for unrelated
reasons. This is worth stating explicitly in any writeup: the full run's
findings describe general-purpose instruction-tuned models only.
