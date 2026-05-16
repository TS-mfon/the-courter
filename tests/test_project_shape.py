from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_frontend_routes_exist() -> None:
    required = [
        "apps/web/app/page.tsx",
        "apps/web/app/file-case/page.tsx",
        "apps/web/app/courtroom/page.tsx",
        "apps/web/app/appeals/page.tsx",
        "apps/web/app/public-cases/page.tsx",
        "apps/web/app/shadow-council/page.tsx",
        "apps/web/app/judges/page.tsx",
        "apps/web/app/case/[id]/page.tsx",
        "apps/web/app/governance/analytics/page.tsx",
        "apps/web/app/internal/chamber/page.tsx",
    ]
    assert all((ROOT / path).exists() for path in required)


def test_required_contracts_exist() -> None:
    required = [
        "contracts/standard_court.py",
        "contracts/inner_court.py",
        "contracts/appeal_court.py",
        "contracts/shadow_council.py",
    ]
    assert all((ROOT / path).exists() for path in required)
