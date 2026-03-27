import json
from dataclasses import asdict
from ..storage import RunManifest


def manifest_to_json(manifest: RunManifest) -> str:
    return json.dumps(asdict(manifest), indent=2)
