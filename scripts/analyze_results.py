#!/usr/bin/env python3
"""Stage 2 / Step 5 primary analysis + Step 6 honest report.

Reads every checkpointed response under data/responses/ (written by
notebooks/open_weight_inference.ipynb -- see src/tb_equity/checkpoint.py for
the file shape) and every vignette under data/vignettes/v1/, scores each
response with the frozen RUBRIC_VERSION scorer (src/tb_equity/rubric.py --
never edited by this script), and writes results/CHECKPOINT2.md.

Refuses to run against zero responses -- an empty report would look like a
result. Run `make manifest-check` first to confirm the manifests this data
came from are valid (RULE 1).

Usage: python scripts/analyze_results.py [version]  (default: v1)
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESPONSES_DIR = REPO_ROOT / "data" / "responses"
CHECKPOINT_OUT = REPO_ROOT / "results" / "CHECKPOINT2.md"

sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.analysis import (  # noqa: E402
    RawResponse,
    breakdown_by_category,
    breakdown_by_clause,
    compute_variance,
    score_all,
    summarize_model,
    truncation_rate_by_family,
)
from tb_equity.render import load_vignettes  # noqa: E402
from tb_equity.rubric import RUBRIC_VERSION, score_response  # noqa: E402
from tb_equity.rubric_variants import classify_axis_naive  # noqa: E402


def load_raw_responses(responses_dir: Path) -> list[RawResponse]:
    responses = []
    for path in sorted(responses_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data["raw"]
        responses.append(
            RawResponse(
                vignette_id=raw["vignette_id"],
                arm=raw["arm"],
                family=_family_for(raw),
                model=raw["model"],
                model_revision=raw.get("model_revision", "unknown"),
                seed=raw.get("seed", 0),
                text=data["text"],
                truncated=raw.get("truncated", raw.get("stop_reason") == "max_tokens"),
            )
        )
    return responses


def _family_for(raw: dict) -> str:
    """The checkpoint's 'raw' field stores the full model repo id, not the
    short family name from config/models.yaml -- map it back so reports read
    'meta'/'epfl'/'ibm' rather than a long HF repo path."""
    model = raw["model"]
    mapping = {
        "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4": "meta",
        "Orion-zhen/Qwen3-8B-AWQ": "qwen",
        "solidrust/Mistral-7B-Instruct-v0.3-AWQ": "mistral",
        "EPFLiGHT/Meditron3-8B": "epfl",
        "ibm-granite/granite-4.2-8b": "ibm",
    }
    return mapping.get(model, model)


def naive_sensitivity(
    responses: list[RawResponse], vignettes_by_id
) -> dict[str, tuple[float, float]]:
    """Per family: (current-scorer deviation rate, naive-no-negation deviation
    rate) on the SAME real responses -- RUBRIC_SPEC.md section 10's stability
    check, re-run against real output instead of the synthetic corpus."""
    from tb_equity.clauses import CLAUSE_ASSERTIONS
    from tb_equity.rubric import VignetteScore, classify_axis, consensus_deviation_rate

    def score_with(classify_fn, vignette, text):
        axis_results = [
            classify_fn(did, text) for did in vignette.divergence_ids if did in CLAUSE_ASSERTIONS
        ]
        return VignetteScore(
            vignette_id=vignette.id,
            overall_label="scored",
            format_drift=False,
            axis_results=axis_results,
        )

    by_family_current: dict[str, list] = defaultdict(list)
    by_family_naive: dict[str, list] = defaultdict(list)
    for r in responses:
        vignette = vignettes_by_id.get(r.vignette_id)
        if vignette is None:
            continue
        by_family_current[r.family].append(score_with(classify_axis, vignette, r.text))
        by_family_naive[r.family].append(score_with(classify_axis_naive, vignette, r.text))

    result = {}
    for family in by_family_current:
        cur_rate, _, _ = consensus_deviation_rate(by_family_current[family])
        naive_rate, _, _ = consensus_deviation_rate(by_family_naive[family])
        result[family] = (cur_rate, naive_rate)
    return result


def render_checkpoint2(
    *,
    version: str,
    model_outcomes: dict,
    clause_breakdowns: dict,
    category_breakdowns: dict,
    variance_reports: dict,
    sensitivity: dict,
    truncation_rates: dict,
    n_total_responses: int,
) -> str:
    lines = [
        "# Checkpoint 2 — full-run primary analysis",
        "",
        f"RUBRIC_VERSION = `{RUBRIC_VERSION}` (frozen for this run, per Stage 2 instructions).",
        f"Vignette set: `{version}`. Total scored responses: {n_total_responses}.",
        "",
        "## Headline: consensus deviation rate per model",
        "",
        "95% CI via Wilson score interval (chosen for stable behavior near 0%/100%,",
        "see `src/tb_equity/analysis.py::wilson_interval`).",
        "",
        "| model | consensus deviation rate | 95% CI | n axes | US-alignment rate | 95% CI |",
        "|---|---|---|---|---|---|",
    ]
    for family, o in sorted(model_outcomes.items()):
        lo, hi = o.consensus_deviation_ci
        ulo, uhi = o.us_alignment_ci
        lines.append(
            f"| {family} | {o.consensus_deviation_rate:.1%} | [{lo:.1%}, {hi:.1%}] | "
            f"{o.consensus_deviation_n} | {o.us_alignment_rate:.1%} | [{ulo:.1%}, {uhi:.1%}] |"
        )

    lines += [
        "",
        "## What the deviation rate is made of (read this before the headline number above)",
        "",
        "The headline is `1 - P(consensus)`, which means `us`-aligned, `hedged`, and",
        "`not_addressed` all count as \"deviant\" identically -- but they mean very",
        "different things. A high deviation rate driven mostly by `not_addressed` says",
        "the model didn't commit to a position on that specific axis (which may just",
        "reflect this prompt format's granularity, not a protocol preference); a high",
        "rate driven by `us` says the model actively took the US-aligned action. Do not",
        "read the headline number alone as \"the model prefers US practice\" without",
        "checking this table -- see the per-clause note in RUBRIC_SPEC.md section 7.",
        "",
        "| model | consensus | us | hedged | not_addressed | n axes |",
        "|---|---|---|---|---|---|",
    ]
    for family, o in sorted(model_outcomes.items()):
        b = o.label_breakdown
        total = sum(b.values()) or 1
        lines.append(
            f"| {family} | {b.get('consensus', 0)} ({b.get('consensus', 0) / total:.0%}) | "
            f"{b.get('us', 0)} ({b.get('us', 0) / total:.0%}) | "
            f"{b.get('hedged', 0)} ({b.get('hedged', 0) / total:.0%}) | "
            f"{b.get('not_addressed', 0)} ({b.get('not_addressed', 0) / total:.0%}) | {total} |"
        )

    lines += [
        "",
        "## Refusal, format-drift, and truncation rates",
        "",
        "Reported separately, never folded into the deviation rate. A truncated",
        "response (hit `GENERATION_MAX_TOKENS` before emitting a real stop token) can",
        "cut off before addressing a later divergence axis, which would inflate that",
        "axis's `not_addressed` count for a reason unrelated to protocol preference --",
        "a high truncation rate for one model is a reason to treat that model's",
        "`not_addressed` numbers with extra caution, not a reason to exclude it.",
        "",
        "| model | refusal rate | format-drift rate | truncation rate | n responses |",
        "|---|---|---|---|---|",
    ]
    for family, o in sorted(model_outcomes.items()):
        trunc_rate, trunc_n = truncation_rates.get(family, (float("nan"), 0))
        lines.append(
            f"| {family} | {o.refusal_rate:.1%} | {o.format_drift_rate:.1%} | "
            f"{trunc_rate:.1%} | {o.n_responses_scored} |"
        )

    lines += ["", "## Breakdown by DIV-### clause", ""]
    for family, clauses in sorted(clause_breakdowns.items()):
        lines.append(f"### {family}")
        lines.append("")
        lines.append("| clause | deviation rate | n |")
        lines.append("|---|---|---|")
        for did, outcome in sorted(clauses.items(), key=lambda kv: kv[0]):
            lines.append(f"| {did} | {outcome.rate:.1%} | {outcome.total} |")
        lines.append("")

    lines += ["## Breakdown by vignette category (presentation_type)", ""]
    for family, cats in sorted(category_breakdowns.items()):
        lines.append(f"### {family}")
        lines.append("")
        lines.append("| category | deviation rate | n |")
        lines.append("|---|---|---|")
        for cat, outcome in sorted(cats.items()):
            lines.append(f"| {cat} | {outcome.rate:.1%} | {outcome.total} |")
        lines.append("")

    lines += [
        "## Within-vignette response variance across samples",
        "",
        "A 'flip' is a (vignette, arm, DIV-###) group where sampled responses did",
        "not all agree on the axis label -- protocol advice that changes between",
        "samples at the same decoding settings.",
        "",
        "| model | flip rate | n groups |",
        "|---|---|---|",
    ]
    for family, report in sorted(variance_reports.items()):
        lines.append(f"| {family} | {report.flip_rate:.1%} | {report.n_groups} |")

    lines += [
        "",
        "## Scorer sensitivity on real data (naive no-negation variant)",
        "",
        "| model | current scorer | naive (no negation) | delta (pp) |",
        "|---|---|---|---|",
    ]
    for family, (cur, naive) in sorted(sensitivity.items()):
        lines.append(f"| {family} | {cur:.1%} | {naive:.1%} | {(naive - cur) * 100:+.1f} |")

    lines += [
        "",
        "## What surprised us / contradicts the prereg hypothesis",
        "",
        "_Fill in by hand after reading the tables above — this script does not",
        "editorialize._",
        "",
        "## Clause rows where the scorer looks unreliable on real output",
        "",
        "_Fill in by hand: any DIV-### row where `not_addressed` or `hedged` is",
        "unexpectedly high, or where reading a handful of real responses for that",
        "row shows the pattern set missing real phrasing — see RUBRIC_SPEC.md",
        "section 9 for the v1 known limitations already on record before this run._",
    ]
    return "\n".join(lines) + "\n"


def main(
    version: str,
    responses_dir: Path = RESPONSES_DIR,
    out_path: Path = CHECKPOINT_OUT,
) -> None:
    if not responses_dir.exists() or not any(responses_dir.glob("*.json")):
        raise SystemExit(
            f"{responses_dir} has no response files yet -- refusing to write a report "
            "against zero data. Run the Colab notebook and copy data/responses/ + "
            "results/manifests/ back into this repo first."
        )

    vignettes = load_vignettes(version)
    vignettes_by_id = {v.id: v for v in vignettes}

    responses = load_raw_responses(responses_dir)
    print(f"Loaded {len(responses)} response files.")

    by_family = score_all(responses, vignettes_by_id)
    unscored = len(responses) - sum(len(v) for v in by_family.values())
    if unscored:
        print(
            f"WARNING: {unscored} responses referenced a vignette_id not found "
            f"in {version} -- skipped."
        )

    model_outcomes = {
        family: summarize_model(family, scores) for family, scores in by_family.items()
    }
    clause_breakdowns = {
        family: breakdown_by_clause(scores) for family, scores in by_family.items()
    }

    category_breakdowns = {}
    for family in by_family:
        family_responses = [
            r for r in responses if r.family == family and r.vignette_id in vignettes_by_id
        ]
        family_scores = [
            score_response(vignettes_by_id[r.vignette_id], r.text) for r in family_responses
        ]
        category_breakdowns[family] = breakdown_by_category(
            family_responses, family_scores, vignettes_by_id, lambda v: v.presentation_type
        )

    variance_reports = compute_variance(responses, vignettes_by_id)
    sensitivity = naive_sensitivity(responses, vignettes_by_id)
    truncation_rates = truncation_rate_by_family(responses)

    report = render_checkpoint2(
        version=version,
        model_outcomes=model_outcomes,
        clause_breakdowns=clause_breakdowns,
        category_breakdowns=category_breakdowns,
        variance_reports=variance_reports,
        sensitivity=sensitivity,
        truncation_rates=truncation_rates,
        n_total_responses=len(responses),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")
    print()
    print("Headline consensus deviation rates:")
    for family, o in sorted(model_outcomes.items()):
        print(f"  {family}: {o.consensus_deviation_rate:.1%} (n={o.consensus_deviation_n})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v1")
