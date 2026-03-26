from dataclasses import dataclass


@dataclass
class TestTemplate:
    name: str
    description: str
    prompt: str
    acceptance_criteria: list[str]


_TEMPLATES: dict[str, TestTemplate] = {}


def register_template(t: TestTemplate) -> TestTemplate:
    _TEMPLATES[t.name] = t
    return t


def get_template(name: str) -> TestTemplate:
    if name not in _TEMPLATES:
        raise KeyError(f"Unknown test template '{name}'. Available: {list(_TEMPLATES)}")
    return _TEMPLATES[name]
