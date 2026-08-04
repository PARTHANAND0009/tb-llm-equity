from tb_equity.manifest import REQUIRED_MANIFEST_FIELDS, validate_manifest


def test_complete_manifest_has_no_problems():
    manifest = {field: "placeholder" for field in REQUIRED_MANIFEST_FIELDS}
    assert validate_manifest(manifest) == []


def test_missing_field_is_reported():
    manifest = {field: "placeholder" for field in REQUIRED_MANIFEST_FIELDS if field != "seed"}
    problems = validate_manifest(manifest)
    assert len(problems) == 1
    assert "seed" in problems[0]
