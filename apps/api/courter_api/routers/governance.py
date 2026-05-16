from fastapi import APIRouter

router = APIRouter()


@router.get("/analytics")
def analytics() -> dict:
    return {
        "participation_rates": [],
        "overturn_statistics": [],
        "council_activity": [],
        "reputation_rankings": [],
    }
