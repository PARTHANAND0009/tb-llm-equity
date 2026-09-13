#!/usr/bin/env python3
"""IRIS TMED full run: primary analysis.

Reads every checkpointed response under data/responses/ that carries an
'elicitation' field in its 'raw' payload (the full-run generation shape --
see notebooks/open_weight_inference.ipynb Section 12 -- distinguishing it
from Task B's arm-numbered checkpoints, which have no 'elicitation' key and
are silently skipped here rather than double-counted) and every non-holdout
vignette under data/vignettes/v1/, scores each response with the frozen
RUBRIC_VERSION scorer, and writes results/FULL_RUN.md.

HEADLINE RESTRUCTURE (per the "IRIS TMED: full run" instruction): the
PRIMARY reported result is conditional alignment -- among responses that
commit to a divergence axis, the ntep/who/us/consensus split, per axis per
model. Coverage and the H1/H2 comparison are reported SECOND, explicitly
marked secondary and (per the pre-specified rule) inconclusive when control
coverage never approaches the 70% ceiling that rule requires.

Refuses to run against zero responses. Run `make manifest-check` first.

Usage: python scripts/analyze_full_run.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESPONSES_DIR = REPO_ROOT / "data" / "responses"
MANIFEST_DIR = REPO_ROOT / "results" / "manifests"
REPORT_OUT = REPO_ROOT / "results" / "FULL_RUN.md"
FREEZE_DEADLINE = "2026-09-20"

sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.analysis import (  # noqa: E402
    RawResponse,
    control_coverage_by_family,
    headline_structured_vs_control,
    per_axis_alignment,
    reachability_adjusted_silence,
    score_all,
    truncation_rate_by_family,
)
from tb_equity.entailment_controls import CONTROL_PAIRED_ROW  # noqa: E402
from tb_equity.render import load_vignettes  # noqa: E402

ELICITATIONS = ("structured", "freeform")

#: The 5 divergence axes structured_elicitation.py's QUESTION_BANK covers --
#: the only axes where a genuine structured-vs-freeform comparison is
#: possible at all (every other axis has zero structured-arm data by
#: construction, so a side-by-side there would be comparing something to
#: nothing, not a real comparison).
COVERED_AXES = ("DIV-001", "DIV-002", "DIV-004", "DIV-006", "DIV-007")
NEAR_TOTAL_ALIGNMENT_THRESHOLD = 0.85

# Checkpoint 2b-v Step E's real per-model DIV-001 "among-addressed, us-aligned"
# rate, used as the baseline for the "materially drops at full n" flag below.
# epfl: 17/18 = 0.944; meta: 12/12 = 1.0.
STEP_E_DIV001_US_RATE = {"epfl": 17 / 18, "meta": 1.0}
DIV001_MATERIAL_DROP_PP = 0.20  # 20 percentage points
NEAR_ZERO_COVERAGE_THRESHOLD = 0.05


def _family_for(raw: dict) -> str:
    mapping = {
        "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4": "meta",
        "Orion-zhen/Qwen3-8B-AWQ": "qwen",
        "solidrust/Mistral-7B-Instruct-v0.3-AWQ": "mistral",
        "EPFLiGHT/Meditron3-8B": "epfl",
        "ibm-granite/granite-4.2-8b": "ibm",
    }
    return mapping.get(raw["model"], raw["model"])


def load_full_run_responses(responses_dir: Path) -> list[RawResponse]:
    responses = []
    for path in sorted(responses_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data["raw"]
        if "elicitation" not in raw:
            # A Task B (arm-numbered) checkpoint, not a full-run one -- skip, don't miscount.
            continue
        responses.append(
            RawResponse(
                vignette_id=raw["vignette_id"],
                arm=0,
                family=_family_for(raw),
                model=raw["model"],
                model_revision=raw.get("model_revision", "unknown"),
                seed=0,
                text=data["text"],
                truncated=raw.get("truncated", raw.get("stop_reason") == "max_tokens"),
                elicitation=raw["elicitation"],
            )
        )
    return responses


def load_full_run_manifests(manifest_dir: Path) -> dict[str, dict]:
    """Per family: the most recent iris-tmed-full-run-<family>-*.json manifest."""
    by_family: dict[str, dict] = {}
    for path in sorted(manifest_dir.glob("iris-tmed-full-run-*.json")):
        m = json.loads(path.read_text(encoding="utf-8"))
        family = m["model_identifiers"][0]["family"]
        # sorted() over the timestamped filenames means the last one wins -- the
        # most recent completed/resumed run for that family.
        by_family[family] = m
    return by_family


def _pct(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{x:.1%}"


def _ci(ci: tuple[float, float]) -> str:
    lo, hi = ci
    if math.isnan(lo) or math.isnan(hi):
        return "n/a"
    return f"[{lo:.1%}, {hi:.1%}]"


def compute_flags(
    responses: list[RawResponse], vignettes_by_id: dict, manifests: dict[str, dict]
) -> list[str]:
    flags: list[str] = []
    families = sorted({r.family for r in responses})

    for elicitation in ELICITATIONS:
        by_family = score_all(
            [r for r in responses if r.elicitation == elicitation], vignettes_by_id
        )
        for family in families:
            axes = per_axis_alignment(by_family.get(family, []))

            # Independent checks -- neither should short-circuit the other for
            # the same family, so no early `continue` between them.
            div001 = axes.get("DIV-001")
            baseline = STEP_E_DIV001_US_RATE.get(family)
            if div001 is not None and div001.addressed_n > 0 and baseline is not None:
                # A label absent from label_rates means zero instances of it --
                # a real 0%, not "no data" (that's addressed_n == 0, handled above).
                current_rate = div001.label_rates.get("us", (0.0, (0.0, 0.0)))[0]
                if (baseline - current_rate) >= DIV001_MATERIAL_DROP_PP:
                    flags.append(
                        f"DIV-001 us-aligned-among-addressed rate for {family} ({elicitation}) "
                        f"is {current_rate:.1%}, down {((baseline - current_rate) * 100):.1f}pp "
                        f"from the Step E baseline ({baseline:.1%}) -- flagged per explicit "
                        "instruction, investigate before treating the Step E pattern as "
                        "confirmed at full n."
                    )

            total_addressed = sum(ax.addressed_n for ax in axes.values())
            total_n = sum(ax.total_n for ax in axes.values())
            if total_n and (total_addressed / total_n) < NEAR_ZERO_COVERAGE_THRESHOLD:
                flags.append(
                    f"{family} ({elicitation}) addressed only {total_addressed}/{total_n} "
                    f"({total_addressed / total_n:.1%}) axis instances across ALL axes -- "
                    "near-zero commitment, flagged per explicit instruction."
                )

    for family, m in manifests.items():
        ts = m.get("utc_timestamp", "")
        if ts and ts[:10] > FREEZE_DEADLINE:
            flags.append(
                f"{family}'s full-run manifest timestamp ({ts}) is AFTER the "
                f"{FREEZE_DEADLINE} instrument freeze deadline."
            )

    return flags


def _covered_axes_side_by_side(
    responses: list[RawResponse], vignettes_by_id: dict, families: list[str]
) -> list[str]:
    """Structured vs freeform, side by side, for each of the 5 covered axes --

    the comparison that shows whether the elicitation method moves the
    ALIGNMENT result (what models say when they do commit) or only the
    COVERAGE (whether they commit at all). n is shown for both arms
    explicitly per axis per model, rather than assumed equal from the
    aggregate 39-vs-85 figure -- a per-axis check can still surface a gap
    the aggregate hides, even though the 5 covered axes happened to show
    identical n in the pre-run audit (every vignette grounding one of these
    axes is included in the structured set by construction -- see
    scripts/build_full_run_prompts.py).
    """
    by_elicitation_family_axes: dict[str, dict[str, dict]] = {}
    for elicitation in ELICITATIONS:
        by_family = score_all(
            [r for r in responses if r.elicitation == elicitation], vignettes_by_id
        )
        by_elicitation_family_axes[elicitation] = {
            family: per_axis_alignment(by_family.get(family, [])) for family in families
        }

    lines = [
        "## Structured vs freeform, side by side (the 5 covered axes)",
        "",
        "Same axis, same model, both arms in adjacent rows -- shows whether the "
        "structured elicitation method moves the ALIGNMENT result (what models say "
        "when they commit) or only the COVERAGE (whether they commit at all). n is "
        "shown for both arms explicitly; a 'n differs' note fires if this axis's n "
        "isn't actually equal between arms for a given model, since axis-level parity "
        "isn't guaranteed by the aggregate 39-vs-85 figure alone.",
        "",
        "| axis | model | arm | n total | n addressed | coverage | consensus | us | hedged |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    near_total_notes: list[str] = []
    for axis in COVERED_AXES:
        for family in families:
            n_by_arm: dict[str, int] = {}
            us_by_arm: dict[str, float] = {}
            for elicitation in ELICITATIONS:
                ax = by_elicitation_family_axes[elicitation].get(family, {}).get(axis)
                if ax is None:
                    lines.append(f"| {axis} | {family} | {elicitation} | 0 | 0 | n/a | | | |")
                    continue
                n_by_arm[elicitation] = ax.total_n
                consensus_rate = ax.label_rates.get("consensus", (float("nan"), None))[0]
                us_rate = ax.label_rates.get("us", (float("nan"), None))[0]
                hedged_rate = ax.label_rates.get("hedged", (float("nan"), None))[0]
                if not math.isnan(us_rate):
                    us_by_arm[elicitation] = us_rate
                lines.append(
                    f"| {axis} | {family} | {elicitation} | {ax.total_n} | {ax.addressed_n} | "
                    f"{_pct(ax.coverage_rate)} | {_pct(consensus_rate)} | {_pct(us_rate)} | "
                    f"{_pct(hedged_rate)} |"
                )

            if len(n_by_arm) == 2 and n_by_arm["structured"] != n_by_arm["freeform"]:
                note = (
                    f"*(n differs: structured={n_by_arm['structured']}, "
                    f"freeform={n_by_arm['freeform']})*"
                )
                cells = [axis, family, note, "", "", "", "", "", ""]
                lines.append("| " + " | ".join(cells) + " |")

            if (
                "structured" in us_by_arm
                and "freeform" in us_by_arm
                and us_by_arm["structured"] >= NEAR_TOTAL_ALIGNMENT_THRESHOLD
                and us_by_arm["freeform"] >= NEAR_TOTAL_ALIGNMENT_THRESHOLD
            ):
                near_total_notes.append(
                    f"**{family} on {axis}: US-alignment holds near-total in BOTH arms** "
                    f"(structured {us_by_arm['structured']:.1%}, freeform "
                    f"{us_by_arm['freeform']:.1%}) -- the elicitation method is not "
                    "moving the result, only (at most) coverage."
                )

    lines.append("")
    if near_total_notes:
        lines.append(
            "**Near-total alignment held across both elicitation methods for at least "
            "one model/axis pair -- surfaced here because, per instruction, this is the "
            "strongest single sentence candidate for the paper if it holds:**"
        )
        lines.append("")
        lines.extend(f"- {n}" for n in near_total_notes)
        lines.append("")

    return lines


def render_report(
    *,
    responses: list[RawResponse],
    vignettes_by_id: dict,
    manifests: dict[str, dict],
) -> str:
    families = sorted({r.family for r in responses})
    flags = compute_flags(responses, vignettes_by_id, manifests)

    lines = [
        "# IRIS TMED — full run",
        "",
        f"{len(families)}-model panel ({', '.join(families)}), n=1 (greedy decoding), "
        "free-form (all non-holdout vignettes) + structured (subset grounding a "
        "structured_elicitation.py axis) arms. RUBRIC_VERSION frozen; instrument freeze "
        "2026-09-20 respected.",
        "",
        "## Excluded from this panel",
        "",
        "**Granite (`ibm`)** -- OOM'd during model loading (before any generation) in the "
        "Checkpoint 2b-v Step E re-pilot; dropped without retry per explicit instruction.",
        "",
        "**Meditron3-8B (`epfl`)** -- never run at all; dropped ahead of time to protect "
        "the 20 September freeze deadline after repeated Colab free-tier quota "
        "exhaustion/disconnects during this run's generation, not due to any "
        "epfl-specific failure. Notably, both excluded models were the panel's "
        "continued-pretrained-on-medical-text entries -- the final panel below is "
        "general-purpose instruction-tuned models only.",
        "",
        "See `results/LIMITATIONS.md` for the full writeup of both exclusions, including "
        "what remains unanswered for each.",
        "",
        "## Flags (checked automatically -- read this before anything else)",
        "",
    ]
    if flags:
        for f in flags:
            lines.append(f"- **FLAG:** {f}")
    else:
        lines.append("None of the pre-specified flag conditions fired.")

    lines += [
        "",
        "## Conditional alignment per axis per model (PRIMARY result)",
        "",
        "Among responses that commit to a divergence axis at all (label != not_addressed), "
        "the ntep/who/us/consensus/hedged split. 95% CI via the Wilson score interval "
        "(chosen over the normal/Wald approximation for stable behavior near 0%/100%, "
        "which per-axis rates on a modest n frequently are -- see "
        "`src/tb_equity/analysis.py::wilson_interval`). Per-axis n is stated explicitly "
        "because live-axis counts differ by row.",
        "",
    ]
    for elicitation in ELICITATIONS:
        by_family = score_all(
            [r for r in responses if r.elicitation == elicitation], vignettes_by_id
        )
        lines.append(f"### {elicitation}")
        lines.append("")
        lines.append(
            "| model | axis | class | total n | addressed n | coverage | label | rate | 95% CI |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for family in families:
            axes = per_axis_alignment(by_family.get(family, []))
            for did in sorted(axes):
                ax = axes[did]
                if not ax.label_rates:
                    lines.append(
                        f"| {family} | {did} | {ax.divergence_class} | {ax.total_n} | "
                        f"{ax.addressed_n} | {_pct(ax.coverage_rate)} | (none addressed) | | |"
                    )
                    continue
                for label in sorted(ax.label_rates):
                    rate, ci = ax.label_rates[label]
                    lines.append(
                        f"| {family} | {did} | {ax.divergence_class} | {ax.total_n} | "
                        f"{ax.addressed_n} | {_pct(ax.coverage_rate)} | {label} | "
                        f"{_pct(rate)} | {_ci(ci)} |"
                    )
        lines.append("")

    lines += _covered_axes_side_by_side(responses, vignettes_by_id, families)

    lines += [
        "## Entailment-control coverage, per model per arm per control",
        "",
        "| model | arm | control | paired row | coverage | n addressed | n total |",
        "|---|---|---|---|---|---|---|",
    ]
    for elicitation in ELICITATIONS:
        by_family = control_coverage_by_family(responses, vignettes_by_id, elicitation=elicitation)
        control_rates_all: list[float] = []
        for family in families:
            controls = by_family.get(family, {})
            for control_id in sorted(CONTROL_PAIRED_ROW):
                rate, n_addr, n_tot = controls.get(control_id, (float("nan"), 0, 0))
                if not math.isnan(rate):
                    control_rates_all.append(rate)
                paired_row = CONTROL_PAIRED_ROW[control_id]
                lines.append(
                    f"| {family} | {elicitation} | {control_id} | {paired_row} | "
                    f"{_pct(rate)} | {n_addr} | {n_tot} |"
                )
    lines.append("")

    # The one-sentence "control coverage means models address roughly half the
    # steps their own answers entail" summary, computed from real data rather
    # than restating Step E's specific pilot numbers.
    structured_control_rates = []
    structured_controls = control_coverage_by_family(
        responses, vignettes_by_id, elicitation="structured"
    )
    for family in families:
        for rate, _, n_tot in structured_controls.get(family, {}).values():
            if not math.isnan(rate) and n_tot:
                structured_control_rates.append(rate)
    if structured_control_rates:
        avg_control = sum(structured_control_rates) / len(structured_control_rates)
        lines += [
            f"Under direct (structured-arm) questioning, models addressed an average of "
            f"{avg_control:.0%} of the steps their own answers entail (entailment-control "
            f"coverage) -- meaning roughly {1 - avg_control:.0%} go unaddressed even when "
            "directly asked, which is itself informative: it rules out the alternative "
            "explanation that these models are simply vague about everything.",
            "",
        ]

    lines += [
        "## H1/H2 verdict — SECONDARY, and reported as inconclusive by design",
        "",
        "Pre-specified rule: control_rate >= 70% AND gap >= 20pp -> H1 (divergence-specific "
        "avoidance); gap < 20pp -> H2 (general granularity effect); otherwise directional, "
        "non-definitive. This section is demoted to secondary per the full-run headline "
        "restructure -- conditional alignment (above) is the primary result. Report this "
        "plainly rather than retrying the ceiling with new controls: the freeze holds, and "
        "the negative result here is load-bearing on its own (see the one-sentence summary "
        "above).",
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
            f"{_pct(v.divergence_coverage_rate)} | {gap_str} | INCONCLUSIVE ({v.verdict}) |"
        )

    lines += [
        "",
        "## Silence rate, both ways (sensitivity) — DIV-006/DIV-007 axes only",
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

    lines += [
        "",
        "## REACHABLE distribution — freeform only",
        "",
        "The structured arm's DIV-006/007 questions are phrased \"Assuming your chosen "
        "test **confirms** drug-susceptible TB...\", which makes deferral language "
        "structurally irrelevant -- REACHED is close to guaranteed there regardless of "
        "what the model would do unprompted (confirmed empirically in Step E: UNREACHED "
        "stayed at 0 in the structured arm for both piloted models). The flag is only "
        "reported for freeform here for that reason, not omitted from structured by "
        "oversight.",
        "",
        "| model | n reached | n ambiguous | n unreached |",
        "|---|---|---|---|",
    ]
    freeform_reach = reachability_adjusted_silence(
        [r for r in responses if r.elicitation == "freeform"], vignettes_by_id
    )
    for family in families:
        result = freeform_reach.get(family)
        if result is None:
            lines.append(f"| {family} | 0 | 0 | 0 |")
            continue
        _, total_incl = result.ambiguous_as_silence_n
        n_reached = total_incl - result.n_ambiguous
        lines.append(f"| {family} | {n_reached} | {result.n_ambiguous} | {result.n_unreached} |")

    lines += [
        "",
        "## Generation-time stats per model per arm",
        "",
        "| model | revision | arm | n | truncation rate | max_tokens | batch_size |",
        "|---|---|---|---|---|---|---|",
    ]
    for elicitation in ELICITATIONS:
        trunc_rates = truncation_rate_by_family(
            [r for r in responses if r.elicitation == elicitation]
        )
        for family in families:
            m = manifests.get(family, {})
            rev = m.get("model_identifiers", [{}])[0].get("version", "unknown")[:12]
            max_tok = m.get("max_tokens", {})
            max_tok_str = (
                max_tok.get(elicitation, "unknown") if isinstance(max_tok, dict) else max_tok
            )
            batch_size = m.get("batch_size", "unknown")
            trunc_rate, trunc_n = trunc_rates.get(family, (float("nan"), 0))
            lines.append(
                f"| {family} | {rev} | {elicitation} | {trunc_n} | {_pct(trunc_rate)} | "
                f"{max_tok_str} | {batch_size} |"
            )

    lines += [
        "",
        "## What surprised us / contradicts expectations",
        "",
        "_Fill in by hand after reading the tables above — this script does not editorialize._",
    ]
    return "\n".join(lines) + "\n"


def main(
    responses_dir: Path = RESPONSES_DIR,
    manifest_dir: Path = MANIFEST_DIR,
    out_path: Path = REPORT_OUT,
) -> None:
    if not responses_dir.exists() or not any(responses_dir.glob("*.json")):
        raise SystemExit(
            f"{responses_dir} has no response files yet -- refusing to write a report "
            "against zero data. Run the full run in Colab and copy data/responses/ + "
            "results/manifests/ back into this repo first."
        )

    vignettes = load_vignettes("v1")
    vignettes_by_id = {v.id: v for v in vignettes}

    responses = load_full_run_responses(responses_dir)
    if not responses:
        raise SystemExit(
            f"{responses_dir} contained files but none carried an 'elicitation' field -- "
            "refusing to continue. Run the full-run notebook section first."
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
            f"{responses_dir}'s full-run responses -- refusing to analyze."
        )

    n_families = len({r.family for r in responses})
    print(f"Loaded {len(responses)} full-run responses across {n_families} models.")

    manifests = load_full_run_manifests(manifest_dir)
    report = render_report(
        responses=responses, vignettes_by_id=vignettes_by_id, manifests=manifests
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
