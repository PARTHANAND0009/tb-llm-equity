"""Shared helpers for rendering a vignette set to human-readable Markdown.

Used by scripts/render_review_packet.py and scripts/render_clinician_review.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from tb_equity.schema import Vignette

REPO_ROOT = Path(__file__).resolve().parents[2]
VIGNETTES_ROOT = REPO_ROOT / "data" / "vignettes"


def load_vignettes(version: str) -> list[Vignette]:
    version_dir = VIGNETTES_ROOT / version
    vignettes = []
    for path in sorted(version_dir.glob("VIG-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        vignettes.append(Vignette.model_validate(data))
    return sorted(vignettes, key=lambda v: v.id)


def group_by_presentation_type(vignettes: list[Vignette]) -> dict[str, list[Vignette]]:
    groups: dict[str, list[Vignette]] = {}
    for v in vignettes:
        groups.setdefault(v.presentation_type, []).append(v)
    return dict(sorted(groups.items()))


def composition_summary(vignettes: list[Vignette]) -> list[tuple[str, str, int]]:
    counts: dict[tuple[str, str], int] = {}
    for v in vignettes:
        key = (v.presentation_type, v.burden_class)
        counts[key] = counts.get(key, 0) + 1
    return [(pt, bc, n) for (pt, bc), n in sorted(counts.items())]


def resolved_critique_flag_summary(version: str) -> list[tuple[str, int, list[str]]]:
    """Return (vignette_id, passes_taken, flag_types_seen) for vignettes with >1 critique pass."""
    critiques_dir = VIGNETTES_ROOT / "critiques"
    if not critiques_dir.exists():
        return []
    by_vignette: dict[str, list[str]] = {}
    for path in sorted(critiques_dir.glob("*_pass*.json")):
        vig_id = path.stem.rsplit("_pass", 1)[0]
        critique = json.loads(path.read_text(encoding="utf-8"))
        flag_types = [f["type"] for f in critique.get("flags", [])]
        by_vignette.setdefault(vig_id, []).extend(flag_types)

    resolved = []
    for vig_id, flag_types in sorted(by_vignette.items()):
        if flag_types:
            pass_files = sorted(critiques_dir.glob(f"{vig_id}_pass*.json"))
            resolved.append((vig_id, len(pass_files), sorted(set(flag_types))))
    return resolved
