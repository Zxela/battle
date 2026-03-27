from abc import ABC, abstractmethod
from claude_agent_sdk import ClaudeAgentOptions

# System prompt injected into all plugin cells.
# Superpowers' brainstorming skill has a HARD-GATE requiring user approval
# before proceeding. In an automated benchmark there is no human to respond,
# so Claude should act as both architect and approver: run through the full
# brainstorm/plan workflow autonomously, approve its own design, then implement.
BENCHMARK_SYSTEM = (
    "You are running in an automated benchmark evaluation with no human present. "
    "When a skill or workflow requires user approval, confirmation, or clarification, "
    "proceed autonomously — act as both the designer and the approver. "
    "Complete any brainstorming or planning steps yourself, approve your own plan, "
    "then implement immediately without waiting for external input."
)


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
    """Class decorator to register an adapter.

    Instantiates with no args to extract plugin_id for the lookup table.
    """
    try:
        instance = cls()
        _ADAPTER_REGISTRY[instance.plugin_id] = cls
    except Exception as exc:
        import warnings
        warnings.warn(f"Failed to register adapter {cls.__name__}: {exc}")
    return cls


class GenericPluginAdapter(PluginAdapter):
    """Adapter for any plugin not covered by a dedicated adapter class."""

    def __init__(self, name: str, plugin_path: str):
        self._name = name
        self._path = plugin_path

    @property
    def plugin_id(self) -> str:
        return self._name

    def get_options(self, model: str, cwd: str) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            cwd=cwd,
            model=model,
            system_prompt=BENCHMARK_SYSTEM,
            plugins=[{"type": "local", "path": self._path}],
            permission_mode="bypassPermissions",
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Skill"],
        )


def get_adapter(name: str, plugin_path: str | None) -> PluginAdapter:
    """Resolve adapter by plugin_id name.

    Falls back to GenericPluginAdapter for any name not covered by a registered
    adapter, as long as a plugin_path is provided.
    """
    if name in _ADAPTER_REGISTRY:
        cls = _ADAPTER_REGISTRY[name]
        if plugin_path is not None:
            return cls(plugin_path=plugin_path)
        return cls()

    # Fall back to generic adapter when a path is available
    if plugin_path is not None:
        return GenericPluginAdapter(name=name, plugin_path=plugin_path)

    raise ValueError(
        f"Unknown adapter '{name}' and no plugin_path provided. "
        f"Registered: {list(_ADAPTER_REGISTRY)}"
    )
