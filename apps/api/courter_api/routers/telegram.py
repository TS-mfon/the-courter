from fastapi import APIRouter

router = APIRouter()


@router.post("/webhook")
def webhook(payload: dict) -> dict[str, str]:
    return {"status": "received", "command_layer": "telegram"}
