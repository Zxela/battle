import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from battle.runner import CellResult, run_cell
from battle.adapters.baseline import BaselineAdapter


def make_mock_result(cost=0.05, result_text="done", num_turns=3):
    from claude_agent_sdk import ResultMessage
    msg = MagicMock(spec=ResultMessage)
    msg.total_cost_usd = cost
    msg.result = result_text
    msg.num_turns = num_turns
    return msg


@pytest.mark.asyncio
async def test_run_cell_returns_cell_result(tmp_path):
    adapter = BaselineAdapter()

    async def fake_query(*args, **kwargs):
        yield make_mock_result()

    with patch("battle.runner.query", fake_query):
        result = await run_cell(
            adapter=adapter,
            model="claude-sonnet-4-6",
            prompt="build something",
            run_index=0,
        )

    assert isinstance(result, CellResult)
    assert result.plugin_id == "baseline"
    assert result.model == "claude-sonnet-4-6"
    assert result.cost_usd == 0.05
    assert result.num_turns == 3
    assert result.error is None


@pytest.mark.asyncio
async def test_run_cell_captures_artifacts(tmp_path):
    adapter = BaselineAdapter()
    captured_cwd = {}

    async def fake_query(*args, **kwargs):
        # Write a file in the cell's cwd
        cwd = kwargs.get("options").cwd
        os.makedirs(cwd, exist_ok=True)
        with open(os.path.join(cwd, "index.tsx"), "w") as f:
            f.write("export default function App() {}")
        captured_cwd["path"] = cwd
        yield make_mock_result()

    with patch("battle.runner.query", fake_query):
        result = await run_cell(
            adapter=adapter,
            model="claude-sonnet-4-6",
            prompt="build something",
            run_index=0,
            artifact_base_dir=str(tmp_path),
        )

    assert "index.tsx" in result.artifact_files
    assert result.artifact_dir != ""
    assert os.path.exists(os.path.join(result.artifact_dir, "index.tsx"))


@pytest.mark.asyncio
async def test_run_cell_handles_error(tmp_path):
    adapter = BaselineAdapter()

    async def fake_query_error(*args, **kwargs):
        raise RuntimeError("SDK failure")
        yield  # make it an async generator

    with patch("battle.runner.query", fake_query_error):
        result = await run_cell(
            adapter=adapter,
            model="claude-sonnet-4-6",
            prompt="build something",
            run_index=0,
        )

    assert result.error is not None
    assert "SDK failure" in result.error


@pytest.mark.asyncio
async def test_run_cell_cleans_up_temp_dir():
    adapter = BaselineAdapter()
    created_cwd = []

    async def fake_query(*args, **kwargs):
        cwd = kwargs.get("options").cwd
        created_cwd.append(cwd)
        yield make_mock_result()

    with patch("battle.runner.query", fake_query):
        await run_cell(
            adapter=adapter,
            model="claude-sonnet-4-6",
            prompt="test",
            run_index=0,
        )

    assert created_cwd, "query was called"
    assert not os.path.exists(created_cwd[0]), "temp dir should be cleaned up"
