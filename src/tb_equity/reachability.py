"""Additive REACHABLE flag -- orthogonal to RUBRIC_VERSION v1's frozen

classify_axis/score_response output (src/tb_equity/rubric.py), which this
module never modifies or imports scoring logic from. Distinguishes "the
response never got to a point where this axis could be addressed"
(UNREACHED) from ordinary silence ("addressed the topic broadly but didn't
commit to a position on this specific axis" -- not_addressed while REACHED).

Motivation (Checkpoint 2b-iii/iv): repairing DIV-001's 16 vignettes removes
the pre-reported molecular-test result, making the case genuinely
presumptive. A clinically well-calibrated response to a presumptive case may
reasonably defer treatment decisions ("order Xpert, await result") --
DIV-006/DIV-007 (both treatment-initiation-stage) could then never be
addressed not because the model is silent on protocol, but because the
scenario itself no longer reaches a treatment decision. Conflating that with
ordinary not_addressed would misread a reachability artifact as silence.

Scope: only DIV-006 and DIV-007 are treated as reachability-sensitive here
-- the two rows Checkpoint 2b-ii/iii's interaction analysis actually flagged
as at risk from the DIV-001 repair. Other treatment-domain rows (DIV-008,
DIV-009, ...) have not been through that analysis and are deliberately left
at the trivial REACHED default rather than silently extended into scope.
"""

from __future__ import annotations

import re
from typing import Literal

Reachability = Literal["REACHED", "UNREACHED", "AMBIGUOUS"]

#: Rows whose decision presupposes a decision to start treatment now --
#: derived from the Checkpoint 2b-iii interaction analysis, not a general
#: "all treatment-domain rows" rule.
REACHABILITY_SENSITIVE_ROWS = frozenset({"DIV-006", "DIV-007"})

#: Any explicit naming of a first-line anti-TB drug or the regimen as a
#: whole -- evidence the response actually committed to starting treatment,
#: regardless of whether it addressed the specific frequency/dosing-
#: mechanism axis. Deliberately excludes the bare abbreviation "RIF": it
#: collides with test names ("Xpert MTB/RIF"), which are never a treatment
#: commitment -- confirmed live by a failing unit test before this fix.
#: "INH"/"PZA"/"EMB"/"HRZE" don't have that collision and are kept.
_DRUG_MENTION_RE = re.compile(
    r"\b(isoniazid|rifampi(?:cin|n)|pyrazinamide|ethambutol|INH|PZA|EMB|HRZE|ATT|"
    r"anti-TB\s+(?:drug|therapy|regimen|medication)s?|first-line\s+(?:treatment|therapy|regimen))\b",
    re.IGNORECASE,
)

#: Language indicating the response explicitly defers TB treatment pending
#: further confirmation -- the signature of a genuinely unreached decision,
#: not mere brevity.
_DEFERRAL_RE = re.compile(
    r"\b(?:await(?:ing)?|pending)\b[^.]{0,60}\b(?:result|confirmation|culture|diagnosis|test)\b"
    r"|\bbefore\s+(?:starting|initiating)\s+(?:treatment|therapy|ATT)\b"
    r"|\bonce\s+(?:confirmed|results?\s+(?:are|come)\s+back|diagnosis\s+is\s+confirmed)\b"
    r"|\bdo\s+not\s+(?:start|initiate)\s+(?:treatment|therapy|ATT)\b[^.]{0,60}\buntil\b",
    re.IGNORECASE,
)


def compute_reachability(divergence_id: str, text: str) -> Reachability:
    """REACHED: response committed to a regimen (drug names appear) with no
    explicit deferral. UNREACHED: response explicitly defers treatment
    pending confirmation, or never mentions any drug/regimen at all --
    either way, there's nothing for classify_axis's not_addressed label to
    distinguish from "the model just didn't say more." AMBIGUOUS: both a
    drug mention and deferral language are present (e.g. "start empiric
    therapy pending confirmation, then de-escalate") -- genuinely
    unresolvable without human judgment, reported as its own bucket rather
    than forced into either side.
    """
    if divergence_id not in REACHABILITY_SENSITIVE_ROWS:
        return "REACHED"

    has_drug = bool(_DRUG_MENTION_RE.search(text))
    has_deferral = bool(_DEFERRAL_RE.search(text))

    if has_drug and not has_deferral:
        return "REACHED"
    if has_drug and has_deferral:
        return "AMBIGUOUS"
    return "UNREACHED"  # no drug mention at all, deferral or not
