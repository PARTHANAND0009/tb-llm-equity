"""Heuristic check for whether a model response follows the three-part

contract every arm-1 prompt asks for (see INSTRUCTION_BLOCK in
scripts/expand_arms.py): a ranked differential diagnosis, a single next
diagnostic step, and an initial management plan, "clearly labeled" and "in
that order." No Phase 5 scorer exists yet to check against directly (see
CLAUDE.md Status: "make score ... not yet implemented"), so this checks the
only contract that currently exists in the repo — the prompt's own
instructions — via a permissive heuristic (numbered "1./2./3.", "Step
1/2/3", or the three section names themselves, in order), not a strict
parser. False positives (structure detected where the response is
actually poor) are an acceptable failure mode for a pilot smoke-test;
false negatives (real structure missed) are not, so the patterns below are
intentionally loose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SECTION_PATTERNS = [
    re.compile(
        r"differential\s+diagnos|ranked\s+differential", re.IGNORECASE
    ),
    re.compile(
        r"next\s+diagnostic\s+step|diagnostic\s+step", re.IGNORECASE
    ),
    re.compile(
        r"management\s+plan|initial\s+management", re.IGNORECASE
    ),
]

_NUMBERED_SECTION_RE = re.compile(r"(?:^|\n)\s*(?:\d[.)]|Step\s+\d)", re.IGNORECASE)


@dataclass
class ParseabilityResult:
    parseable: bool
    sections_found: list[bool]
    numbered_sections_found: int
    reason: str


def check_parseable(text: str) -> ParseabilityResult:
    """Non-empty, and either (a) all three section labels appear, in

    order, or (b) at least 2 numbered/"Step N"-style section markers
    appear (a model may use its own wording for section names but still
    number them). Either is treated as parseable.
    """
    if not text or not text.strip():
        return ParseabilityResult(
            parseable=False, sections_found=[False, False, False],
            numbered_sections_found=0, reason="empty response",
        )

    positions = []
    for pattern in _SECTION_PATTERNS:
        match = pattern.search(text)
        positions.append(match.start() if match else None)

    sections_found = [p is not None for p in positions]
    found_positions = [p for p in positions if p is not None]
    in_order = found_positions == sorted(found_positions)

    numbered_count = len(_NUMBERED_SECTION_RE.findall(text))

    if all(sections_found) and in_order:
        return ParseabilityResult(
            parseable=True, sections_found=sections_found,
            numbered_sections_found=numbered_count,
            reason="all three section labels present, in order",
        )
    if numbered_count >= 2:
        return ParseabilityResult(
            parseable=True, sections_found=sections_found,
            numbered_sections_found=numbered_count,
            reason=f"{numbered_count} numbered/Step-N section markers present",
        )
    return ParseabilityResult(
        parseable=False, sections_found=sections_found,
        numbered_sections_found=numbered_count,
        reason=(
            f"neither all 3 section labels in order (found={sections_found}) "
            f"nor >=2 numbered markers (found {numbered_count})"
        ),
    )
