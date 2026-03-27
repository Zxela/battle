import json
import os
import subprocess
from dataclasses import dataclass


@dataclass
class StaticResult:
    error_count: int
    warning_count: int
    tool: str = "eslint"
    ran: bool = True


def run_eslint(artifact_dir: str) -> StaticResult:
    """Run ESLint on all JS/TS files in artifact_dir. Returns counts."""
    if not artifact_dir or not os.path.isdir(artifact_dir):
        return StaticResult(error_count=0, warning_count=0, ran=False)

    js_extensions = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
    js_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(artifact_dir)
        for f in files
        if os.path.splitext(f)[1] in js_extensions
        and "node_modules" not in root
    ]

    if not js_files:
        return StaticResult(error_count=0, warning_count=0, ran=False)

    # Prevent option injection from filenames starting with '-'
    safe_files = [f if not f.startswith("-") else "./" + f for f in js_files]

    try:
        result = subprocess.run(
            ["npx", "eslint", "--format=json", "--no-eslintrc",
             "--rule", '{"no-undef":"warn","no-unused-vars":"warn","no-console":"off"}',
             "--", *safe_files],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=artifact_dir,
        )
        if not result.stdout.strip():
            return StaticResult(error_count=0, warning_count=0)

        data = json.loads(result.stdout)
        total_errors = sum(f.get("errorCount", 0) for f in data)
        total_warnings = sum(f.get("warningCount", 0) for f in data)
        return StaticResult(error_count=total_errors, warning_count=total_warnings)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return StaticResult(error_count=0, warning_count=0, ran=False)
