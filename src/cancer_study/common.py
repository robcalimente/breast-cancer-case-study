from __future__ import annotations

import hashlib
import json
from pathlib import Path


def root() -> Path:
    for path in [Path.cwd(), *Path.cwd().parents]:
        if (path / "protocol.json").is_file() and (path / "pyproject.toml").is_file():
            return path
    raise RuntimeError("Run from the study repository or a subdirectory.")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
