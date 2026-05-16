from __future__ import annotations

from typing import Any


def audit(
    action: str,
    *,
    actor_type: str = "system",
    actor_id: str = "system",
    entity_type: str = "system",
    entity_id: str = "",
    severity: str = "info",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from .repository import repo

    return repo.add_audit_log(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=severity,
        metadata=metadata or {},
    )
