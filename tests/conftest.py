import pytest
from pathlib import Path

@pytest.fixture
def tmp_battle_home(tmp_path, monkeypatch):
    """Override BATTLE_HOME to a temp dir for tests."""
    monkeypatch.setenv("BATTLE_HOME", str(tmp_path))
    return tmp_path
