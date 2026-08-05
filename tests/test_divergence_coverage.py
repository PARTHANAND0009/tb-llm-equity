import json
from pathlib import Path

import generate_vignettes
from generate_vignettes import DIVERGENCE_MAP, divergence_rows_for, load_divergence_table

REPO_ROOT = Path(__file__).resolve().parents[1]
STRATIFICATION_PLAN_PATH = REPO_ROOT / "data" / "vignettes" / "stratification_plan.json"


def test_every_divergence_row_grounds_at_least_one_vignette():
    """Task 3: the union of divergence_ids used across the stratification plan
    must equal the full set of row ids in divergence_table.json -- no row is
    left ungrounded."""
    table = load_divergence_table()
    all_row_ids = set(table.keys())

    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))
    used_ids: set[str] = set()
    for cell in cells:
        rows = divergence_rows_for(cell, table)
        used_ids.update(row["id"] for row in rows)

    missing = all_row_ids - used_ids
    assert not missing, f"divergence rows with no grounded vignette: {sorted(missing)}"


def test_divergence_map_only_references_real_row_ids():
    table = load_divergence_table()
    all_row_ids = set(table.keys())
    for ids in DIVERGENCE_MAP.values():
        unknown = set(ids) - all_row_ids
        assert not unknown, f"DIVERGENCE_MAP references unknown row ids: {sorted(unknown)}"


def test_every_stratification_cell_resolves_to_at_least_one_divergence_row():
    table = load_divergence_table()
    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))
    for cell in cells:
        rows = divergence_rows_for(cell, table)
        label = f"{cell['presentation_type']}/{cell['subtype']}"
        assert rows, f"cell {cell['cell_id']} ({label}) has no grounding rows"


def test_no_cell_grounds_in_more_than_three_divergence_rows():
    """Task 2 Bug A: one clinical case can't meaningfully probe more than a
    few decision points at once, and a failure needs to be attributable to a
    specific row. Grounding is capped at MAX_DIVERGENCE_IDS_PER_VIGNETTE."""
    table = load_divergence_table()
    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))
    for cell in cells:
        rows = divergence_rows_for(cell, table)
        assert len(rows) <= generate_vignettes.MAX_DIVERGENCE_IDS_PER_VIGNETTE, (
            f"cell {cell['cell_id']} grounds in {len(rows)} rows "
            f"(> {generate_vignettes.MAX_DIVERGENCE_IDS_PER_VIGNETTE}): "
            f"{[r['id'] for r in rows]}"
        )


def test_no_cell_grounds_in_a_row_outside_its_age_band():
    """Task 2 Bug B: a row must never ground a vignette whose age_band isn't
    in that row's own applicable_age_bands (e.g. adult weight-band dosing
    grounding a 7-year-old's case)."""
    table = load_divergence_table()
    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))
    for cell in cells:
        rows = divergence_rows_for(cell, table)
        for row in rows:
            applicable = row.get("applicable_age_bands", [])
            assert cell["age_band"] in applicable, (
                f"cell {cell['cell_id']} (age_band={cell['age_band']!r}) is grounded in "
                f"{row['id']}, whose applicable_age_bands is {applicable} -- age mismatch"
            )
