import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_anonymity import load_blocklist  # noqa: E402


def test_blocklist_does_not_contain_india():
    """RULE 3 targets identifying strings about the author, not the

    research subject. Arm 2 prompts state the patient is seen at a district
    hospital in India, and NTEP content is the substance of the study --
    blocklisting "India"/"Indian" would break the experimental design by
    flagging the study's own intentional content as a violation. See
    config/blocklist.txt's header comment.
    """
    terms = load_blocklist()
    lowered = [t.lower() for t in terms]
    assert "india" not in lowered
    assert "indian" not in lowered


def test_blocklist_has_entries():
    terms = load_blocklist()
    assert len(terms) >= 5
