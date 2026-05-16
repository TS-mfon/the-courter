from courter_shared.judges import load_judge_profile, load_judge_profiles, select_judges


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
