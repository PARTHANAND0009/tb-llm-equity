from build_stratification_plan import (
    GROUPS,
    TOTAL_HOLDOUT,
    TOTAL_VIGNETTES,
    WESTERN_CONTROL_COUNT,
    allocate,
    build_cells,
)


def test_allocate_sums_to_total_and_matches_weights_roughly():
    result = allocate(20, [40, 35, 25, 20, 30])
    assert sum(result) == 20
    assert result == [5, 5, 3, 3, 4]


def test_allocate_handles_equal_weights():
    assert allocate(9, [1, 1, 1]) == [3, 3, 3]


def test_build_cells_total_and_holdout_counts():
    cells = build_cells()
    assert len(cells) == TOTAL_VIGNETTES
    assert sum(1 for c in cells if c["holdout"]) == TOTAL_HOLDOUT


def test_build_cells_matches_target_composition():
    cells = build_cells()
    india_high_counts = {}
    western_counts = 0
    for c in cells:
        if c["burden_class"] == "india_high":
            pt = c["presentation_type"]
            india_high_counts[pt] = india_high_counts.get(pt, 0) + 1
        else:
            western_counts += 1

    expected = {g["presentation_type"]: g["count"] for g in GROUPS}
    assert india_high_counts == expected
    assert western_counts == WESTERN_CONTROL_COUNT


def test_comorbid_cells_get_a_subtype_and_significant_burden():
    cells = build_cells()
    comorbid_cells = [c for c in cells if c["presentation_type"] == "comorbid"]
    assert comorbid_cells
    for c in comorbid_cells:
        assert c["subtype"] in {"tb_diabetes", "tb_hiv", "undernutrition"}
        assert c["comorbidity_burden"] == "significant"


def test_non_comorbid_cells_have_no_subtype_unless_drug_resistant():
    cells = build_cells()
    for c in cells:
        if c["presentation_type"] in {"pulmonary", "extrapulmonary"}:
            assert c["subtype"] is None
        if c["presentation_type"] == "drug_resistant":
            assert c["subtype"] in {"rifampicin_mono_resistant", "mdr_tb", "pre_xdr_tb"}


def test_cell_ids_are_unique():
    cells = build_cells()
    ids = [c["cell_id"] for c in cells]
    assert len(ids) == len(set(ids))
