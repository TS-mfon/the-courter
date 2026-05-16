from fastapi import APIRouter

from fastapi import Header, HTTPException

from ..config import get_settings
from ..services.evidence import ocr_status
from ..services.payments import payment_rpc_health
from ..services.repository import repo

router = APIRouter()


@router.get("/payment-audit")
def payment_audit(x_admin_secret: str | None = Header(default=None)) -> dict:
    if x_admin_secret != get_settings().admin_secret:
        raise HTTPException(status_code=401, detail="Admin auth required")
    return {"events": [event for event in repo.list_audit_logs() if event["action"].startswith("payment")]}


@router.get("/audit-logs")
def audit_logs(x_admin_secret: str | None = Header(default=None), limit: int = 200) -> dict:
    if x_admin_secret != get_settings().admin_secret:
        raise HTTPException(status_code=401, detail="Admin auth required")
    return {"events": repo.list_audit_logs(limit=limit)}


@router.get("/system-health")
def system_health(x_admin_secret: str | None = Header(default=None)) -> dict:
    if x_admin_secret != get_settings().admin_secret:
        raise HTTPException(status_code=401, detail="Admin auth required")
    settings = get_settings()
    warnings = []
    if not repo.db_ready():
        warnings.append("Supabase/PostgreSQL connection unavailable; using process memory fallback")
    if settings.operational_wallet and settings.operational_wallet.lower() == settings.treasury_wallet.lower():
        warnings.append("Treasury wallet equals operational wallet; separate before production")
    if not settings.genlayer_standard_court_address:
        warnings.append("Standard Court contract address missing")
    if not settings.genlayer_inner_court_address:
        warnings.append("Inner Court contract address missing")
    if not settings.genlayer_appeal_court_address:
        warnings.append("Appeal Court contract address missing")
    if not settings.genlayer_shadow_council_address:
        warnings.append("Shadow Council contract address missing")
    if not settings.onesignal_api_key:
        warnings.append("OneSignal API key missing")
    if not settings.bot_token:
        warnings.append("Telegram bot token missing")
    rpc_health = payment_rpc_health()
    ocr = ocr_status()
    backend_status = "healthy"
    database_status = "healthy" if repo.db_ready() else "degraded"
    contracts_status = "healthy"
    for value in (
        settings.genlayer_standard_court_address,
        settings.genlayer_inner_court_address,
        settings.genlayer_appeal_court_address,
        settings.genlayer_shadow_council_address,
    ):
        if not value:
            contracts_status = "degraded"
            break
    latest_failures = [event for event in repo.list_audit_logs(limit=200) if event["severity"] in {"warning", "critical"}][:20]
    return {
        "db_ready": repo.db_ready(),
        "warnings": warnings,
        "subsystems": {
            "backend": {"status": backend_status},
            "database": {"status": database_status},
            "ocr": ocr,
            "payment_rpcs": rpc_health,
            "genlayer_contracts": {
                "status": contracts_status,
                "network": settings.genlayer_contract_network,
                "standard_court": settings.genlayer_standard_court_address,
                "inner_court": settings.genlayer_inner_court_address,
                "appeal_court": settings.genlayer_appeal_court_address,
                "shadow_council": settings.genlayer_shadow_council_address,
            },
            "payment_verifier": {
                "status": "healthy" if settings.payment_verification_mode != "development" else "degraded",
                "mode": settings.payment_verification_mode,
                "treasury_wallet": settings.treasury_wallet,
                "explorer_base_url": settings.payment_explorer_base_url,
            },
        },
        "latest_failures": latest_failures,
    }


@router.get("/cases")
def admin_cases(x_admin_secret: str | None = Header(default=None)) -> dict:
    if x_admin_secret != get_settings().admin_secret:
        raise HTTPException(status_code=401, detail="Admin auth required")
    return {"cases": repo.list_cases(public_only=False)}
