#!/usr/bin/env python3
"""Render data/vignettes/REVIEW_PACKET.md — a human-readable rendering of the vignette set.

Groups vignettes by presentation_type; each entry shows the stem, NTEP
correct actions, Western correct actions, and the divergence rows it
probes. Includes a one-page composition summary and any critique flags
that were auto-resolved during the critique pass (Step 3).

Usage: python scripts/render_review_packet.py [version]  (default: v1)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.render import (  # noqa: E402
    composition_summary,
    group_by_presentation_type,
    load_vignettes,
    resolved_critique_flag_summary,
)

OUT_PATH = REPO_ROOT / "data" / "vignettes" / "REVIEW_PACKET.md"


def render(version: str) -> str:
    vignettes = load_vignettes(version)
    lines = [f"# Vignette review packet — {version}", ""]

    if not vignettes:
        lines += [
            f"No vignettes found under `data/vignettes/{version}/`. Run "
            "`scripts/generate_vignettes.py` (and optionally "
            "`scripts/critique_vignettes.py`) first.",
            "",
        ]
        return "\n".join(lines) + "\n"

    lines += [
        "## Composition summary",
        "",
        "| presentation_type | burden_class | count |",
        "|---|---|---|",
    ]
    for pt, bc, n in composition_summary(vignettes):
        lines.append(f"| {pt} | {bc} | {n} |")
    lines.append(f"| **total** |  | **{len(vignettes)}** |")
    holdout_n = sum(1 for v in vignettes if v.holdout)
    lines += ["", f"Holdout vignettes: {holdout_n} of {len(vignettes)}.", ""]

    resolved = resolved_critique_flag_summary(version)
    lines += ["## Critique flags auto-resolved during revision", ""]
    if resolved:
        lines += ["| vignette | passes | flag types seen |", "|---|---|---|"]
        for vig_id, passes, flag_types in resolved:
            lines.append(f"| {vig_id} | {passes} | {', '.join(flag_types)} |")
    else:
        lines.append(
            "None recorded (no critiques directory, or every vignette passed on the first pass)."
        )
    lines.append("")

    lines += ["## Vignettes by presentation type", ""]
    for presentation_type, group in group_by_presentation_type(vignettes).items():
        lines.append(f"### {presentation_type} ({len(group)})")
        lines.append("")
        for v in group:
            holdout_tag = " `[HOLDOUT]`" if v.holdout else ""
            lines.append(f"#### {v.id}{holdout_tag} — {v.burden_class}")
            lines.append("")
            lines.append(f"**Divergence rows probed:** {', '.join(v.divergence_ids)}")
            lines.append("")
            lines.append(f"**Stem:** {v.stem}")
            lines.append("")
            lines.append("**NTEP-correct actions:**")
            for a in v.ntep_correct_actions:
                lines.append(f"- {a}")
            lines.append("")
            lines.append("**Western-correct actions:**")
            for a in v.western_correct_actions:
                lines.append(f"- {a}")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(version: str) -> None:
    OUT_PATH.write_text(render(version), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v1")
