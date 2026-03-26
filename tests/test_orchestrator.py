import pytest
from unittest.mock import patch
from battle.orchestrator import MatrixConfig, run_matrix
from battle.runner import CellResult


def make_cell_result(plugin_id, model, run_index=0):
    return CellResult(
        plugin_id=plugin_id, model=model, run_index=run_index,
        result_text="done", cost_usd=0.01, num_turns=2,
        artifact_files=[], artifact_dir="", error=None,
    )


@pytest.mark.asyncio
async def test_run_matrix_includes_baseline(tmp_path):
    config = MatrixConfig(
        plugin_names=["superpowers"],
        plugin_paths={"superpowers": str(tmp_path / "sp")},
        models=["claude-sonnet-4-6"],
        prompt="build something",
        runs_per_cell=1,
        artifact_base_dir=str(tmp_path),
    )

    async def fake_run_cell(adapter, model, prompt, run_index, artifact_base_dir):
        return make_cell_result(adapter.plugin_id, model, run_index)

    with patch("battle.orchestrator.run_cell", fake_run_cell):
        results = await run_matrix(config)

    plugin_ids = {r.plugin_id for r in results}
    assert "baseline" in plugin_ids
    assert "superpowers" in plugin_ids


@pytest.mark.asyncio
async def test_run_matrix_cell_count(tmp_path):
    """2 plugins + baseline = 3 adapters, 2 models, 3 runs = 18 cells."""
    config = MatrixConfig(
        plugin_names=["superpowers", "homerun"],
        plugin_paths={"superpowers": "/sp", "homerun": "/hr"},
        models=["claude-sonnet-4-6", "claude-opus-4-6"],
        prompt="build",
        runs_per_cell=3,
        artifact_base_dir=str(tmp_path),
    )

    async def fake_run_cell(adapter, model, prompt, run_index, artifact_base_dir):
        return make_cell_result(adapter.plugin_id, model, run_index)

    with patch("battle.orchestrator.run_cell", fake_run_cell):
        results = await run_matrix(config)

    assert len(results) == 18  # 3 adapters * 2 models * 3 runs


@pytest.mark.asyncio
async def test_run_matrix_no_named_plugins(tmp_path):
    """With no named plugins, only baseline runs."""
    config = MatrixConfig(
        plugin_names=[],
        plugin_paths={},
        models=["claude-sonnet-4-6"],
        prompt="build",
        runs_per_cell=1,
        artifact_base_dir=str(tmp_path),
    )

    async def fake_run_cell(adapter, model, prompt, run_index, artifact_base_dir):
        return make_cell_result(adapter.plugin_id, model, run_index)

    with patch("battle.orchestrator.run_cell", fake_run_cell):
        results = await run_matrix(config)

    assert len(results) == 1
    assert results[0].plugin_id == "baseline"
