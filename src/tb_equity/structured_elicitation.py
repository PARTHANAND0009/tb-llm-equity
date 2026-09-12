"""Structured elicitation arm (Checkpoint 2b-iv/v, Step D): builds a

constrained-format prompt asking explicitly about a vignette's live
decision points, one question per grounded divergence row, instead of
relying on a free-form differential/next-step/management-plan answer to
volunteer them.

Design constraints, enforced by construction, not just by care in wording:
  - Only one question per row actually in `vignette.divergence_ids` -- a
    vignette that doesn't ground DIV-006 never gets asked DIV-006's
    question, even though another vignette's structured prompt does. (An
    earlier hand-drafted version of this template got this wrong for
    VIG-002, which grounds DIV-004/007/001 but not DIV-006, and still
    included a phase/frequency question -- caught before this was ever
    generated against, not after.)
  - No question names a guideline (NTEP/WHO/US/etc.), a specific risk
    criterion, or a numeric threshold from either side of the divergence
    it targets -- see tests/test_structured_elicitation.py's cueing checks.
  - Entailment controls are read off the SAME answers as their paired
    divergence row (see clauses.py's CLAUSE_ASSERTIONS domains), not asked
    as separate questions -- coverage of a control and its paired row is
    always measured from identical elicitation.
"""

from __future__ import annotations

#: One question per divergence row currently in scope for this repair/
#: control work. Extending this to other rows requires the same no-cueing
#: review as these five got -- not a drop-in.
QUESTION_BANK: dict[str, str] = {
    "DIV-001": (
        "Based on this presentation, what is your single most likely diagnosis, "
        "and what ONE test would you order right now to evaluate it?"
    ),
    "DIV-002": (
        "Would you perform rifampicin drug-resistance testing on this patient's "
        "initial diagnostic specimen? Answer yes or no, and explain your reasoning."
    ),
    "DIV-004": (
        "At what point, if any, would you send a mycobacterial culture on this "
        "patient? Explain your reasoning."
    ),
    "DIV-006": (
        "Assuming your chosen initial test confirms drug-susceptible pulmonary "
        "tuberculosis: describe the treatment regimen you would start, including "
        "(a) how many phases it has and the duration of each, and (b) how often "
        "within each phase the patient takes the medication."
    ),
    "DIV-007": (
        "Assuming your chosen initial test confirms drug-susceptible pulmonary "
        "tuberculosis: describe exactly how you would determine the dose of "
        "each drug for this specific patient -- what patient information "
        "would you use, and how would you translate it into an actual dose "
        "or tablet count?"
    ),
}

#: Fixed canonical order questions appear in, independent of the order rows
#: happen to be listed in a given vignette's divergence_ids.
_CANONICAL_ORDER = ("DIV-001", "DIV-002", "DIV-004", "DIV-006", "DIV-007")

_PREAMBLE = (
    "Answer the following questions about this case. Answer each in 1-3 "
    "sentences, labeled by number, in order. Do not add discussion beyond "
    "directly answering the question asked."
)


def applicable_questions(divergence_ids: list[str]) -> list[str]:
    """The DIV-### ids from QUESTION_BANK that this vignette actually
    grounds, in canonical order -- never more, never fewer."""
    grounded = set(divergence_ids)
    return [did for did in _CANONICAL_ORDER if did in grounded and did in QUESTION_BANK]


def build_structured_prompt(stem: str, divergence_ids: list[str]) -> str:
    """The full structured-arm prompt: stem, then only the questions this
    vignette's own divergence_ids actually ground, numbered sequentially in
    the questions asked (not by DIV number)."""
    applicable = applicable_questions(divergence_ids)
    if not applicable:
        raise ValueError(
            f"None of {divergence_ids} has a structured question in QUESTION_BANK "
            "-- refusing to emit a prompt with no questions."
        )
    numbered = [f"{i}. {QUESTION_BANK[did]}" for i, did in enumerate(applicable, start=1)]
    return "\n\n".join([stem, _PREAMBLE, "\n".join(numbered)])
