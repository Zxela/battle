from claude_agent_sdk import ClaudeAgentOptions
from .base import PluginAdapter, register_adapter


@register_adapter
class BaselineAdapter(PluginAdapter):
    """No-plugin control cell."""

    @property
    def plugin_id(self) -> str:
        return "baseline"

    def get_options(self, model: str, cwd: str) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            cwd=cwd,
            model=model,
            permission_mode="bypassPermissions",
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        )
