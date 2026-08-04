import json
from pathlib import Path

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
