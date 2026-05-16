from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .paths import resolve_data_dir


def judges_dir() -> Path:
    return resolve_data_dir("judges")


def load_judge_profile(name: str) -> dict[str, Any]:
    path = judges_dir() / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_judge_profiles() -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for path in sorted(judges_dir().glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            profile = json.load(handle)
            profile["id"] = path.stem
            profiles.append(profile)
    return profiles


def select_judges(
    count: int = 3,
    excluded_ids: set[str] | None = None,
    prefer_rational: bool = False,
) -> list[dict[str, Any]]:
    excluded_ids = excluded_ids or set()
    profiles = [judge for judge in load_judge_profiles() if judge["id"] not in excluded_ids]
    if prefer_rational:
        profiles = sorted(
            profiles,
            key=lambda judge: judge.get("rationality_weight", 0),
            reverse=True,
        )
        return profiles[:count]
    if len(profiles) <= count:
        return profiles
    return random.sample(profiles, count)
