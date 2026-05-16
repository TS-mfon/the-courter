from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SHARED_ROOT = os.path.join(PROJECT_ROOT, "packages", "shared", "python")
for candidate in (PROJECT_ROOT, SHARED_ROOT):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from apps.api.courter_api.config import get_settings  # noqa: E402
from courter_shared.judges import load_judge_profiles  # noqa: E402


COMMANDS = {
    "status": "Check the current status of a case. Usage: /status CASE-XXXX",
    "track": "Track a case ID and get the current public status. Usage: /track CASE-XXXX",
    "appeal": "Get appeal guidance for a case. Usage: /appeal CASE-XXXX",
    "verdict": "Get the verdict summary for a case. Usage: /verdict CASE-XXXX",
    "judges": "List the available judge personas.",
    "help": "Show available commands.",
}


def bot_token() -> str:
    token = os.getenv("BOT_TOKEN") or get_settings().bot_token
    if not token:
        raise RuntimeError("BOT_TOKEN is missing")
    return token


def courter_api_url() -> str:
    return (os.getenv("COURTER_API_URL") or get_settings().courter_api_url).rstrip("/")


def telegram_api_base() -> str:
    return f"https://api.telegram.org/bot{bot_token()}"


def _telegram_get(method: str, params: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    with httpx.Client(timeout=timeout) as client:
        response = client.get(f"{telegram_api_base()}/{method}", params=params or {})
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok", False):
            raise RuntimeError(f"Telegram API error for {method}: {payload}")
        return payload


def _telegram_post(method: str, json_payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{telegram_api_base()}/{method}", json=json_payload)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok", False):
            raise RuntimeError(f"Telegram API error for {method}: {payload}")
        return payload


def set_my_commands() -> None:
    payload = {
        "commands": [{"command": command, "description": description.split(".")[0]} for command, description in COMMANDS.items()]
    }
    _telegram_post("setMyCommands", payload)


def get_case(case_id: str) -> dict[str, Any]:
    with httpx.Client(timeout=30) as client:
        response = client.get(f"{courter_api_url()}/cases/{case_id}")
        response.raise_for_status()
        return response.json()


def get_verdict(case_id: str) -> dict[str, Any]:
    with httpx.Client(timeout=30) as client:
        response = client.get(f"{courter_api_url()}/verdicts/{case_id}")
        response.raise_for_status()
        return response.json()


def _truncate(text: str, limit: int = 3500) -> str:
    return text if len(text) <= limit else f"{text[:limit - 3]}..."


def help_text() -> str:
    lines = ["The Courter Telegram companion"]
    for command, description in COMMANDS.items():
        lines.append(f"/{command} - {description}")
    return "\n".join(lines)


def judges_text() -> str:
    profiles = load_judge_profiles()
    lines = ["Judges available in The Courter:"]
    for profile in profiles[:8]:
        lines.append(f"- {profile['name']}: {profile.get('style', 'Judicial profile')}")
    if len(profiles) > 8:
        lines.append(f"...and {len(profiles) - 8} more.")
    return "\n".join(lines)


def status_text(case_id: str) -> str:
    record = get_case(case_id)
    return _truncate(
        "\n".join(
            [
                f"Case: {record['id']}",
                f"Status: {record['status']}",
                f"Court: {record['court_type']}",
                f"Country: {record['country']}",
                f"Dispute: {record['dispute_type']}",
                f"Summary: {record.get('plain_english_verdict', 'No public summary yet.')}",
            ]
        )
    )


def verdict_text(case_id: str) -> str:
    verdict_response = get_verdict(case_id)
    verdict = verdict_response.get("verdict") or {}
    headline = verdict.get("headline_verdict") or "Verdict pending"
    conclusion = verdict.get("final_conclusion") or "No final conclusion yet."
    winner = verdict.get("winner") or "unknown"
    confidence = verdict.get("confidence")
    return _truncate(
        "\n".join(
            [
                f"Case: {case_id}",
                f"Winner: {winner}",
                f"Confidence: {confidence}",
                headline,
                conclusion,
            ]
        )
    )


def appeal_text(case_id: str) -> str:
    return _truncate(
        "\n".join(
            [
                f"Appeal guidance for {case_id}:",
                "Use the Courter web app appeal flow.",
                "Appeal Court fee: 5 GEN.",
                "Provide your case ID, appeal grounds, sender wallet, and Bradbury payment transaction hash.",
            ]
        )
    )


def track_text(case_id: str) -> str:
    record = get_case(case_id)
    return _truncate(f"Tracking {record['id']}. Current status: {record['status']}. Verdict summary: {record.get('plain_english_verdict', 'Pending')}")


def handle_command(text: str) -> str:
    command_line = (text or "").strip()
    if not command_line.startswith("/"):
        return "Unknown command. Use /help."
    parts = command_line.split(maxsplit=1)
    command = parts[0].lstrip("/").split("@", 1)[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    if command == "help":
        return help_text()
    if command == "judges":
        return judges_text()
    if command in {"status", "track", "appeal", "verdict"} and not arg:
        return COMMANDS[command]
    if command == "status":
        return status_text(arg)
    if command == "track":
        return track_text(arg)
    if command == "appeal":
        return appeal_text(arg)
    if command == "verdict":
        return verdict_text(arg)
    return "Unknown command. Use /help."


def send_message(chat_id: int, text: str) -> None:
    _telegram_post("sendMessage", {"chat_id": chat_id, "text": _truncate(text)})


def process_update(update: dict[str, Any]) -> None:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text") or ""
    if not chat_id or not text:
        return
    try:
        response = handle_command(text)
    except Exception as exc:
        response = f"The Courter bot hit an error: {exc}"
    send_message(chat_id, response)


def run_polling() -> None:
    settings = get_settings()
    timeout_seconds = int(os.getenv("TELEGRAM_POLL_TIMEOUT_SECONDS") or settings.telegram_poll_timeout_seconds)
    pause_seconds = int(os.getenv("TELEGRAM_POLL_INTERVAL_SECONDS") or settings.telegram_poll_interval_seconds)
    offset = 0
    me = _telegram_get("getMe", timeout=20)
    print(f"The Courter Telegram companion is configured for @{me['result']['username']}.", flush=True)
    set_my_commands()
    while True:
        try:
            updates = _telegram_get(
                "getUpdates",
                params={"offset": offset, "timeout": timeout_seconds},
                timeout=timeout_seconds + 10,
            )
            for update in updates.get("result", []):
                offset = max(offset, int(update["update_id"]) + 1)
                process_update(update)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"Polling error: {exc}", flush=True)
            time.sleep(pause_seconds)


if __name__ == "__main__":
    run_polling()
