import json
import os
import re
import subprocess
from pathlib import Path


def _battle_home() -> Path:
    home = os.environ.get("BATTLE_HOME")
    if home:
        return Path(home)
    return Path.home() / ".battle"


def _is_github_shorthand(s: str) -> bool:
    """Return True if s looks like 'owner/repo' (not an absolute/relative path)."""
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", s))


class Config:
    def __init__(self):
        self._home = _battle_home()
        self._home.mkdir(parents=True, exist_ok=True)
        self._path = self._home / "plugins.json"
        self._data: dict[str, str] = {}
        if self._path.exists():
            self._data = json.loads(self._path.read_text())

    def _save(self):
        self._path.write_text(json.dumps(self._data, indent=2))

    def _clone_or_pull(self, name: str, repo: str) -> str:
        """Clone owner/repo to ~/.battle/plugins/<name>/, or pull if already cloned."""
        plugins_dir = self._home / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)
        dest = plugins_dir / name
        if dest.exists():
            subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"], check=True)
        else:
            url = f"https://github.com/{repo}.git"
            subprocess.run(["git", "clone", url, str(dest)], check=True)
        return str(dest)

    def register(self, name: str, path: str) -> None:
        if _is_github_shorthand(path):
            local_path = self._clone_or_pull(name, path)
        else:
            local_path = path
        self._data[name] = local_path
        self._save()

    def list_plugins(self) -> dict[str, str]:
        return dict(self._data)

    def resolve(self, name_or_path: str) -> str:
        # Absolute paths pass through directly
        p = Path(name_or_path)
        if p.is_absolute() and p.exists():
            return str(p)
        if name_or_path in self._data:
            return self._data[name_or_path]
        raise KeyError(f"Plugin '{name_or_path}' not registered. Run: battle register {name_or_path} /path/to/plugin")
