"""Per-clause deterministic classifiers for the 17 rows of
``data/divergence/divergence_table.json``.

Each :class:`ClauseAssertion` encodes, for one divergence row, the surface
vocabulary a model's free-text response would plausibly use if it took the
consensus/NTEP/WHO/US-aligned action for that row's decision point. These
patterns are read directly off ``decision_point``/``*_position`` in the
divergence table (see ``RUBRIC_SPEC.md`` for the full row text and the
rationale behind each pattern set) -- nothing here is invented; every axis
traces to a specific ``DIV-###`` id.

For a ``consensus_divergence`` row, the two sides that matter are
``consensus`` (NTEP and WHO agree) and ``us``. For a ``national_adaptation``
row there is no consensus position, so the sides are ``ntep``, ``who``, and
(where a real US document was fetched) ``us``.

This is a v1, heuristic, keyword/regex classifier -- not an NLP negation
parser. See RUBRIC_SPEC.md "Known limitations" for what it gets wrong and
why LLM-judge scoring (RULE 6) stays a supplementary layer, never the
headline number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Negation handling
# ---------------------------------------------------------------------------

#: Cues that negate whatever comes AFTER them (checked only in the window
#: BEFORE a match, e.g. "rather than smear microscopy" negates "smear
#: microscopy" which follows it -- a symmetric before/after check would
#: wrongly also negate whatever precedes "rather than" in the same
#: sentence, which is exactly the bug this directional split avoids: "Order
#: Xpert, rather than smear microscopy" must not negate "Xpert").
#: Deliberately broad-recall: false negatives here (a real affirmative
#: reading gets suppressed) are treated as more costly than false positives
#: (a genuine negation gets missed and the mention is kept), because a
#: suppressed affirmative just falls through to "not_addressed" rather than
#: flipping to the wrong side.
_PRE_NEGATION_CUE_RE = re.compile(
    r"\b("
    r"not|no longer|rather than|instead of|without(?:\s+first)?|"
    r"reserve[ds]?\s+for|reserved\s+for|only\s+if|only\s+for|unless|"
    r"do\s+not|don't|doesn't|does\s+not|isn't|is\s+not|are\s+not|"
    r"need\s+not|no\s+need\s+for|avoid|contrary\s+to|as\s+opposed\s+to|"
    r"never\s+(?:need|order|require)"
    r")\b",
    re.IGNORECASE,
)

#: Cues that negate whatever comes BEFORE them (checked only in the window
#: AFTER a match, e.g. "molecular testing is not necessary" negates
#: "molecular testing").
_POST_NEGATION_CUE_RE = re.compile(
    r"\b(?:is|are|was|were)?\s*not\s+(?:an?\s+)?(?:necessary|required|mandatory|routine|"
    r"standard|option|established|recommended|listed|available)\b|"
    r"\bno\s+longer\s+(?:required|recommended|necessary|standard)\b|"
    r"\bas\s+an?\s+optional\b|\boptional\s+(?:conditional\s+)?adjunct\b|"
    r"\bconditional(?:ly)?\s+(?:adjunct|recommend)|\brather\s+than\s+(?:the\s+)?mandatory\b",
    re.IGNORECASE,
)

#: How many characters of context on each side of a match are scanned for a
#: negation cue. Tuned by hand against the hand-labelled examples in
#: tests/test_rubric.py -- see RUBRIC_SPEC.md for why 50.
DEFAULT_NEGATION_WINDOW = 50


def affirmed_hits(
    patterns: tuple[str, ...], text: str, window: int = DEFAULT_NEGATION_WINDOW
) -> list[str]:
    """Return the subset of `patterns` that match `text` with no negation
    cue negating that specific match (pre-cues checked before the match,
    post-cues checked after -- see the directional note above)."""
    hits: list[str] = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            start, end = m.span()
            before = text[max(0, start - window) : start]
            after = text[end : end + window]
            if _PRE_NEGATION_CUE_RE.search(before) or _POST_NEGATION_CUE_RE.search(after):
                continue
            hits.append(pat)
            break  # one affirmed hit is enough evidence for this pattern
    return hits


# ---------------------------------------------------------------------------
# Clause assertion registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClauseAssertion:
    divergence_id: str
    domain: str
    divergence_class: str  # "consensus_divergence" | "national_adaptation"
    is_critical: bool
    axis_description: str
    consensus_patterns: tuple[str, ...] = ()
    ntep_patterns: tuple[str, ...] = ()
    who_patterns: tuple[str, ...] = ()
    us_patterns: tuple[str, ...] = ()

    def sides(self) -> dict[str, tuple[str, ...]]:
        """The named pattern-sets applicable to this row's divergence_class."""
        if self.divergence_class == "consensus_divergence":
            sides = {"consensus": self.consensus_patterns, "us": self.us_patterns}
        else:
            sides = {"ntep": self.ntep_patterns, "who": self.who_patterns}
            if self.us_patterns:
                sides["us"] = self.us_patterns
        return {name: pats for name, pats in sides.items() if pats}


CLAUSE_ASSERTIONS: dict[str, ClauseAssertion] = {}


def _register(assertion: ClauseAssertion) -> None:
    CLAUSE_ASSERTIONS[assertion.divergence_id] = assertion


_register(
    ClauseAssertion(
        divergence_id="DIV-001",
        domain="diagnosis",
        divergence_class="consensus_divergence",
        is_critical=True,
        axis_description="Initial test for presumptive pulmonary TB: molecular (NAAT) vs smear.",
        consensus_patterns=(
            r"\bxpert(?:\s*mtb\s*/?\s*rif)?(?:\s*ultra)?\b",
            r"\bcbnaat\b",
            r"\btruenat\b",
            r"\bgenexpert\b",
            # Bare "molecular test(ing)" is ambiguous on its own (it can
            # appear in a US-aligned sentence too, e.g. "...regardless of
            # the molecular test result" describing molecular testing as a
            # demoted adjunct) -- only count it when paired with
            # priority language indicating it's the recommended first step.
            r"\b(?:molecular|naat)\s+test(?:ing)?\b[^.]{0,15}\bas\s+the\s+(?:initial|first)\b",
            r"\b(?:first|initial|upfront)\s+(?:diagnostic\s+)?te"
            r"st\b[^.]{0,15}\b(?:molecular|naat)\s+test(?:ing)?\b",
            r"\border\b[^.]{0,15}\b(?:molecular|naat)\s+test(?:ing)?\b[^.]{0,20}\bfirst\b",
            r"\bnucleic\s+acid\s+amplification\b",
        ),
        us_patterns=(
            r"\b(?:afb\s+)?smear\s+microscopy\b",
            r"\bsputum\s+smear\b",
            r"\bafb\s+smear\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-002",
        domain="diagnosis",
        divergence_class="consensus_divergence",
        is_critical=True,
        axis_description="Rifampicin-resistance (DST) testing: universal vs risk-factor-gated.",
        consensus_patterns=(
            r"\buniversal\s+(?:drug[- ]susceptibility|dst)\b",
            r"\b(?:all|every|each)\s+(?:newly[- ]diagnosed\s+)?(?:t"
            r"b\s+)?patients?\b[^.]{0,60}\b(?:rifampicin|rifampin)\b",
            r"\bregardless\s+of\s+(?:risk|prior\s+treatment|hiv\s+status|birth|residence)\b",
            r"\brifampicin[- ]resistance\s+testing\b[^.]{0,40}\b(?:all|every|regardless)\b",
        ),
        us_patterns=(
            r"\brisk\s+criteri(?:on|a)\b",
            r"\bmeets?\s+(?:at\s+least\s+)?(?:one|a)?\s*(?:specific\s+)?risk\s+factor",
            r"\bonly\s+(?:for|if)\b[^.]{0,60}\b(?:prior\s+t"
            r"reatment|born\s+in|resident|contact\s+of|hiv)",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-003",
        domain="diagnosis",
        divergence_class="consensus_divergence",
        is_critical=False,
        axis_description="Extrapulmonary workup: upfront molecular testing vs culture/histology.",
        consensus_patterns=(
            r"\bxpert\s*ultra\b",
            r"\b(?:cbnaat|truenat|naat|molecular)\b[^.]{0,60}\b(?:csf|pleur"
            r"al|pericardial|synovial|urine|extrapulmonary|first[- ]line)\b",
            r"\bupfront\s+(?:molecular|naat)\b",
        ),
        us_patterns=(
            r"\bculture\s+and\s+histolog",
            r"\bhistopatholog(?:y|ic)\b[^.]{0,40}\breference\s+standard\b",
            r"\bculture\b[^.]{0,40}\breference\s+standard\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-004",
        domain="diagnosis",
        divergence_class="consensus_divergence",
        is_critical=False,
        axis_description="Mycobacterial culture: reserved for resistance cascade vs mandatory.",
        consensus_patterns=(
            r"\breserve[ds]?\b[^.]{0,40}\bculture\b",
            r"\bculture\b[^.]{0,50}\b(?:cascade|downstream|after\s+(?:a\s+)?positive)\b",
            r"\bnot\s+(?:a\s+)?(?:mandatory|routine)\s+parallel\s+(?:test|culture)\b",
        ),
        us_patterns=(
            r"\bculture\b[^.]{0,50}\b(?:every\s+specimen|in\s+parallel|rega"
            r"rdless\s+of\s+(?:the\s+)?(?:naat|molecular|smear)\s+result)\b",
            r"\b(?:both\s+)?liquid\s+and\s+solid\s+(?:mycobacterial\s+)?culture\b",
            r"\bculture\b[^.]{0,30}\bgold[- ]standard\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-005",
        domain="diagnosis",
        divergence_class="consensus_divergence",
        is_critical=False,
        axis_description="TBI test choice with BCG history: TST/IGRA interchangeable vs IGRA.",
        consensus_patterns=(
            r"\b(?:tst|tuberculin\s+skin\s+test)\s+(?:and|or)\s+igr"
            r"a\b[^.]{0,40}\b(?:interchangeable|either|equivalent)\b",
            r"\beither\s+(?:a\s+)?(?:tst|igra)\b",
            r"\bbcg\b[^.]{0,60}\bshould\s+not\s+(?:determine|be\s+a\s+determining\s+factor)\b",
        ),
        us_patterns=(
            r"\bigra\b[^.]{0,60}\b(?:preferred|recommended|rather\s+than\s+tst)\b[^.]{0,60}\bbcg\b",
            r"\bbcg\b[^.]{0,60}\bigra\b[^.]{0,40}\b(?:preferred|instead)\b",
            r"\bdue\s+to\s+(?:prior\s+)?bcg\s+vaccination\b[^.]{0,40}\bigra\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-006",
        domain="treatment",
        divergence_class="consensus_divergence",
        is_critical=True,
        axis_description="Dosing frequency: daily throughout vs intermittent continuation phase.",
        consensus_patterns=(
            r"\bdaily\b[^.]{0,60}\b(?:throughout|intensive\s+and\s+continuation|both\s+phases)\b",
            r"\bno\s+intermittent\b",
            r"\bdaily\s+dosing\b[^.]{0,40}\b(?:continuation|entire\s+course)\b",
        ),
        us_patterns=(
            r"\bthrice[- ]weekly\b",
            r"\btwice[- ]weekly\b",
            r"\bintermittent\s+dosing\b",
            r"\bthree\s+times\s+(?:a\s+|per\s+)?week\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-007",
        domain="treatment",
        divergence_class="consensus_divergence",
        is_critical=False,
        axis_description="Dosing mechanism: weight-band FDC tablet count vs per-kg calculation.",
        consensus_patterns=(
            r"\bweight[- ]band\b",
            r"\bfixed[- ]dose\s+combination\b",
            r"\bfdc\b[^.]{0,40}\btablet\b",
            r"\btablet\s+count\b",
        ),
        us_patterns=(
            r"\bmg\s*/\s*kg\b",
            r"\bper[- ]kilogram\b",
            r"\bmilligrams?\s+per\s+kilogram\b",
            r"\bcalculat(?:e|ed|ing)\b[^.]{0,40}\bindividually\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-008",
        domain="treatment",
        divergence_class="national_adaptation",
        is_critical=False,
        axis_description="Regimen extension on slow response: physician discretion vs fixed rule.",
        ntep_patterns=(
            r"\b(?:physician|clinician)(?:'s)?\s+discretion\b",
            r"\bcase[- ]by[- ]case\b[^.]{0,80}\bexten(?:d|ded|ding|sion)\b",
            r"\bindividuali[sz]ed\s+judg?ment\b[^.]{0,80}\bexten(?:d|ded|ding|sion)\b",
            r"\btreating\s+physician'?s?\s+case[- ]by[- ]case\s+clinical\s+judg?ment\b",
        ),
        who_patterns=(
            r"\bfixed\s+6[- ]month\b",
            r"\brecommends?\s+against\s+extending\b",
            r"\bdo\s+not\s+extend\b",
        ),
        us_patterns=(
            r"\bcavitation\b[^.]{0,80}\b(?:positive\s+culture|2\s+months)\b[^.]{0,80}\bextend",
            r"\bextend(?:ed)?\s+(?:the\s+)?continuation\s+phas"
            r"e\s+by\s+(?:an\s+)?(?:additional\s+)?3\s+months\b",
            r"\b(?:7|nine|9)[- ]month\b[^.]{0,30}\bcontinuation\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-009",
        domain="resistance",
        divergence_class="consensus_divergence",
        is_critical=True,
        axis_description=(
            "TPT for FQ-susceptible MDR/RR-TB contacts: fixed standardized regimen "
            "vs conditional/individualized."
        ),
        consensus_patterns=(
            r"\b6[\s-]*months?\b[^.]{0,40}\b(?:daily\s+)?levofloxacin\b",
            r"\blevofloxacin\b[^.]{0,40}\b(?:standard(?:ized)?|routine|fixed)\b",
            r"\b(?:standard(?:ized)?|routine|fixed)\b[^.]{0,40}\blevofloxacin\b",
            r"\b(?:6lfx|6\s*lfx)\b",
        ),
        us_patterns=(
            r"\bconditional(?:ly)?\s+recommend",
            r"\bobservation\s+alone\b",
            r"\bindividuali[sz]ed\b[^.]{0,60}\b(?:fluoroqu"
            r"inolone|regimen)\b[^.]{0,60}\bsource\s+case\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-010",
        domain="prevention",
        divergence_class="national_adaptation",
        is_critical=True,
        axis_description=(
            "TPT for household contacts >=5y: standard/undeferred vs "
            "conditional-with-testing-desirable vs confirmed-LTBI-treatment framing."
        ),
        ntep_patterns=(
            r"\bmust\s+not\s+be\s+deferred\b",
            r"\bstandard\s+practice\b[^.]{0,60}\b(?:tpt|preventive\s+treatment)\b",
            r"\btesting\s+(?:is\s+)?(?:desirable|optional)\b[^.]{0,60}\bnot\s+(?:be\s+)?deferred\b",
        ),
        who_patterns=(
            r"\bmay\s+be\s+given\b[^.]{0,60}\b(?:tpt|tb\s+preventive\s+treatment)\b",
            r"\bconditional(?:ly)?\s+appropriate\b",
            r"\bconfirmation\s+of\s+(?:tb\s+infection|tbi)\b[^.]{0,60}\bdesirable\b",
            r"\b(?:tbi|tb\s+infection)\s+(?:confirmation|test(?:ing)?)\b[^.]{0,60}\bdesirable\b",
        ),
        us_patterns=(
            r"\bconfirm(?:ed)?\s+(?:latent\s+tb\s+infection"
            r"|ltbi)\b[^.]{0,60}\b(?:before|then\s+treat)\b",
            r"\btreatment\s+of\s+(?:confirmed\s+)?(?:latent\s+tb\s+infection|ltbi)\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-011",
        domain="prevention",
        divergence_class="consensus_divergence",
        is_critical=False,
        axis_description="TPT for PLHIV: started empirically without a positive TBI test.",
        consensus_patterns=(
            r"\b(?:tbi\s+test(?:ing)?|tst|igra)\b[^.]{0,60}\bnot\s+(?"
            r":a\s+)?(?:requirement|required|prerequisite|necessary)\b",
            r"\bwithout\s+(?:requiring|need(?:ing)?\s+for)\b[^.]{0,60}\b(?:tbi|tst|igra)\b",
            r"\bempirical(?:ly)?\b[^.]{0,60}\btpt\b",
        ),
        us_patterns=(
            r"\b(?:tst|igra)\b[^.]{0,40}\bpositive\b[^.]{0,60}\bbefore\s+(?:starting|initiat)",
            r"\bpositive\b[^.]{0,40}\b(?:tst|igra)\b[^.]{0,60}\bbefore\s+(?:starting|initiat)",
            r"\bconfirm(?:ed|ing)?\b[^.]{0,60}\b(?:tst|igra|"
            r"tbi)\b[^.]{0,60}\bbefore\s+(?:starting|initiat)",
            r"\bcontingent\s+on\s+a\s+confirmed\s+positive\s+tbi\s+test\b",
            r"\bframed\s+around\s+treatment\s+of\s+confirmed\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-012",
        domain="prevention",
        divergence_class="consensus_divergence",
        is_critical=False,
        axis_description="1HP regimen: available programmatic TPT option vs not offered.",
        consensus_patterns=(
            r"\b1hp\b",
            r"\bone[- ]month\b[^.]{0,40}\b(?:rifapentine|isoniazid)\b",
            r"\b28\s+daily\s+doses\b",
        ),
        us_patterns=(
            r"\b1hp\b[^.]{0,50}\bnot\b[^.]{0,20}\b(?:establ"
            r"ished|recommended|listed|standard|available)\b",
            r"\bnot\s+(?:among|one\s+of)\s+(?:the\s+)?recommended\s+regimens\b",
            r"\bdo\s+not\s+include\s+1hp\b",
            r"\b1hp\b[^.]{0,80}\bnot\s+(?:among|include)",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-016",
        domain="differential",
        divergence_class="national_adaptation",
        is_critical=False,
        axis_description=(
            "Active case-finding: routine national program vs prevalence-threshold-gated "
            "vs passive contact investigation."
        ),
        ntep_patterns=(
            r"\b(?:routine|systematic)\b[^.]{0,20}\bcase[- ]find",
            r"\bhouse[- ]to[- ]house\b",
            r"\bmandated\s+national\s+program\b",
            r"\bstanding\s+national\s+program\s+policy\b",
            r"\b(?:not|without|rather\s+than)\b[^.]{0,40}\bthreshold[- ]gated\b",
            r"\bunconditional\b[^.]{0,60}\b(?:case[- ]find|contact)",
            r"\b(?:case[- ]find|contact)[^.]{0,60}\bunconditional\b",
            r"\bstanding,?\s+unconditional\s+program\s+activity\b",
            r"\bnot\s+contingent\s+on\b[^.]{0,60}\bprevalence\b",
            r"\bopportunistic\s+screening\b",
        ),
        who_patterns=(
            r"\b0\.5\s*%\b",
            r"\bprevalence\b[^.]{0,60}\bthreshold\b",
            r"\bthreshold\b[^.]{0,60}\bprevalence\b",
            r"\bconditionally\s+appropriate\b",
            r"\bconditional\b[^.]{0,60}\bscreening\b[^.]{0,60}\bprevalence\b",
        ),
        us_patterns=(
            r"\bcontact\s+investigation\b[^.]{0,60}\b(?:index\s"
            r"+case|known\s+(?:adult|adolescent|tb\s+contact))\b",
            r"\bpassive\s+case[- ]find",
            r"\bpassive\b[^.]{0,20}\bcontact[- ]investigation[- ]driven\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-017",
        domain="monitoring",
        divergence_class="national_adaptation",
        is_critical=False,
        axis_description=(
            "Referral triage: standardized quantified thresholds vs general "
            "decentralization direction vs individualized judgment."
        ),
        ntep_patterns=(
            r"\bspo2\b[^.]{0,10}<\s*94",
            r"\brespiratory\s+rate\b[^.]{0,10}>\s*24",
            r"\bred[- ]flag\b",
            r"\bmandat(?:e|ed|ory|es)\b[^.]{0,60}\b(?:escalat|referral)",
            r"\bindependently\s+meets?\b[^.]{0,40}\b(?:red[- ]flag|quantified\s+red[- ]flag)\b",
        ),
        who_patterns=(
            r"\bdecentrali[sz](?:ation|ed)\b",
            r"\bambulatory\b[^.]{0,40}\bcare\b",
        ),
        us_patterns=(
            # Excludes cases where the surrounding text explicitly attributes
            # the individualized-judgment framing to WHO itself (real
            # vignette phrasing: "...individualized clinical judgment...
            # there is no WHO-specified quantified threshold... decentralized
            # care") -- without this, that WHO-attributed sentence reads as
            # both sides at once and gets marked hedged. See RUBRIC_SPEC.md.
            r"\bindividuali[sz]ed\s+(?:clinical\s+)?judg?ment\b(?!.{0,120"
            r"}\bwho[- ](?:specified|recommend)|.{0,120}\bwho'?s\s+own\b)",
            r"\bcase[- ]by[- ]case\b[^.]{0,60}\b(?:hospitali[sz]ation|referral)\b",
            r"\b(?:hospitali[sz]ation|referral)\b[^.]{0,60}\bcase[- ]by[- ]case\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-019",
        domain="comorbidity",
        divergence_class="consensus_divergence",
        is_critical=False,
        axis_description="Cotrimoxazole preventive therapy: universal for HIV+ TB vs CD4-gated.",
        consensus_patterns=(
            r"\bcotrimoxazole\b[^.]{0,80}\bregardless\s+of\b[^.]{0,20}\bcd4\b",
            r"\ball\s+hiv[- ]positive\s+tb\s+patients\b[^.]{0,40}\bcotrimoxazole\b",
        ),
        us_patterns=(
            r"\bcd4\b[^.]{0,20}<\s*200\b",
            r"\bcd4\s+count(?:s)?\s+(?:below|under|less\s+than)\s+200\b",
            r"\bcotrimoxazole\b[^.]{0,60}\bcd4\b[^.]{0,20}(?:200|threshold)",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-020",
        domain="treatment",
        divergence_class="national_adaptation",
        is_critical=False,
        axis_description=(
            "Pediatric non-severe DS-TB regimen duration: 4-month vs standard "
            "6-month regardless of severity."
        ),
        ntep_patterns=(
            r"\b6[- ]months?\b[^.]{0,40}\b(?:2hrze|4hre|regimen)\b",
            r"\b(?:2hrze\s*/?\s*4hre|2hrze\s*\+\s*4hre)\b",
            r"\bsame\s+duration\b[^.]{0,40}\b(?:adult|regardless\s+of\s+severity)\b",
        ),
        who_patterns=(
            r"\b4[- ]months?\s+regimen\b",
            r"\b2hrz\(?e\)?\s*/?\s*2hr\b",
            r"\bnon[- ]severe\b[^.]{0,60}\b4[- ]month\b",
            r"\bshine\s+trial\b",
        ),
    )
)

_register(
    ClauseAssertion(
        divergence_id="DIV-021",
        domain="diagnosis",
        divergence_class="national_adaptation",
        is_critical=False,
        axis_description=(
            "Pediatric bacteriologically-unconfirmed TB diagnosis: unstructured clinical "
            "judgment vs structured scored algorithm."
        ),
        ntep_patterns=(
            r"\bunstructured\s+clinical\s+judg?ment\b",
            r"\bclinician'?s?\s+synthesis\b",
            r"\btrial\s+of\s+antibiotics\b[^.]{0,60}\b(?:clinical\s+judg?ment|imaging)\b",
            r"\bclinical\s+judg?ment\b[^.]{0,80}\bclinically[- ]diagnosed\b",
            r"\bclinically[- ]diagnosed\s+tb\b",
            r"\bwithout\s+a\s+defined,?\s+weighted\s+scoring\s+tool\b",
        ),
        who_patterns=(
            r"\bintegrated\s+treatment[- ]decision\s+algorithm\b",
            r"\bscored\s+(?:diagnostic\s+)?(?:tool|algorithm)\b",
            r"\bweighted\s+scor(?:e|ing)\b",
            r"\bflow\s+chart\b[^.]{0,60}\bscore",
            r"\bstructured\s+integrated\s+treatment[- ]decision\s+algorithm\b",
        ),
    )
)


assert set(CLAUSE_ASSERTIONS) == {
    "DIV-001", "DIV-002", "DIV-003", "DIV-004", "DIV-005", "DIV-006", "DIV-007",
    "DIV-008", "DIV-009", "DIV-010", "DIV-011", "DIV-012", "DIV-016", "DIV-017",
    "DIV-019", "DIV-020", "DIV-021",
}, "CLAUSE_ASSERTIONS must cover exactly the 17 non-dropped divergence rows"
