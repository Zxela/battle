import pytest
from battle.storage import RunStorage, RunManifest
from battle.runner import CellResult
from battle.evaluators.llm_judge import RubricScore
from battle.evaluators.static import StaticResult


def make_cell_result(plugin_id="baseline", model="claude-sonnet-4-6"):
    return CellResult(
        plugin_id=plugin_id, model=model, run_index=0,
        result_text="done", cost_usd=0.02, num_turns=3,
        artifact_files=["index.tsx"], artifact_dir="", error=None,
    )


def make_rubric():
    return RubricScore(
        ac_completeness=8, code_style=7, code_quality=8,
        security=9, bugs=8, rationale="Good"
    )


def make_static():
    return StaticResult(error_count=2, warning_count=5)


def test_new_run_creates_directory(tmp_battle_home):
    storage = RunStorage()
    run_id = storage.new_run(
        plugin_names=["superpowers"],
        models=["claude-sonnet-4-6"],
        test_name="spa",
    )
    assert run_id is not None
    assert len(run_id) > 8


def test_new_run_creates_artifact_dir(tmp_battle_home):
    storage = RunStorage()
    run_id = storage.new_run(["sp"], ["m"], "spa")
    import os
    assert os.path.isdir(storage.artifact_dir(run_id))


def test_record_and_load_manifest(tmp_battle_home):
    storage = RunStorage()
    run_id = storage.new_run(["superpowers"], ["claude-sonnet-4-6"], "spa")
    storage.record_cell(run_id, make_cell_result(), make_rubric(), make_static())
    manifest = storage.load_manifest(run_id)
    assert manifest.run_id == run_id
    assert len(manifest.cells) == 1
    assert manifest.cells[0]["plugin_id"] == "baseline"
    assert manifest.cells[0]["rubric"]["ac_completeness"] == 8
    assert manifest.cells[0]["static"]["error_count"] == 2


def test_total_cost_accumulates(tmp_battle_home):
    storage = RunStorage()
    run_id = storage.new_run(["sp"], ["m"], "spa")
    storage.record_cell(run_id, make_cell_result("baseline"), make_rubric(), make_static())
    storage.record_cell(run_id, make_cell_result("superpowers"), make_rubric(), make_static())
    manifest = storage.load_manifest(run_id)
    assert manifest.total_cost_usd == pytest.approx(0.04, rel=0.01)


def test_list_runs_returns_ids(tmp_battle_home):
    storage = RunStorage()
    id1 = storage.new_run(["sp"], ["m1"], "spa")
    id2 = storage.new_run(["hr"], ["m1"], "spa")
    runs = storage.list_runs()
    assert id1 in runs
    assert id2 in runs


def test_manifest_persists_across_instances(tmp_battle_home):
    storage1 = RunStorage()
    run_id = storage1.new_run(["sp"], ["m"], "spa")
    storage1.record_cell(run_id, make_cell_result(), make_rubric(), make_static())

    storage2 = RunStorage()
    manifest = storage2.load_manifest(run_id)
    assert len(manifest.cells) == 1
