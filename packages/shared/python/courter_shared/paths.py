from __future__ import annotations

import os
from pathlib import Path


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def candidate_roots() -> list[Path]:
    roots: list[Path] = []
    for env_name in ("COURTER_DATA_ROOT", "COURTER_PROJECT_ROOT"):
        env_value = os.getenv(env_name, "").strip()
        if env_value:
            roots.append(Path(env_value))

    here = Path(__file__).resolve()
    roots.extend(here.parents)

    cwd = Path.cwd().resolve()
    roots.append(cwd)
    roots.extend(cwd.parents)

    for fallback in (Path("/opt/the-courter"), Path("/srv/the-courter")):
        roots.append(fallback)

    return _unique_paths(roots)


def resolve_project_root(*required_dirs: str) -> Path:
    for root in candidate_roots():
        if all((root / dirname).exists() for dirname in required_dirs):
            return root
    required = ", ".join(required_dirs) or "<none>"
    checked = ", ".join(str(path) for path in candidate_roots())
    raise FileNotFoundError(f"Unable to locate Courter project root with required paths: {required}. Checked: {checked}")


def resolve_data_dir(dirname: str) -> Path:
    return resolve_project_root(dirname) / dirname
