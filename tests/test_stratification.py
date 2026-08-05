from build_stratification_plan import (
    COMPARATOR_CONTROL_COUNT,
    GROUPS,
    TOTAL_HOLDOUT,
    TOTAL_VIGNETTES,
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
    comparator_counts = 0
    for c in cells:
        if c["burden_class"] == "india_high":
            pt = c["presentation_type"]
            india_high_counts[pt] = india_high_counts.get(pt, 0) + 1
        else:
            comparator_counts += 1

    expected = {g["presentation_type"]: g["count"] for g in GROUPS}
    assert india_high_counts == expected
    assert comparator_counts == COMPARATOR_CONTROL_COUNT


def test_comorbid_cells_get_a_subtype_and_significant_burden():
    cells = build_cells()
    comorbid_cells = [c for c in cells if c["presentation_type"] == "comorbid"]
    assert comorbid_cells
    for c in comorbid_cells:
        assert c["subtype"] in {"tb_diabetes", "tb_hiv", "undernutrition"}
        assert c["comorbidity_burden"] == "significant"


def test_non_comorbid_cells_have_no_subtype_unless_drug_resistant_or_contact_management():
    cells = build_cells()
    for c in cells:
        if c["presentation_type"] in {"pulmonary", "extrapulmonary"}:
            assert c["subtype"] is None
        if c["presentation_type"] == "drug_resistant":
            assert c["subtype"] in {"rifampicin_mono_resistant", "mdr_tb", "pre_xdr_tb"}
        if c["presentation_type"] == "contact_management":
            assert c["subtype"] in {
                "household_contact_ds_tb",
                "household_contact_mdr_tb",
                "plhiv_tpt",
            }


def test_contact_management_cells_exist_for_both_burden_classes():
    cells = build_cells()
    contact_mgmt = [c for c in cells if c["presentation_type"] == "contact_management"]
    assert contact_mgmt
    assert any(c["burden_class"] == "india_high" for c in contact_mgmt)
    assert any(c["burden_class"] == "comparator_control" for c in contact_mgmt)


def test_cell_ids_are_unique():
    cells = build_cells()
    ids = [c["cell_id"] for c in cells]
    assert len(ids) == len(set(ids))


def test_every_comparator_control_cell_is_matched():
    cells = build_cells()
    comparator = [c for c in cells if c["burden_class"] == "comparator_control"]
    assert comparator
    assert all(c["matched_pair_id"] for c in comparator)


def test_matched_pairs_are_unique_and_same_presentation_type():
    cells = build_cells()
    by_id = {c["cell_id"]: c for c in cells}
    comparator = [c for c in cells if c["burden_class"] == "comparator_control"]
    targets = [c["matched_pair_id"] for c in comparator]
    assert len(targets) == len(set(targets))  # no india_high cell matched twice
    for c in comparator:
        partner = by_id[c["matched_pair_id"]]
        assert partner["burden_class"] == "india_high"
        assert partner["presentation_type"] == c["presentation_type"]


def test_matched_pairs_align_on_age_band_and_num_distractors():
    cells = build_cells()
    by_id = {c["cell_id"]: c for c in cells}
    comparator = [c for c in cells if c["burden_class"] == "comparator_control"]
    for c in comparator:
        partner = by_id[c["matched_pair_id"]]
        assert partner["age_band"] == c["age_band"]
        assert partner["num_distractors"] == c["num_distractors"]


def test_matched_india_high_cell_links_back_to_comparator_control_cell():
    cells = build_cells()
    by_id = {c["cell_id"]: c for c in cells}
    comparator = [c for c in cells if c["burden_class"] == "comparator_control"]
    for c in comparator:
        partner = by_id[c["matched_pair_id"]]
        assert partner["matched_pair_id"] == c["cell_id"]
