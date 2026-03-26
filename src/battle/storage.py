import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import _battle_home
from .evaluators.llm_judge import RubricScore
from .evaluators.static import StaticResult
from .runner import CellResult


@dataclass
class RunManifest:
    run_id: str
    timestamp: float
    plugin_names: list[str]
    models: list[str]
    test_name: str
    cells: list[dict]
    total_cost_usd: float = 0.0


class RunStorage:
    def __init__(self):
        self._runs_dir = _battle_home() / "runs"
        self._runs_dir.mkdir(parents=True, exist_ok=True)

    def new_run(self, plugin_names: list[str], models: list[str], test_name: str) -> str:
        run_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        run_dir = self._runs_dir / run_id
        run_dir.mkdir()
        (run_dir / "artifacts").mkdir()
        manifest = RunManifest(
            run_id=run_id,
            timestamp=time.time(),
            plugin_names=plugin_names,
            models=models,
            test_name=test_name,
            cells=[],
        )
        self._write_manifest(run_id, manifest)
        return run_id

    def artifact_dir(self, run_id: str) -> str:
        return str(self._runs_dir / run_id / "artifacts")

    def record_cell(
        self,
        run_id: str,
        cell: CellResult,
        rubric: RubricScore,
        static: StaticResult,
    ) -> None:
        manifest = self.load_manifest(run_id)
        manifest.cells.append({
            "plugin_id": cell.plugin_id,
            "model": cell.model,
            "run_index": cell.run_index,
            "cost_usd": cell.cost_usd,
            "num_turns": cell.num_turns,
            "error": cell.error,
            "rubric": asdict(rubric),
            "static": asdict(static),
        })
        manifest.total_cost_usd = sum(c["cost_usd"] for c in manifest.cells)
        self._write_manifest(run_id, manifest)

    def load_manifest(self, run_id: str) -> RunManifest:
        path = self._runs_dir / run_id / "manifest.json"
        data = json.loads(path.read_text())
        return RunManifest(**data)

    def list_runs(self) -> list[str]:
        return sorted(
            [d.name for d in self._runs_dir.iterdir() if d.is_dir()],
            reverse=True,
        )

    def _write_manifest(self, run_id: str, manifest: RunManifest) -> None:
        path = self._runs_dir / run_id / "manifest.json"
        path.write_text(json.dumps(asdict(manifest), indent=2))
