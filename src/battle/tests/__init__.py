from .base import TestTemplate, get_template, register_template
# Import to trigger registration
from . import spa, mobile, tooling

__all__ = ["TestTemplate", "get_template", "register_template"]
