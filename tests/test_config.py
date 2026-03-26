import json
import pytest
from battle.config import Config


def test_empty_config(tmp_battle_home):
    cfg = Config()
    assert cfg.list_plugins() == {}


def test_register_and_resolve(tmp_battle_home, tmp_path):
    plugin_dir = tmp_path / "superpowers"
    plugin_dir.mkdir()
    cfg = Config()
    cfg.register("superpowers", str(plugin_dir))
    assert cfg.resolve("superpowers") == str(plugin_dir)


def test_resolve_unknown_raises(tmp_battle_home):
    cfg = Config()
    with pytest.raises(KeyError, match="superpowers"):
        cfg.resolve("superpowers")


def test_resolve_absolute_path_passthrough(tmp_battle_home, tmp_path):
    plugin_dir = tmp_path / "myplugin"
    plugin_dir.mkdir()
    cfg = Config()
    assert cfg.resolve(str(plugin_dir)) == str(plugin_dir)


def test_config_persists(tmp_battle_home, tmp_path):
    plugin_dir = tmp_path / "homerun"
    plugin_dir.mkdir()
    cfg = Config()
    cfg.register("homerun", str(plugin_dir))
    # Create a new Config instance — should reload from disk
    cfg2 = Config()
    assert cfg2.resolve("homerun") == str(plugin_dir)
