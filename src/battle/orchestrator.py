import asyncio
from dataclasses import dataclass

from .adapters.base import get_adapter
from .adapters.baseline import BaselineAdapter
from .runner import CellResult, run_cell


@dataclass
class MatrixConfig:
    plugin_names: list[str]         # e.g. ["superpowers", "homerun"]
    plugin_paths: dict[str, str]    # name -> local path
    models: list[str]
    prompt: str
    runs_per_cell: int
    artifact_base_dir: str


async def run_matrix(config: MatrixConfig) -> list[CellResult]:
    """Run all (plugin × model × run_index) cells in parallel."""
    tasks = []

    # Build adapter list: baseline always first, then named plugins
    adapters = [BaselineAdapter()]
    for name in config.plugin_names:
        path = config.plugin_paths.get(name)
        adapters.append(get_adapter(name, plugin_path=path))

    for adapter in adapters:
        for model in config.models:
            for run_index in range(config.runs_per_cell):
                tasks.append(
                    run_cell(
                        adapter=adapter,
                        model=model,
                        prompt=config.prompt,
                        run_index=run_index,
                        artifact_base_dir=config.artifact_base_dir,
                    )
                )

    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)
