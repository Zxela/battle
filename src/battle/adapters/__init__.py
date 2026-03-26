from .base import PluginAdapter, get_adapter, register_adapter
from .baseline import BaselineAdapter
from .superpowers import SuperpowersAdapter
from .homerun import HomerunAdapter

__all__ = [
    "PluginAdapter", "get_adapter", "register_adapter",
    "BaselineAdapter", "SuperpowersAdapter", "HomerunAdapter",
]
