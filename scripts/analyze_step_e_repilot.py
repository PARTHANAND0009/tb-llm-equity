#!/usr/bin/env python3
"""Checkpoint 2b-v Step E: structured-vs-free-form re-pilot analysis.

Reads results/pilot/step_e_repilot/{meta,epfl,ibm}.json (written by
notebooks/open_weight_inference.ipynb's Section 9c -- copy that directory
back from Drive into the repo before running this) and every vignette under
data/vignettes/v1/, then produces the full report the Checkpoint 2b-v
CRITICAL ANALYSIS CHANGE asked for: per-model-per-arm divergence-axis and
per-control coverage, the pre-specified H1/H2 headline verdict, conditional
alignment among addressed axes, the REACHABLE/UNREACHED/AMBIGUOUS
distribution, silence rate reported both ways, and the generation-time
stats (tokens, truncation, wall-clock, batch size) the notebook captured.

No GPU needed -- this is pure local aggregation over already-generated text,
via the same frozen RUBRIC_VERSION scorer used everywhere else in this repo
(src/tb_equity/rubric.py, never edited by this script).

Refuses to run against zero responses, and refuses to run against a
holdout vignette (RULE 7) -- both would look like a result instead of
failing loudly.

Usage: python scripts/analyze_step_e_repilot.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STEP_E_DIR = REPO_ROOT / "results" / "pilot" / "step_e_repilot"
REPORT_OUT = REPO_ROOT / "results" / "CHECKPOINT_STEP_E.md"

sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.analysis import (  # noqa: E402
    RawResponse,
    conditional_alignment_among_addressed,
    control_coverage_by_family,
    divergence_addressed_by_family,
    headline_structured_vs_control,
    reachability_adjusted_silence,
    score_all,
    truncation_rate_by_family,
)
from tb_equity.entailment_controls import CONTROL_PAIRED_ROW  # noqa: E402
from tb_equity.render import load_vignettes  # noqa: E402

ELICITATIONS = ("structured", "freeform")


def _pct(x: float) -> str:
    """1-decimal percentage, or 'n/a' for NaN (a zero-denominator rate --
    e.g. every observation on an axis was AMBIGUOUS reachability, leaving
    nothing in the ambiguous-excluded denominator) rather than the literal
    string 'nan%', which reads as a bug rather than as missing data."""
    return "n/a" if math.isnan(x) else f"{x:.1%}"


def _num(x: float, spec: str = ".1f") -> str:
    return "n/a" if math.isnan(x) else format(x, spec)


def load_step_e_responses(step_e_dir: Path) -> list[RawResponse]:
    responses = []
    for path in sorted(step_e_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for r in payload["responses"]:
            responses.append(
                RawResponse(
                    vignette_id=r["vignette_id"],
                    arm=0,  # not arm-numbered -- elicitation is the axis under test here
                    family=r["family"],
                    model=r["model"],
                    model_revision=r["model_revision"],
                    seed=0,
                    text=r["text"],
                    truncated=r["truncated"],
                    elicitation=r["elicitation"],
                )
            )
    return responses


def load_generation_stats(step_e_dir: Path) -> dict[str, dict]:
    """Per family: model/revision, and per elicitation: elapsed_seconds,
    batch_size_used, mean_output_tokens, wall_clock_per_generation, n."""
    stats: dict[str, dict] = {}
    for path in sorted(step_e_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        family = payload["family"]
        by_elicitation = {}
        for elicitation in ELICITATIONS:
            summary = payload["elicitation_summary"].get(elicitation, {})
            recs = [r for r in payload["responses"] if r["elicitation"] == elicitation]
            n = len(recs)
            mean_out = sum(r["output_tokens"] for r in recs) / n if n else float("nan")
            elapsed = summary.get("elapsed_seconds", float("nan"))
            by_elicitation[elicitation] = {
                "n": n,
                "mean_output_tokens": mean_out,
                "elapsed_seconds": elapsed,
                "wall_clock_per_generation": elapsed / n if n else float("nan"),
                "batch_size_used": summary.get("batch_size_used"),
            }
        stats[family] = {
            "model": payload["model"],
            "model_revision": payload["model_revision"],
            "by_elicitation": by_elicitation,
        }
    return stats


def render_report(
    *,
    responses: list[RawResponse],
    vignettes_by_id: dict,
    gen_stats: dict[str, dict],
) -> str:
    families = sorted(gen_stats)
    lines = [
        "# Checkpoint 2b-v Step E — structured-vs-free-form re-pilot",
        "",
        f"12 vignettes x {len(families)} models x 2 elicitation arms. Pre-specified rule",
        "(stated in the Checkpoint 2b-v CRITICAL ANALYSIS CHANGE, before this ran):",
        "control_rate >= 70% AND gap >= 20pp -> H1 (divergence-specific avoidance);",
        "gap < 20pp -> H2 (general granularity effect); otherwise directional, non-definitive.",
        "",
        "## H1/H2 headline (structured arm only)",
        "",
        "| model | control coverage | divergence coverage | gap (pp) | verdict |",
        "|---|---|---|---|---|",
    ]
    headline = headline_structured_vs_control(responses, vignettes_by_id)
    for family in families:
        v = headline.get(family)
        if v is None:
            lines.append(f"| {family} | n/a | n/a | n/a | no structured-arm data |")
            continue
        gap_str = "n/a" if math.isnan(v.gap_pp) else f"{v.gap_pp:+.1f}"
        lines.append(
            f"| {family} | {_pct(v.control_coverage_rate)} | "
            f"{_pct(v.divergence_coverage_rate)} | {gap_str} | {v.verdict} |"
        )

    lines += ["", "## Divergence-axis coverage, per model per arm", ""]
    lines += [
        "(fraction of consensus_divergence axis instances addressed at all -- consensus,",
        "us, or hedged -- as opposed to not_addressed; NOT the same as the",
        "consensus-alignment rate.)",
        "",
        "| model | arm | coverage | n addressed | n total |",
        "|---|---|---|---|---|",
    ]
    for elicitation in ELICITATIONS:
        by_family = divergence_addressed_by_family(
            responses, vignettes_by_id, elicitation=elicitation
        )
        for family in families:
            rate, n_addr, n_tot = by_family.get(family, (float("nan"), 0, 0))
            lines.append(f"| {family} | {elicitation} | {_pct(rate)} | {n_addr} | {n_tot} |")

    lines += ["", "## Entailment-control coverage, per model per arm per control", ""]
    lines += ["| model | arm | control | paired row | coverage | n addressed | n total |",
              "|---|---|---|---|---|---|---|"]
    for elicitation in ELICITATIONS:
        by_family = control_coverage_by_family(responses, vignettes_by_id, elicitation=elicitation)
        for family in families:
            controls = by_family.get(family, {})
            for control_id in sorted(CONTROL_PAIRED_ROW):
                rate, n_addr, n_tot = controls.get(control_id, (float("nan"), 0, 0))
                paired_row = CONTROL_PAIRED_ROW[control_id]
                lines.append(
                    f"| {family} | {elicitation} | {control_id} | {paired_row} | "
                    f"{_pct(rate)} | {n_addr} | {n_tot} |"
                )

    lines += [
        "",
        "## Conditional alignment among ADDRESSED divergence axes (structured arm)",
        "",
        "Excludes not_addressed entirely -- among responses that DID commit to a",
        "position, what did they say.",
        "",
        "| model | consensus | ntep | who | us | hedged | n addressed |",
        "|---|---|---|---|---|---|---|",
    ]
    structured_scores = score_all(
        [r for r in responses if r.elicitation == "structured"], vignettes_by_id
    )
    for family in families:
        counts = conditional_alignment_among_addressed(structured_scores.get(family, []))
        total = sum(counts.values()) or 1
        lines.append(
            f"| {family} | {counts.get('consensus', 0)} | {counts.get('ntep', 0)} | "
            f"{counts.get('who', 0)} | {counts.get('us', 0)} | {counts.get('hedged', 0)} "
            f"| {total} |"
        )

    lines += [
        "",
        "## REACHABLE distribution and silence rate (DIV-006/DIV-007 axes only)",
        "",
        "UNREACHED should fire against these repaired stems now (the reachability flag",
        "exists specifically to catch drug-mention-without-deferral text this axis",
        "shouldn't have been able to reach before the Step B stem repair). **If it stays",
        "at zero here, investigate before trusting the flag** -- don't read a zero as a",
        "clean bill of health by default.",
        "",
        "| model | arm | n reached | n ambiguous | n unreached | silence "
        "(ambiguous=silent) | silence (ambiguous excluded) |",
        "|---|---|---|---|---|---|---|",
    ]
    for elicitation in ELICITATIONS:
        by_family = reachability_adjusted_silence(
            [r for r in responses if r.elicitation == elicitation], vignettes_by_id
        )
        for family in families:
            result = by_family.get(family)
            if result is None:
                lines.append(f"| {family} | {elicitation} | 0 | 0 | 0 | n/a | n/a |")
                continue
            _, total_incl = result.ambiguous_as_silence_n
            n_reached = total_incl - result.n_ambiguous
            lines.append(
                f"| {family} | {elicitation} | {n_reached} | {result.n_ambiguous} | "
                f"{result.n_unreached} | {_pct(result.ambiguous_as_silence_rate)} | "
                f"{_pct(result.ambiguous_excluded_rate)} |"
            )

    lines += ["", "## Generation-time stats (captured on GPU by the notebook)", ""]
    lines += [
        "| model | revision | arm | n | mean output tokens | truncation rate | "
        "wall-clock/gen (s) | batch_size_used |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for elicitation in ELICITATIONS:
        trunc_rates = truncation_rate_by_family(
            [r for r in responses if r.elicitation == elicitation]
        )
        for family in families:
            g = gen_stats[family]
            e = g["by_elicitation"][elicitation]
            trunc_rate, trunc_n = trunc_rates.get(family, (float("nan"), 0))
            lines.append(
                f"| {family} | {g['model_revision'][:12]} | {elicitation} | {e['n']} | "
                f"{_num(e['mean_output_tokens'])} | {_pct(trunc_rate)} ({trunc_n}) | "
                f"{_num(e['wall_clock_per_generation'], '.2f')} | {e['batch_size_used']} |"
            )

    ibm_stats = gen_stats.get("ibm", {}).get("by_elicitation", {})
    ibm_structured_bs = ibm_stats.get("structured", {}).get("batch_size_used")
    lines += [
        "",
        "## Granite batch-size question",
        "",
        f"Model revision pinned: `{gen_stats.get('ibm', {}).get('model_revision', 'n/a')}`.",
        (
            f"Structured-arm batch_size_used = {ibm_structured_bs} -- "
            + (
                "**restoration ACHIEVED**: the constrained format's shorter output let "
                "batch_size=4 run without OOM."
                if ibm_structured_bs == 4
                else "**restoration NOT achieved**: fell back to batch_size=1 on a real "
                "CUDA OOM even with the constrained format."
            )
        ),
        "",
        "## What surprised us / contradicts the pre-specified rule",
        "",
        "_Fill in by hand after reading the tables above — this script does not editorialize._",
    ]
    return "\n".join(lines) + "\n"


def main(step_e_dir: Path = STEP_E_DIR, out_path: Path = REPORT_OUT) -> None:
    if not step_e_dir.exists() or not any(step_e_dir.glob("*.json")):
        raise SystemExit(
            f"{step_e_dir} has no response files yet -- refusing to write a report "
            "against zero data. Run notebooks/open_weight_inference.ipynb's Section 9c "
            "and copy results/pilot/step_e_repilot/ back into this repo first."
        )

    vignettes = load_vignettes("v1")
    vignettes_by_id = {v.id: v for v in vignettes}

    responses = load_step_e_responses(step_e_dir)
    if not responses:
        raise SystemExit(
            f"{step_e_dir} contained files but zero response records -- refusing to continue."
        )

    holdout_hits = sorted(
        {
            r.vignette_id
            for r in responses
            if vignettes_by_id.get(r.vignette_id) and vignettes_by_id[r.vignette_id].holdout
        }
    )
    if holdout_hits:
        raise SystemExit(
            f"RULE 7 violation: {holdout_hits} are holdout=true vignettes but appear in "
            f"{step_e_dir} -- refusing to analyze. This should never happen (the notebook "
            "reads structured_pilot_manifest.json, which is built only from non-holdout "
            "vignettes) -- investigate how a holdout vignette's prompts ended up generated."
        )

    n_families = len({r.family for r in responses})
    print(f"Loaded {len(responses)} Step E responses across {n_families} models.")

    gen_stats = load_generation_stats(step_e_dir)
    report = render_report(
        responses=responses, vignettes_by_id=vignettes_by_id, gen_stats=gen_stats
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
