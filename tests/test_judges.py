import json
from pathlib import Path

import pytest

from courter_shared.judges import load_judge_profile, load_judge_profiles, select_judges
from courter_shared.paths import resolve_data_dir


def test_justice_ratio_profile_exists() -> None:
    profile = load_judge_profile("justice_ratio")
    assert profile["name"] == "Justice Ratio"
    assert profile["rationality_weight"] == 0.98


def test_judge_registry_includes_justice_ratio() -> None:
    names = {profile["name"] for profile in load_judge_profiles()}
    assert "Justice Ratio" in names


def test_prefer_rational_selects_justice_ratio() -> None:
    judges = select_judges(count=1, prefer_rational=True)
    assert judges[0]["name"] == "Justice Ratio"


def test_appeal_can_exclude_original_judge() -> None:
    judges = select_judges(count=10, excluded_ids={"justice_ratio"})
    assert all(judge["id"] != "justice_ratio" for judge in judges)


def test_judges_can_load_from_env_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "courter-fixture"
    judges_dir = root / "judges"
    laws_dir = root / "laws"
    judges_dir.mkdir(parents=True)
    laws_dir.mkdir(parents=True)
    with (judges_dir / "fixture_judge.json").open("w", encoding="utf-8") as handle:
        json.dump({"name": "Fixture Judge", "style": "Analytical"}, handle)

    monkeypatch.setenv("COURTER_DATA_ROOT", str(root))

    profiles = load_judge_profiles()

    assert [profile["name"] for profile in profiles] == ["Fixture Judge"]
    assert resolve_data_dir("judges") == judges_dir.resolve()
