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


def test_every_row_in_the_table_grounds_at_least_one_vignette():
    """Task 3: same intent as test_every_divergence_row_grounds_at_least_one_vignette
    above, phrased against the table directly rather than derived ids, so a
    row added to divergence_table.json without a DIVERGENCE_MAP update fails
    loudly. Every row still in the table survived Task 1's convergence
    triage (nothing here is a dropped/converged row -- those never made it
    into divergence_table.json in the first place)."""
    table = load_divergence_table()
    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))
    used_ids: set[str] = set()
    for cell in cells:
        used_ids.update(row["id"] for row in divergence_rows_for(cell, table))
    for row_id in table:
        assert row_id in used_ids, f"{row_id} grounds no vignette in the stratification plan"


def test_consensus_adaptation_cell_ratio_within_tolerance_of_target():
    """Task 3: roughly 75% of cells should ground primarily in
    consensus_divergence rows (the primary dataset for the reframed study)
    and roughly 25% in national_adaptation rows (secondary). 'Primarily'
    means the majority divergence_class among a cell's actually-selected
    grounding rows, not just the requested primary_divergence_class tag --
    this checks what generation would actually be grounded in, not merely
    what the stratification plan asked for."""
    table = load_divergence_table()
    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))

    consensus_primary = 0
    for cell in cells:
        rows = divergence_rows_for(cell, table)
        classes = [row["divergence_class"] for row in rows]
        consensus_count = classes.count("consensus_divergence")
        adaptation_count = classes.count("national_adaptation")
        if consensus_count >= adaptation_count:
            consensus_primary += 1

    fraction = consensus_primary / len(cells)
    assert 0.65 <= fraction <= 0.85, (
        f"{consensus_primary}/{len(cells)} ({fraction:.0%}) cells ground primarily in "
        f"consensus_divergence rows -- outside the [65%, 85%] tolerance band around "
        f"the 75% target"
    )
