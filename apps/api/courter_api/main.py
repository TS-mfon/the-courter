from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import admin, appeals, auth, cases, evidence, governance, notifications, payments, retrieval, shadow_council, telegram, verdicts

app = FastAPI(title="The Courter API", version="0.1.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(retrieval.router, prefix="/retrieval", tags=["retrieval"])
app.include_router(verdicts.router, prefix="/verdicts", tags=["verdicts"])
app.include_router(appeals.router, prefix="/appeals", tags=["appeals"])
app.include_router(shadow_council.router, prefix="/shadow-council", tags=["shadow-council"])
app.include_router(governance.router, prefix="/governance", tags=["governance"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "the-courter"}
