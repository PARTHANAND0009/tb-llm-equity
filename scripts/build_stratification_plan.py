#!/usr/bin/env python3
"""Build the systematic (non-random) stratification plan for the 150-vignette set.

Deterministically assigns every vignette slot to a combination of strata by
round-robin cycling through fixed value lists — never `random.choice`, so the
plan is reproducible and auditable. Writes:

  data/vignettes/stratification_plan.json  (machine-readable, one row per cell)
  data/vignettes/stratification_plan.md    (human-readable design doc)

This only plans *which combinations of strata* each of the 150 vignette slots
should cover. It does not call any model and does not write vignette content.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = REPO_ROOT / "data" / "vignettes" / "stratification_plan.json"
OUT_MD = REPO_ROOT / "data" / "vignettes" / "stratification_plan.md"

TOTAL_VIGNETTES = 150
TOTAL_HOLDOUT = 20

# Presentation-type groups, per the target composition. western_control's own
# presentation_type split is computed below, proportional to the india_high spread.
GROUPS = [
    {"presentation_type": "pulmonary", "burden_class": "india_high", "count": 40},
    {"presentation_type": "extrapulmonary", "burden_class": "india_high", "count": 35},
    {"presentation_type": "comorbid", "burden_class": "india_high", "count": 25},
    {"presentation_type": "drug_resistant", "burden_class": "india_high", "count": 20},
]
WESTERN_CONTROL_COUNT = 30

COMORBID_SUBTYPES = ["tb_diabetes", "tb_hiv", "undernutrition"]
DR_TB_SUBTYPES = ["rifampicin_mono_resistant", "mdr_tb", "pre_xdr_tb"]

AGE_BANDS = ["child_0_9", "adolescent_10_17", "adult_18_59", "older_adult_60_plus"]
SEXES = ["male", "female"]
SETTINGS = ["urban", "rural"]
OCCUPATIONS = [
    "student",
    "agricultural_worker",
    "informal_daily_wage_laborer",
    "factory_or_industrial_worker",
    "healthcare_worker",
    "homemaker",
    "retired",
    "migrant_worker",
]
SYMPTOM_DURATION_BANDS = [
    "2_4_weeks",
    "4_8_weeks",
    "8_12_weeks",
    "12_plus_weeks_delayed_presentation",
]
NUM_DISTRACTORS = [2, 3]
INCIDENTAL_COMORBIDITY_BURDEN = ["none", "mild", "significant"]


def allocate(total: int, weights: list[float]) -> list[int]:
    """Largest-remainder allocation of `total` across `weights`, summing exactly to `total`."""
    weight_sum = sum(weights)
    raw = [total * w / weight_sum for w in weights]
    floors = [int(x) for x in raw]
    remainder = total - sum(floors)
    fractional = sorted(
        range(len(weights)), key=lambda i: (raw[i] - floors[i]), reverse=True
    )
    for i in fractional[:remainder]:
        floors[i] += 1
    return floors


def build_cells() -> list[dict]:
    cells: list[dict] = []

    # western_control's presentation_type split, proportional to the india_high groups.
    wc_split = allocate(WESTERN_CONTROL_COUNT, [g["count"] for g in GROUPS])
    western_groups = [
        {"presentation_type": g["presentation_type"], "burden_class": "western_control", "count": n}
        for g, n in zip(GROUPS, wc_split, strict=False)
    ]

    all_groups = GROUPS + western_groups

    # Per-group holdout counts, proportional to group size, summing to TOTAL_HOLDOUT.
    holdout_counts = allocate(TOTAL_HOLDOUT, [g["count"] for g in all_groups])

    age_cycle = itertools.cycle(AGE_BANDS)
    sex_cycle = itertools.cycle(SEXES)
    setting_cycle = itertools.cycle(SETTINGS)
    occupation_cycle = itertools.cycle(OCCUPATIONS)
    duration_cycle = itertools.cycle(SYMPTOM_DURATION_BANDS)
    distractor_cycle = itertools.cycle(NUM_DISTRACTORS)
    burden_cycle = itertools.cycle(INCIDENTAL_COMORBIDITY_BURDEN)
    comorbid_subtype_cycle = itertools.cycle(COMORBID_SUBTYPES)
    dr_subtype_cycle = itertools.cycle(DR_TB_SUBTYPES)

    seq = 0
    for group, holdout_n in zip(all_groups, holdout_counts, strict=False):
        # Which positions within this group are holdout — evenly spaced, not random.
        count = group["count"]
        if holdout_n:
            step = count / holdout_n
            holdout_positions = {int(i * step) for i in range(holdout_n)}
        else:
            holdout_positions = set()

        for position_in_group in range(count):
            seq += 1
            subtype = None
            comorbidity_burden = next(burden_cycle)
            if group["presentation_type"] == "comorbid":
                subtype = next(comorbid_subtype_cycle)
                comorbidity_burden = "significant"
            elif group["presentation_type"] == "drug_resistant":
                subtype = next(dr_subtype_cycle)

            cells.append(
                {
                    "cell_id": f"STRAT-{seq:03d}",
                    "presentation_type": group["presentation_type"],
                    "burden_class": group["burden_class"],
                    "subtype": subtype,
                    "age_band": next(age_cycle),
                    "sex": next(sex_cycle),
                    "setting": next(setting_cycle),
                    "occupation_class": next(occupation_cycle),
                    "comorbidity_burden": comorbidity_burden,
                    "symptom_duration_band": next(duration_cycle),
                    "num_distractors": next(distractor_cycle),
                    "holdout": position_in_group in holdout_positions,
                }
            )

    return cells


def render_markdown(cells: list[dict]) -> str:
    def count_by(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in cells:
            v = c[key]
            out[v] = out.get(v, 0) + 1
        return out

    lines = [
        "# Vignette stratification plan",
        "",
        "Systematic (deterministic round-robin), not random, assignment of strata to each of the "
        f"{len(cells)} vignette slots. Generated by `scripts/build_stratification_plan.py` — "
        "re-run that script to regenerate this file and `stratification_plan.json` together; "
        "do not hand-edit either.",
        "",
        "## Composition",
        "",
        "| presentation_type | burden_class | count |",
        "|---|---|---|",
    ]
    combo_counts: dict[tuple[str, str], int] = {}
    for c in cells:
        key = (c["presentation_type"], c["burden_class"])
        combo_counts[key] = combo_counts.get(key, 0) + 1
    for (pt, bc), n in sorted(combo_counts.items()):
        lines.append(f"| {pt} | {bc} | {n} |")
    lines.append(f"| **total** |  | **{len(cells)}** |")

    lines += [
        "",
        f"Holdout: {sum(1 for c in cells if c['holdout'])} of {len(cells)}, "
        "stratified proportionally across the groups above (largest-remainder allocation).",
        "",
        "## Systematic variation axes",
        "",
        "Each vignette slot cycles deterministically through these value lists — no `random` "
        "calls — so coverage is even and reproducible:",
        "",
    ]
    for key, values in [
        ("age_band", AGE_BANDS),
        ("sex", SEXES),
        ("setting", SETTINGS),
        ("occupation_class", OCCUPATIONS),
        ("symptom_duration_band", SYMPTOM_DURATION_BANDS),
        ("num_distractors", NUM_DISTRACTORS),
        (
            "comorbidity_burden (incidental, non-`comorbid`-category cases)",
            INCIDENTAL_COMORBIDITY_BURDEN,
        ),
        ("comorbid subtype (`comorbid` presentation_type only)", COMORBID_SUBTYPES),
        ("drug-resistance subtype (`drug_resistant` presentation_type only)", DR_TB_SUBTYPES),
    ]:
        lines.append(f"- **{key}**: {', '.join(str(v) for v in values)}")

    lines += [
        "",
        "## Distribution by axis (sanity check)",
        "",
    ]
    for key in ("age_band", "sex", "setting", "symptom_duration_band", "num_distractors"):
        counts = ", ".join(f"{k}={v}" for k, v in sorted(count_by(key).items()))
        lines.append(f"- `{key}`: {counts}")

    lines += [
        "",
        "## Full cell list",
        "",
        "See `stratification_plan.json` for the complete machine-readable list of all "
        f"{len(cells)} cells (one per planned vignette slot). Each cell is consumed by "
        "`scripts/generate_vignettes.py`, which grounds the generated case in one or more "
        "divergence-table rows appropriate to its `presentation_type`/`subtype` and renders the "
        "generation prompt from the cell's strata.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    cells = build_cells()
    assert len(cells) == TOTAL_VIGNETTES, f"expected {TOTAL_VIGNETTES} cells, got {len(cells)}"
    assert sum(1 for c in cells if c["holdout"]) == TOTAL_HOLDOUT

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(cells, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(cells), encoding="utf-8")
    print(f"Wrote {len(cells)} cells to {OUT_JSON} and {OUT_MD}")


if __name__ == "__main__":
    main()
