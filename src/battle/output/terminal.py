from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich import box
from ..storage import RunManifest


def _overall(cell: dict) -> float:
    r = cell.get("rubric", {})
    return (r.get("ac_completeness", 0) + r.get("code_style", 0) + r.get("code_quality", 0)
            + r.get("security", 0) + r.get("bugs", 0)) / 5


def print_results(manifest: RunManifest) -> None:
    console = Console()

    # Aggregate cells by (plugin_id, model) — average across run_index
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for cell in manifest.cells:
        grouped[(cell["plugin_id"], cell["model"])].append(cell)

    table = Table(
        title=f"Battle Results — {manifest.test_name} | Run {manifest.run_id}",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Plugin", style="bold cyan")
    table.add_column("Model", style="dim")
    table.add_column("Overall", justify="center")
    table.add_column("AC", justify="center")
    table.add_column("Style", justify="center")
    table.add_column("Quality", justify="center")
    table.add_column("Security", justify="center")
    table.add_column("Bugs", justify="center")
    table.add_column("ESLint Errs", justify="center")
    table.add_column("Cost $", justify="right")

    for (plugin_id, model), cells in sorted(grouped.items()):
        def avg(fn):
            return sum(fn(c) for c in cells) / len(cells)

        overall = avg(_overall)
        color = "green" if overall >= 8 else "yellow" if overall >= 6 else "red"

        table.add_row(
            plugin_id,
            model,
            f"[{color}]{overall:.1f}[/{color}]",
            f"{avg(lambda c: c.get('rubric', {}).get('ac_completeness', 0)):.1f}",
            f"{avg(lambda c: c.get('rubric', {}).get('code_style', 0)):.1f}",
            f"{avg(lambda c: c.get('rubric', {}).get('code_quality', 0)):.1f}",
            f"{avg(lambda c: c.get('rubric', {}).get('security', 0)):.1f}",
            f"{avg(lambda c: c.get('rubric', {}).get('bugs', 0)):.1f}",
            str(int(avg(lambda c: c.get('static', {}).get('error_count', 0)))),
            f"${avg(lambda c: c.get('cost_usd', 0)):.3f}",
        )

    console.print(table)
    console.print(f"\nTotal cost: [bold]${manifest.total_cost_usd:.3f}[/bold]")
