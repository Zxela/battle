import json
import os
from pathlib import Path


def _battle_home() -> Path:
    home = os.environ.get("BATTLE_HOME")
    if home:
        return Path(home)
    return Path.home() / ".battle"


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

    def register(self, name: str, path: str) -> None:
        self._data[name] = path
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
