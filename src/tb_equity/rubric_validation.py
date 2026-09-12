"""Self-consistency check: does the scorer classify each of the 100 real
vignettes' own hand-authored `ntep_correct_actions` / `who_correct_actions`
/ `us_correct_actions` strings the way it should?

This is not a substitute for tests/test_rubric.py's hand-labelled examples
(those pin *expected* behavior for a human to review). This is a coverage
check against every real divergence-row instantiation in the actual
vignette set -- ~270 (divergence_id, side) instances the classifier was not
specifically tuned against string-by-string, so a low accuracy here would
mean the hand-written patterns in clauses.py don't generalize past the
handful of examples used to write them.

Deliberately does NOT assume `ntep_correct_actions[i]` corresponds to
`divergence_ids[i]` -- spot-checking the real v1 data (see the Stage-1
checkpoint report) found that assumption holds for some vignettes (e.g.
VIG-001, VIG-008) but not others (e.g. VIG-002, where divergence_ids is
`[DIV-004, DIV-007, DIV-001]` but the action list is written in ascending
DIV-id order regardless), so there is no single consistent positional rule
to rely on. Instead, for each side, every divergence_id is checked against
the *concatenation* of that vignette's full action list for that side --
which is also exactly how score_response() checks a real model response
(the whole response text, not a substring), so this validates the same
matching regime the real scorer uses, not a stricter one.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tb_equity.clauses import CLAUSE_ASSERTIONS
from tb_equity.rubric import classify_axis
from tb_equity.schema import Vignette

_EXPECTED_LABEL_FOR_SIDE = {
    "ntep_correct_actions": {"consensus_divergence": "consensus", "national_adaptation": "ntep"},
    "who_correct_actions": {"consensus_divergence": "consensus", "national_adaptation": "who"},
    "us_correct_actions": {"consensus_divergence": "us", "national_adaptation": "us"},
}


@dataclass
class Mismatch:
    vignette_id: str
    divergence_id: str
    side: str
    expected: str
    got: str
    text: str


@dataclass
class ValidationReport:
    total_checked: int = 0
    total_correct: int = 0
    skipped_no_us_side: int = 0
    mismatches: list[Mismatch] = field(default_factory=list)
    # id -> (correct, total)
    per_divergence_id: dict[str, tuple[int, int]] = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        return self.total_correct / self.total_checked if self.total_checked else float("nan")


def _side_text(vignette: Vignette, side: str) -> str:
    return " ".join(getattr(vignette, side))


def validate_against_ground_truth(vignettes: list[Vignette]) -> ValidationReport:
    report = ValidationReport()
    for vignette in vignettes:
        for did in vignette.divergence_ids:
            assertion = CLAUSE_ASSERTIONS.get(did)
            if assertion is None:
                continue
            for side in ("ntep_correct_actions", "who_correct_actions", "us_correct_actions"):
                expected = _EXPECTED_LABEL_FOR_SIDE[side][assertion.divergence_class]
                if expected == "us" and "us" not in assertion.sides():
                    report.skipped_no_us_side += 1
                    continue
                text = _side_text(vignette, side)
                result = classify_axis(did, text)
                correct = result.label == expected
                report.total_checked += 1
                report.total_correct += int(correct)
                c, t = report.per_divergence_id.get(did, (0, 0))
                report.per_divergence_id[did] = (c + int(correct), t + 1)
                if not correct:
                    report.mismatches.append(
                        Mismatch(
                            vignette_id=vignette.id,
                            divergence_id=did,
                            side=side,
                            expected=expected,
                            got=result.label,
                            text=text,
                        )
                    )
    return report
