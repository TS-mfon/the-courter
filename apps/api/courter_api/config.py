from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env.test")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env.test"), extra="ignore")

    bot_token: str | None = Field(default=None, alias="BOT_TOKEN")
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, alias="SUPABASE_KEY")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    onesignal_api_key: str | None = Field(default=None, alias="ONESIGNAL_API_KEY")
    treasury_wallet: str = Field(default="0x5905c9Dea6Ae52AA0947D8F7F218263889eDfC4E", alias="TREASURY_WALLET")
    operational_wallet: str | None = Field(default=None, alias="OPERATIONAL_WALLET")
    genlayer_private_key: str | None = Field(default=None, alias="GENLAYER_PRIVATE_KEY")
    genlayer_operator_private_key: str | None = Field(default=None, alias="GENLAYER_OPERATOR_PRIVATE_KEY")
    genlayer_network: str = Field(default="testnet-bradbury", alias="GENLAYER_NETWORK")
    genlayer_contract_network: str = Field(default="studionet", alias="GENLAYER_CONTRACT_NETWORK")
    genlayer_payment_network: str = Field(default="testnet-bradbury", alias="GENLAYER_PAYMENT_NETWORK")
    genlayer_account_password: str | None = Field(default=None, alias="GENLAYER_ACCOUNT_PASSWORD")
    genlayer_standard_court_address: str | None = Field(default=None, alias="GENLAYER_STANDARD_COURT_ADDRESS")
    genlayer_inner_court_address: str | None = Field(default=None, alias="GENLAYER_INNER_COURT_ADDRESS")
    genlayer_appeal_court_address: str | None = Field(default=None, alias="GENLAYER_APPEAL_COURT_ADDRESS")
    genlayer_shadow_council_address: str | None = Field(default=None, alias="GENLAYER_SHADOW_COUNCIL_ADDRESS")
    payment_verification_mode: str = Field(default="receipt", alias="PAYMENT_VERIFICATION_MODE")
    bradbury_payment_rpc_primary: str = Field(default="https://zksync-os-testnet-genlayer.zksync.dev", alias="BRADBURY_PAYMENT_RPC_PRIMARY")
    bradbury_payment_rpc_fallback: str = Field(default="https://rpc.bradbury.genlayer.com", alias="BRADBURY_PAYMENT_RPC_FALLBACK")
    payment_explorer_base_url: str = Field(default="https://zksync-os-testnet-genlayer.explorer.zksync.dev", alias="PAYMENT_EXPLORER_BASE_URL")
    cors_allowed_origins: str = Field(default="http://172.236.110.179:3000", alias="CORS_ALLOWED_ORIGINS")
    cors_allow_origin_regex: str | None = Field(default=r"https://.*\.vercel\.app", alias="CORS_ALLOW_ORIGIN_REGEX")
    courter_api_url: str = Field(default="http://172.236.110.179:8001", alias="COURTER_API_URL")
    telegram_poll_timeout_seconds: int = Field(default=30, alias="TELEGRAM_POLL_TIMEOUT_SECONDS")
    telegram_poll_interval_seconds: int = Field(default=2, alias="TELEGRAM_POLL_INTERVAL_SECONDS")
    admin_secret: str = Field(default="rottwiller123", alias="ADMIN_SECRET")
    max_upload_bytes: int = Field(default=8_000_000, alias="MAX_UPLOAD_BYTES")


@lru_cache
def get_settings() -> Settings:
    return Settings()
