from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

from ..config import get_settings


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._db_ready = False
        self.users: dict[str, dict[str, Any]] = {}
        self.cases: dict[str, dict[str, Any]] = {}
        self.payments: dict[str, dict[str, Any]] = {}
        self.audit_logs: list[dict[str, Any]] = []
        self.proposals: dict[str, dict[str, Any]] = {}
        self.council_members: dict[str, dict[str, Any]] = {
            "0x5905c9dea6ae52aa0947d8f7f218263889edfc4e": {
                "wallet": "0x5905c9Dea6Ae52AA0947D8F7F218263889eDfC4E",
                "display_name": "High Chancellor",
                "voting_weight": 10.4,
                "active": True,
                "joined_at": "2026-01-01T00:00:00Z",
            }
        }
        self._try_init_db()

    def _connect(self):
        if not self.settings.database_url:
            raise RuntimeError("DATABASE_URL missing")
        return psycopg.connect(self.settings.database_url, row_factory=dict_row, connect_timeout=5)

    def _try_init_db(self) -> None:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        create table if not exists courter_users (
                          username text primary key,
                          recovery_key text not null,
                          hidden_wallet text not null,
                          payload jsonb not null,
                          created_at timestamptz default now()
                        );
                        create table if not exists courter_cases (
                          id text primary key,
                          username text not null,
                          status text not null,
                          public boolean default true,
                          payload jsonb not null,
                          created_at timestamptz default now(),
                          updated_at timestamptz default now()
                        );
                        create table if not exists courter_payments (
                          tx_hash text primary key,
                          sender_wallet text not null,
                          court_type text not null,
                          amount_gen numeric not null,
                          payload jsonb not null,
                          consumed_at timestamptz default now()
                        );
                        create table if not exists courter_audit_logs (
                          id text primary key,
                          actor_type text not null,
                          actor_id text not null,
                          action text not null,
                          entity_type text not null,
                          entity_id text not null,
                          severity text not null,
                          metadata jsonb not null,
                          created_at timestamptz default now()
                        );
                        create table if not exists courter_council_members (
                          wallet text primary key,
                          display_name text not null,
                          voting_weight numeric not null,
                          active boolean not null,
                          joined_at timestamptz default now()
                        );
                        create table if not exists courter_council_proposals (
                          id text primary key,
                          case_id text not null,
                          status text not null,
                          payload jsonb not null,
                          created_at timestamptz default now(),
                          updated_at timestamptz default now()
                        );
                        """
                    )
                conn.commit()
            self._db_ready = True
        except Exception:
            self._db_ready = False

    def db_ready(self) -> bool:
        return self._db_ready

    def create_user(self, username: str) -> dict[str, Any]:
        recovery_key = f"COURTER-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        hidden_wallet = f"0x{secrets.token_hex(20)}"
        user = {
            "username": username,
            "recovery_key": recovery_key,
            "hidden_wallet": hidden_wallet,
            "created_at": now_iso(),
        }
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into courter_users (username, recovery_key, hidden_wallet, payload)
                        values (%s, %s, %s, %s)
                        on conflict (username) do update set payload = excluded.payload
                        """,
                        (username, recovery_key, hidden_wallet, json.dumps(user)),
                    )
                conn.commit()
        self.users[username] = user
        return user

    def get_user(self, username: str) -> dict[str, Any] | None:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("select payload from courter_users where username=%s", (username,))
                    row = cur.fetchone()
                    if row:
                        return row["payload"]
        return self.users.get(username)

    def save_case(self, case: dict[str, Any]) -> dict[str, Any]:
        case["updated_at"] = now_iso()
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into courter_cases (id, username, status, public, payload)
                        values (%s, %s, %s, %s, %s)
                        on conflict (id) do update set status=excluded.status, public=excluded.public,
                          payload=excluded.payload, updated_at=now()
                        """,
                        (
                            case["id"],
                            case["username"],
                            case["status"],
                            case.get("public", True),
                            json.dumps(case),
                        ),
                    )
                conn.commit()
        self.cases[case["id"]] = case
        return case

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("select payload from courter_cases where id=%s", (case_id,))
                    row = cur.fetchone()
                    if row:
                        return row["payload"]
        return self.cases.get(case_id)

    def list_cases(self, public_only: bool = False) -> list[dict[str, Any]]:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    if public_only:
                        cur.execute("select payload from courter_cases where public=true order by created_at desc")
                    else:
                        cur.execute("select payload from courter_cases order by created_at desc")
                    return [row["payload"] for row in cur.fetchall()]
        values = list(self.cases.values())
        if public_only:
            values = [case for case in values if case.get("public", True)]
        return sorted(values, key=lambda case: case.get("created_at", ""), reverse=True)

    def consume_payment(self, payment: dict[str, Any]) -> None:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into courter_payments (tx_hash, sender_wallet, court_type, amount_gen, payload)
                        values (%s, %s, %s, %s, %s)
                        """,
                        (
                            payment["tx_hash"].lower(),
                            payment["sender_wallet"],
                            payment["court_type"],
                            payment["amount_gen"],
                            json.dumps(payment),
                        ),
                    )
                conn.commit()
        self.payments[payment["tx_hash"].lower()] = payment

    def payment_consumed(self, tx_hash: str) -> bool:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("select tx_hash from courter_payments where tx_hash=%s", (tx_hash.lower(),))
                    return cur.fetchone() is not None
        return tx_hash.lower() in self.payments

    def add_audit_log(self, **event: Any) -> dict[str, Any]:
        entry = {
            "id": f"AUD-{secrets.token_hex(6).upper()}",
            "created_at": now_iso(),
            **event,
        }
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into courter_audit_logs
                        (id, actor_type, actor_id, action, entity_type, entity_id, severity, metadata)
                        values (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            entry["id"],
                            entry["actor_type"],
                            entry["actor_id"],
                            entry["action"],
                            entry["entity_type"],
                            entry["entity_id"],
                            entry["severity"],
                            json.dumps(entry["metadata"]),
                        ),
                    )
                conn.commit()
        self.audit_logs.append(entry)
        return entry

    def list_audit_logs(self, limit: int = 200) -> list[dict[str, Any]]:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("select * from courter_audit_logs order by created_at desc limit %s", (limit,))
                    return [dict(row) for row in cur.fetchall()]
        return list(reversed(self.audit_logs[-limit:]))

    def list_council_members(self) -> list[dict[str, Any]]:
        return list(self.council_members.values())

    def save_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into courter_council_proposals (id, case_id, status, payload)
                        values (%s, %s, %s, %s)
                        on conflict (id) do update set status=excluded.status, payload=excluded.payload, updated_at=now()
                        """,
                        (proposal["id"], proposal["case_id"], proposal["status"], json.dumps(proposal)),
                    )
                conn.commit()
        self.proposals[proposal["id"]] = proposal
        return proposal

    def list_proposals(self) -> list[dict[str, Any]]:
        if self._db_ready:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("select payload from courter_council_proposals order by created_at desc")
                    return [row["payload"] for row in cur.fetchall()]
        return list(self.proposals.values())


repo = Repository()
