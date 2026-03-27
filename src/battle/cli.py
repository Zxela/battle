import argparse
import asyncio
from pathlib import Path

from .config import Config
from .evaluators.llm_judge import RubricScore, score_cell
from .evaluators.static import run_eslint
from .orchestrator import MatrixConfig, run_matrix
from .output import manifest_to_html, manifest_to_json, print_results
from .storage import RunStorage
from .tests.base import get_template


def cli_register(name: str, path: str) -> None:
    cfg = Config()
    cfg.register(name, path)
    print(f"Registered plugin '{name}' at {path}")


def cli_list() -> None:
    cfg = Config()
    plugins = cfg.list_plugins()
    if not plugins:
        print("No plugins registered. Use: battle register <name> <path>")
        return
    for name, path in plugins.items():
        exists = "✓" if Path(path).exists() else "✗ (not found)"
        print(f"  {name}: {path} {exists}")



def cli_run(
    plugins: list[str],
    models: list[str],
    test_name: str,
    runs: int,
    judge_model: str,
    output: str,
    ci: bool = False,
    threshold: float = 6.0,
    sequential: bool = False,
) -> None:
    cfg = Config()
    template = get_template(test_name)

    # Filter out 'baseline' — it's always auto-included by the orchestrator
    plugins = [p for p in plugins if p != "baseline"]

    # Resolve plugin paths
    plugin_paths = {}
    for name in plugins:
        try:
            plugin_paths[name] = cfg.resolve(name)
        except KeyError:
            print(f"Error: Plugin '{name}' not registered. Run: battle register {name} <path-or-repo>")
            return

    storage = RunStorage()
    run_id = storage.new_run(
        plugin_names=plugins,
        models=models,
        test_name=test_name,
    )
    artifact_dir = storage.artifact_dir(run_id)

    mode = "sequential" if sequential else "parallel"
    print(f"Starting battle run {run_id} ({mode})")
    print(f"Plugins: {plugins + ['baseline']}  Models: {models}  Runs/cell: {runs}")

    matrix_config = MatrixConfig(
        plugin_names=plugins,
        plugin_paths=plugin_paths,
        models=models,
        prompt=template.prompt,
        runs_per_cell=runs,
        artifact_base_dir=artifact_dir,
    )

    async def _run_and_evaluate() -> None:
        results = await run_matrix(matrix_config, sequential=sequential)
        print(f"Completed {len(results)} cells. Evaluating...")
        for cell in results:
            try:
                rubric = await score_cell(
                    artifact_dir=cell.artifact_dir,
                    acceptance_criteria=template.acceptance_criteria,
                    judge_model=judge_model,
                )
            except Exception as e:
                print(f"  Judge failed for {cell.plugin_id}/{cell.model}: {e}")
                rubric = RubricScore(
                    ac_completeness=1, code_style=1, code_quality=1,
                    security=1, bugs=1, rationale=f"Judge error: {e}",
                )

            static = run_eslint(artifact_dir=cell.artifact_dir or "")
            storage.record_cell(run_id, cell, rubric, static)

    asyncio.run(_run_and_evaluate())
    manifest = storage.load_manifest(run_id)

    # Output
    formats = output.split(",") if output != "all" else ["terminal", "html", "json"]
    if "terminal" in formats:
        print_results(manifest)
    if "json" in formats:
        json_path = Path(artifact_dir).parent / "report.json"
        json_path.write_text(manifest_to_json(manifest))
        print(f"JSON saved to {json_path}")
    if "html" in formats:
        html_path = Path(artifact_dir).parent / "report.html"
        html_path.write_text(manifest_to_html(manifest))
        print(f"HTML report saved to {html_path}")

    if ci:
        _check_ci_threshold(manifest, threshold)


def _check_ci_threshold(manifest, threshold: float) -> None:
    from collections import defaultdict
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for cell in manifest.cells:
        grouped[(cell["plugin_id"], cell["model"])].append(cell)

    failures = []
    for (plugin_id, model), cells in grouped.items():
        overall = sum(
            (c["rubric"]["ac_completeness"] + c["rubric"]["code_style"]
             + c["rubric"]["code_quality"] + c["rubric"]["security"]
             + c["rubric"]["bugs"]) / 5
            for c in cells
        ) / len(cells)
        if overall < threshold:
            failures.append(f"  {plugin_id}/{model}: {overall:.1f} < {threshold}")

    if failures:
        print(f"\n[CI] {len(failures)} cell(s) below threshold {threshold}:")
        for f in failures:
            print(f)
        sys.exit(1)
    else:
        print(f"\n[CI] All cells passed threshold {threshold}. ✓")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="battle",
        description="Benchmark Claude Code plugins head-to-head",
    )
    subparsers = parser.add_subparsers(dest="command")

    # battle register <name> <path>
    reg = subparsers.add_parser("register", help="Register a plugin by name and local path")
    reg.add_argument("name", help="Plugin name (e.g. superpowers)")
    reg.add_argument("path", help="Absolute path to cloned plugin repo")

    # battle list
    subparsers.add_parser("list", help="List registered plugins")

    # battle run (default)
    run_p = subparsers.add_parser("run", help="Run a battle")
    run_p.add_argument("--plugins", default="", help="Comma-separated plugin names or paths (baseline always included)")
    run_p.add_argument("--models", default="claude-sonnet-4-6", help="Comma-separated model IDs")
    run_p.add_argument("--test", default="spa", help="Test template name (spa, mobile, tooling)")
    run_p.add_argument("--runs", type=int, default=1, help="Runs per cell (default: 1)")
    run_p.add_argument("--judge-model", default="claude-opus-4-6", help="Model used as judge")
    run_p.add_argument("--output", default="all", help="Output formats: terminal,html,json or all")
    run_p.add_argument("--ci", action="store_true", help="Exit non-zero if any cell scores below --threshold")
    run_p.add_argument("--threshold", type=float, default=6.0, help="Minimum acceptable overall score (default: 6.0)")
    run_p.add_argument("--sequential", action="store_true", help="Run cells one at a time instead of in parallel")

    # Allow `battle --plugins ...` as shorthand for `battle run --plugins ...`
    parser.add_argument("--plugins", help="Comma-separated plugin names or paths (shorthand for 'battle run')")
    parser.add_argument("--models", default="claude-sonnet-4-6", help=argparse.SUPPRESS)
    parser.add_argument("--test", help=argparse.SUPPRESS, default="spa")
    parser.add_argument("--runs", type=int, help=argparse.SUPPRESS, default=1)
    parser.add_argument("--judge-model", help=argparse.SUPPRESS, default="claude-opus-4-6")
    parser.add_argument("--output", help=argparse.SUPPRESS, default="all")
    parser.add_argument("--ci", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--threshold", type=float, help=argparse.SUPPRESS, default=6.0)
    parser.add_argument("--sequential", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.command == "register":
        cli_register(args.name, args.path)
    elif args.command == "list":
        cli_list()
    elif args.command == "run" or (args.command is None and args.plugins):
        plugins = [p.strip() for p in args.plugins.split(",")]
        models = [m.strip() for m in args.models.split(",")]
        cli_run(plugins, models, args.test, args.runs, args.judge_model, args.output,
                ci=args.ci, threshold=args.threshold)
    elif args.command == "run" or (args.command is None and args.plugins is not None):
        plugins = [p.strip() for p in args.plugins.split(",") if p.strip()] if args.plugins else []
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        if not models:
            parser.error("--models must specify at least one model")
        if args.runs < 1:
            parser.error("--runs must be at least 1")
        cli_run(plugins, models, args.test, args.runs, args.judge_model, args.output, args.sequential)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
