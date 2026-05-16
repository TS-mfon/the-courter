from __future__ import annotations

import secrets

users: dict[str, dict[str, str]] = {}


def create_identity(username: str) -> dict[str, str]:
    recovery_key = secrets.token_urlsafe(24)
    users[username] = {"username": username, "recovery_key": recovery_key}
    return {"username": username, "recovery_key": recovery_key}


def recover_identity(username: str, recovery_key: str) -> bool:
    user = users.get(username)
    return bool(user and user["recovery_key"] == recovery_key)
