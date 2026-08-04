from check_anonymity import load_blocklist, scan_file


def test_load_blocklist_skips_comments_and_blanks(tmp_path):
    path = tmp_path / "blocklist.txt"
    path.write_text("# comment\n\nRiverside High\nSpringfield\n", encoding="utf-8")
    assert load_blocklist(path) == ["Riverside High", "Springfield"]


def test_scan_file_flags_case_insensitive_match(tmp_path):
    target = tmp_path / "vignette.json"
    target.write_text('{"note": "seen at riverside high clinic"}', encoding="utf-8")
    hits = scan_file(target, ["Riverside High"])
    assert len(hits) == 1
    assert hits[0][1] == "Riverside High"


def test_scan_file_no_match(tmp_path):
    target = tmp_path / "vignette.json"
    target.write_text('{"note": "a rural district clinic"}', encoding="utf-8")
    assert scan_file(target, ["Riverside High"]) == []
