import pytest
from battle.adapters.base import get_adapter
from battle.adapters.baseline import BaselineAdapter
from battle.adapters.superpowers import SuperpowersAdapter
from battle.adapters.homerun import HomerunAdapter


def test_baseline_adapter_id():
    adapter = BaselineAdapter()
    assert adapter.plugin_id == "baseline"


def test_baseline_options_has_no_plugins():
    adapter = BaselineAdapter()
    opts = adapter.get_options(model="claude-sonnet-4-6", cwd="/tmp")
    # Should have no plugins list or empty plugins
    plugins = getattr(opts, "plugins", None)
    assert not plugins  # None or []


def test_baseline_options_uses_model():
    adapter = BaselineAdapter()
    opts = adapter.get_options(model="claude-opus-4-6", cwd="/tmp")
    assert opts.model == "claude-opus-4-6"


def test_superpowers_adapter_id(tmp_path):
    adapter = SuperpowersAdapter(plugin_path=str(tmp_path))
    assert adapter.plugin_id == "superpowers"


def test_superpowers_options_has_plugin(tmp_path):
    adapter = SuperpowersAdapter(plugin_path=str(tmp_path))
    opts = adapter.get_options(model="claude-sonnet-4-6", cwd="/tmp")
    assert opts.plugins is not None
    assert len(opts.plugins) == 1
    assert opts.plugins[0]["path"] == str(tmp_path)


def test_homerun_adapter_id(tmp_path):
    adapter = HomerunAdapter(plugin_path=str(tmp_path))
    assert adapter.plugin_id == "homerun"


def test_get_adapter_baseline():
    adapter = get_adapter("baseline", plugin_path=None)
    assert isinstance(adapter, BaselineAdapter)


def test_get_adapter_superpowers(tmp_path):
    adapter = get_adapter("superpowers", plugin_path=str(tmp_path))
    assert isinstance(adapter, SuperpowersAdapter)


def test_get_adapter_homerun(tmp_path):
    adapter = get_adapter("homerun", plugin_path=str(tmp_path))
    assert isinstance(adapter, HomerunAdapter)


def test_get_adapter_unknown_raises():
    with pytest.raises(ValueError, match="Unknown adapter"):
        get_adapter("unknown-plugin", plugin_path=None)
