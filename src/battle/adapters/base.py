from abc import ABC, abstractmethod
from claude_agent_sdk import ClaudeAgentOptions


class PluginAdapter(ABC):
    """Base class for all plugin adapters."""

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Short identifier, e.g. 'superpowers', 'homerun', 'baseline'."""

    @abstractmethod
    def get_options(self, model: str, cwd: str) -> ClaudeAgentOptions:
        """Return ClaudeAgentOptions for a single cell run."""


_ADAPTER_REGISTRY: dict[str, type[PluginAdapter]] = {}


def register_adapter(cls: type[PluginAdapter]) -> type[PluginAdapter]:
    """Class decorator to register an adapter."""
    # plugin_id is an abstract property; instantiate to get the value for registry
    _ADAPTER_REGISTRY[cls.__name__] = cls  # store by class name temporarily
    return cls


def get_adapter(name: str, plugin_path: str | None) -> PluginAdapter:
    """Resolve adapter by plugin_id name."""
    # Build id->class map on demand
    id_map = {}
    for cls in _ADAPTER_REGISTRY.values():
        try:
            if plugin_path is not None:
                instance = cls(plugin_path=plugin_path)
            else:
                instance = cls()
            id_map[instance.plugin_id] = cls
        except Exception:
            pass
    if name not in id_map:
        raise ValueError(f"Unknown adapter '{name}'. Available: {list(id_map)}")
    cls = id_map[name]
    if plugin_path is not None:
        return cls(plugin_path=plugin_path)
    return cls()
