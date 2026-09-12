"""Entailment controls (Checkpoint 2b-iv Step C-new / 2b-v Step C3):

clinical steps every position in a paired divergence row mathematically
requires, so coverage of these needs no guideline citation to interpret --
only whether the response mentions the step at all. Scoring is pass/
addressed/not_addressed only -- there is no ntep/us split, because there is
no divergence to have a side on. See RUBRIC_SPEC.md and the Checkpoint 2b
thread for the entailment argument behind each one and why several other
candidates were rejected rather than forced through.

Patterns here are the same ones already run against the real 36 pilot
responses to measure each control's salience (Checkpoint 2b-iv) -- this
module makes that ad hoc measurement into frozen, tested, reusable code
rather than a one-off script.
"""

from __future__ import annotations

import re
from typing import Literal

ControlLabel = Literal["addressed", "not_addressed"]

#: DIV-### row each control is paired with, for reporting divergence-vs-
#: control coverage on the same axis.
CONTROL_PAIRED_ROW: dict[str, str] = {
    "E-001": "DIV-001",
    "E-006": "DIV-006",
    "E-007a": "DIV-007",
    "E-007b": "DIV-007",
}

_PATTERNS: dict[str, re.Pattern[str]] = {
    "E-001": re.compile(
        r"\b(?:sputum|specimen|sample)\b[^.]{0,40}\b(?:collect|obtain|send|sent|submit)\w*\b"
        r"|\b(?:collect|obtain|send|order)\w*\b[^.]{0,40}\b(?:sputum|specimen|sample)\b",
        re.IGNORECASE,
    ),
    "E-006": re.compile(
        r"\b(?:2|two)[\s-]month\w*\b[^.]{0,100}\b(?:then|followed by|,?\s*and then|"
        r"for the (?:remaining|next|final))\b"
        r"|\bintensive\s+phase\b[^.]{0,100}\bcontinuation\s+phase\b",
        re.IGNORECASE,
    ),
    "E-007a": re.compile(
        r"\b(?:obtain|record|measure|check|confirm|verify)\w*\b[^.]{0,30}\b(?:body\s+)?weight\b"
        r"|\bweigh\s+the\s+patient\b",
        re.IGNORECASE,
    ),
    "E-007b": re.compile(
        r"\b\d+\s*mg\s*/\s*kg\b|\bweight[- ]band\b"
        r"|\bbased\s+on\s+(?:current\s+)?(?:body\s+)?weight\b"
        r"|\bweight\s+of\s+\d+\s*kg\b[^.]{0,60}\bdos",
        re.IGNORECASE,
    ),
}


def score_control(control_id: str, text: str) -> ControlLabel:
    pattern = _PATTERNS[control_id]
    return "addressed" if pattern.search(text) else "not_addressed"


def score_all_controls(text: str) -> dict[str, ControlLabel]:
    return {cid: score_control(cid, text) for cid in _PATTERNS}
