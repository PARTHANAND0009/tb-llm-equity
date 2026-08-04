import shutil
from pathlib import Path

import tb_equity.render as render_mod

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "example_vignettes"


def _seed_vignettes(tmp_path, monkeypatch, version="test-fixture"):
    monkeypatch.setattr(render_mod, "VIGNETTES_ROOT", tmp_path)
    dest = tmp_path / version
    dest.mkdir(parents=True)
    for f in FIXTURE_DIR.glob("VIG-*.json"):
        shutil.copy(f, dest / f.name)
    return version


def test_load_vignettes_reads_and_sorts(tmp_path, monkeypatch):
    version = _seed_vignettes(tmp_path, monkeypatch)
    vignettes = render_mod.load_vignettes(version)
    assert [v.id for v in vignettes] == ["VIG-901", "VIG-902"]


def test_group_by_presentation_type(tmp_path, monkeypatch):
    version = _seed_vignettes(tmp_path, monkeypatch)
    vignettes = render_mod.load_vignettes(version)
    groups = render_mod.group_by_presentation_type(vignettes)
    assert set(groups) == {"pulmonary", "comorbid"}
    assert len(groups["pulmonary"]) == 1
    assert len(groups["comorbid"]) == 1


def test_composition_summary(tmp_path, monkeypatch):
    version = _seed_vignettes(tmp_path, monkeypatch)
    vignettes = render_mod.load_vignettes(version)
    summary = render_mod.composition_summary(vignettes)
    assert ("comorbid", "india_high", 1) in summary
    assert ("pulmonary", "india_high", 1) in summary


def test_resolved_critique_flag_summary_empty_without_critiques_dir(tmp_path, monkeypatch):
    _seed_vignettes(tmp_path, monkeypatch)
    assert render_mod.resolved_critique_flag_summary("test-fixture") == []
