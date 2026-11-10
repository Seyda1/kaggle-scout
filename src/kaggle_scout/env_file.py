"""Minimal reader for local KEY=VALUE environment files."""

import os
from collections.abc import MutableMapping
from pathlib import Path


def read_env_file(path: Path) -> dict[str, str]:
    """Return KEY=VALUE pairs from a file, or an empty dict if it is missing."""
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key.removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def load_env_file(
    path: Path,
    environ: MutableMapping[str, str] | None = None,
) -> None:
    """Copy file values into the environment without overriding existing ones."""
    target = os.environ if environ is None else environ
    for key, value in read_env_file(path).items():
        target.setdefault(key, value)
