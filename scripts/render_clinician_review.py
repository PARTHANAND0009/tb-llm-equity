#!/usr/bin/env python3
"""Render data/vignettes/CLINICIAN_REVIEW.md — a review form for the physician reviewer.

Same underlying content as REVIEW_PACKET.md, formatted with a checkbox per
vignette for "clinically plausible / implausible / needs edit" and a
free-text field.

Usage: python scripts/render_clinician_review.py [version]  (default: v1)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.render import group_by_presentation_type, load_vignettes  # noqa: E402

OUT_PATH = REPO_ROOT / "data" / "vignettes" / "CLINICIAN_REVIEW.md"


def render(version: str) -> str:
    vignettes = load_vignettes(version)
    lines = [
        f"# Clinician review form — vignette set {version}",
        "",
        "For each vignette: mark one plausibility box and use the free-text field for anything "
        "that needs a specific edit (a finding to change, an action list correction, a distractor "
        "that doesn't read as plausible, etc.). Do not edit vignette JSON directly — record "
        "feedback here and it will be applied by the pipeline.",
        "",
    ]

    if not vignettes:
        lines += [
            f"No vignettes found under `data/vignettes/{version}/`. Run "
            "`scripts/generate_vignettes.py` (and optionally "
            "`scripts/critique_vignettes.py`) first.",
            "",
        ]
        return "\n".join(lines) + "\n"

    for presentation_type, group in group_by_presentation_type(vignettes).items():
        lines.append(f"## {presentation_type} ({len(group)})")
        lines.append("")
        for v in group:
            holdout_tag = " `[HOLDOUT]`" if v.holdout else ""
            lines.append(f"### {v.id}{holdout_tag} — {v.burden_class}")
            lines.append("")
            lines.append(f"**Divergence rows probed:** {', '.join(v.divergence_ids)}")
            lines.append("")
            lines.append(f"**Stem:** {v.stem}")
            lines.append("")
            lines.append("**NTEP-correct actions:**")
            for a in v.ntep_correct_actions:
                lines.append(f"- {a}")
            lines.append("")
            lines.append("**Comparator (WHO)-correct actions:**")
            for a in v.comparator_correct_actions:
                lines.append(f"- {a}")
            lines.append("")
            lines.append("**Distractors seeded:**")
            for d in v.distractors:
                lines.append(f"- {d}")
            lines.append("")
            lines.append("**Reviewer assessment:**")
            lines.append("")
            lines.append("- [ ] Clinically plausible")
            lines.append("- [ ] Clinically implausible")
            lines.append("- [ ] Needs edit")
            lines.append("")
            lines.append("Notes:")
            lines.append("")
            lines.append("```")
            lines.append("")
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(version: str) -> None:
    OUT_PATH.write_text(render(version), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v1")
