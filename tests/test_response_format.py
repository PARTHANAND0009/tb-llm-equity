from tb_equity.response_format import check_parseable

GOOD_NUMBERED = """
1. Ranked differential diagnosis: Pulmonary TB is most likely given...
2. The single next diagnostic step: obtain a sputum sample for NAAT.
3. Initial management plan: start standard first-line therapy pending results.
"""

GOOD_LABELED_NO_NUMBERS = """
Differential diagnosis: pulmonary TB most likely, given the history.
Next diagnostic step: gastric aspirate for molecular testing.
Management plan: begin standard four-drug therapy.
"""

GOOD_STEP_STYLE = """
Step 1: Differential -- TB, pneumonia, malignancy.
Step 2: Order sputum NAAT.
Step 3: Start empiric therapy while awaiting results.
"""

BAD_UNSTRUCTURED_PROSE = (
    "This patient likely has tuberculosis given the cough and weight loss, "
    "so a sputum test would help confirm before starting treatment."
)

BAD_OUT_OF_ORDER = """
3. Management plan: start therapy.
1. Differential diagnosis: TB most likely.
2. Next diagnostic step: sputum NAAT.
"""

BAD_EMPTY = ""

BAD_WHITESPACE_ONLY = "   \n\n   "


def test_numbered_response_is_parseable():
    result = check_parseable(GOOD_NUMBERED)
    assert result.parseable
    assert all(result.sections_found)


def test_labeled_response_without_numbers_is_parseable():
    result = check_parseable(GOOD_LABELED_NO_NUMBERS)
    assert result.parseable


def test_step_n_style_response_is_parseable():
    result = check_parseable(GOOD_STEP_STYLE)
    assert result.parseable
    assert result.numbered_sections_found >= 2


def test_unstructured_prose_is_not_parseable():
    result = check_parseable(BAD_UNSTRUCTURED_PROSE)
    assert not result.parseable


def test_out_of_order_sections_fall_back_to_numbered_marker_check():
    # Section labels present but not in order -- still parseable because
    # it has >=2 numbered markers, which is the intentionally loose half
    # of the check (real models sometimes number correctly but reorder or
    # rename sections).
    result = check_parseable(BAD_OUT_OF_ORDER)
    assert result.parseable
    assert result.numbered_sections_found >= 2


def test_empty_response_is_not_parseable():
    result = check_parseable(BAD_EMPTY)
    assert not result.parseable
    assert result.reason == "empty response"


def test_whitespace_only_response_is_not_parseable():
    result = check_parseable(BAD_WHITESPACE_ONLY)
    assert not result.parseable


def test_meditron_style_thinking_wrapper_with_labeled_sections_is_parseable():
    """Continued-pretrained/reasoning-style models sometimes wrap the

    answer in a "## Thinking ... ## Final Response" block (e.g.
    HuatuoGPT-o1's documented format) -- the checker should still find the
    three labeled sections wherever they land in the text.
    """
    text = """
    ## Thinking
    The cough and weight loss over three weeks suggest TB, though
    pneumonia and malignancy remain on the differential.

    ## Final Response
    1. Ranked differential diagnosis: TB most likely, then bacterial
       pneumonia, then malignancy.
    2. The single next diagnostic step: sputum NAAT.
    3. Initial management plan: start first-line therapy pending confirmation.
    """
    result = check_parseable(text)
    assert result.parseable
