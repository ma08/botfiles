"""
Shared notification utilities for Claude Code and Codex hooks.
"""
from __future__ import annotations

import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path
from shutil import which
from shlex import quote as shell_quote
from urllib.parse import quote as url_quote

import requests


_BOTFILES_ROOT = Path(__file__).resolve().parents[1]
_CLAUDE_HOOKS_DIR = _BOTFILES_ROOT / "claude" / "hooks"
_ENV_PATH = _BOTFILES_ROOT / "secrets" / "local" / "claude-hooks.rc"

_LOG_FILE = _CLAUDE_HOOKS_DIR / "hooks.log"


def _log(message: str) -> None:
    """Append a timestamped message to the log file."""
    timestamp = datetime.now().isoformat()
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def load_env(override: bool = False) -> None:
    """
    Load key=value pairs from the shared secrets rc file.

    Only basic KEY=VALUE and optional 'export KEY=VALUE' lines are supported.
    """
    if not _ENV_PATH.exists():
        return

    for line in _ENV_PATH.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()

        if "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        if override or key not in os.environ:
            os.environ[key] = value


load_env()


def get_latest_message_from_transcript(transcript_path_jsonl: str) -> str:
    try:
        messages = []
        with open(transcript_path_jsonl, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not messages:
            return ""

        last_message_dict = messages[-1].get("message", {})
        last_message_content_list = last_message_dict.get("content", [])

        curated_content = ""
        for content_item in last_message_content_list:
            if content_item.get("type") == "text":
                curated_content += content_item.get("text", "") + "\n"

        return curated_content.strip()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return ""


def get_config() -> dict:
    """Get configuration from environment variables."""
    return {
        "whatsapp_enabled": os.getenv("WHATSAPP_ENABLED", "false").lower() == "true",
        "whatsapp_token": os.getenv("WHATSAPP_TOKEN", ""),
        "phone_number_id": os.getenv("PHONE_NUMBER_ID", ""),
        "notify_phone_number": os.getenv("NOTIFY_PHONE_NUMBER", ""),
        "system_name": os.getenv("SYSTEM_NAME", ""),
        "zellij_web_enable_links": os.getenv("ZELLIJ_WEB_ENABLE_LINKS", "false").lower()
        == "true",
        "zellij_web_base_url": os.getenv("ZELLIJ_WEB_BASE_URL", "").strip(),
        "zellij_send_attach_command": os.getenv(
            "ZELLIJ_SEND_ATTACH_COMMAND", "true"
        ).lower()
        == "true",
    }


def get_system_name() -> str:
    """Get system name from SYSTEM_NAME env var, fallback to hostname."""
    system_name = os.getenv("SYSTEM_NAME", "")
    if system_name:
        return system_name
    return socket.gethostname()


def get_zellij_session_name() -> str:
    """Get zellij session name from environment, fallback to 'unknown'."""
    session_name = os.getenv("ZELLIJ_SESSION_NAME", "").strip()
    if session_name:
        return session_name
    return "unknown"


def build_context_header(system_name: str, session_name: str) -> str:
    """Build a compact context header for outbound chat notifications."""
    return f"[{system_name} | zj:{session_name}]"


def build_zellij_session_url(
    session_name: str,
    base_url: str,
    links_enabled: bool,
) -> str | None:
    """
    Build a direct zellij web URL for a session.

    Returns None when links are disabled, base URL is missing, or session is unknown.
    """
    if not links_enabled:
        return None

    normalized_base_url = base_url.strip().rstrip("/")
    if not normalized_base_url:
        return None

    if session_name == "unknown":
        return None

    encoded_session = url_quote(session_name, safe="")
    return f"{normalized_base_url}/{encoded_session}"


def build_zellij_attach_command(session_name: str) -> str | None:
    """Build a shell-safe zellij attach command for copy/paste in SSH terminals."""
    if session_name == "unknown":
        return None
    return f"zellij attach {shell_quote(session_name)}"


def send_local_notification(title: str, message: str) -> None:
    """
    Send a local macOS notification using terminal-notifier.

    Args:
        title: Notification title
        message: Notification body
    """
    if sys.platform != "darwin":
        _log("Local notification skipped (non-macOS)")
        return
    if which("terminal-notifier") is None:
        _log("Local notification skipped (terminal-notifier not found)")
        return

    safe_message = message.replace('"', '\\"')
    safe_title = title.replace('"', '\\"')
    os.system(
        f'terminal-notifier -message "{safe_message}" -title "{safe_title}" -sound default'
    )


def send_whatsapp_message(
    message: str,
    to_phone: str,
    token: str,
    phone_number_id: str,
) -> bool:
    """
    Send a WhatsApp message via Meta's Cloud API.
    """
    _log(f"WhatsApp: Sending to {to_phone}, phone_number_id={phone_number_id}")

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    to_phone_digits = to_phone.lstrip("+")
    sanitized_message = message.encode("utf-8", errors="replace").decode("utf-8")

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone_digits,
        "type": "text",
        "text": {"body": sanitized_message},
    }

    _log(f"WhatsApp: Payload to={to_phone_digits}, message_preview={sanitized_message[:100]}...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()

        _log(f"WhatsApp: Response status={response.status_code}, body={result}")

        if response.status_code == 200 and "messages" in result:
            _log("WhatsApp: Message sent successfully")
            return True
        error_msg = result.get("error", {}).get("message", str(result))
        _log(f"WhatsApp: API error - {error_msg}")
        print(f"WhatsApp API error: {error_msg}", file=sys.stderr)
        return False

    except requests.RequestException as e:
        _log(f"WhatsApp: Request exception - {e}")
        print(f"WhatsApp request failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        _log(f"WhatsApp: General exception - {e}")
        print(f"WhatsApp send failed: {e}", file=sys.stderr)
        return False


def send_notification(title: str, message: str, send_local: bool = True) -> None:
    """Send notification to all enabled channels (local + WhatsApp)."""
    _log(f"send_notification called: title={title}")

    if send_local:
        send_local_notification(title, message)
        _log("Local notification attempted")
    else:
        _log("Local notification disabled by caller")

    config = get_config()
    _log(f"Config: whatsapp_enabled={config['whatsapp_enabled']}")

    if not config["whatsapp_enabled"]:
        _log("WhatsApp not enabled, skipping")
        return

    if not all(
        [
            config["whatsapp_token"],
            config["phone_number_id"],
            config["notify_phone_number"],
        ]
    ):
        _log("WhatsApp enabled but missing required config")
        print(
            "WhatsApp enabled but missing required config (WHATSAPP_TOKEN, PHONE_NUMBER_ID, NOTIFY_PHONE_NUMBER)",
            file=sys.stderr,
        )
        return

    system_name = get_system_name()
    session_name = get_zellij_session_name()
    context_header = build_context_header(system_name, session_name)
    session_url = build_zellij_session_url(
        session_name=session_name,
        base_url=config["zellij_web_base_url"],
        links_enabled=config["zellij_web_enable_links"],
    )

    whatsapp_lines = [context_header, title, str(message).strip()]
    if config["zellij_web_enable_links"]:
        whatsapp_lines.append(f"Open Session: {session_url or 'n/a'}")

    whatsapp_message = "\n".join([line for line in whatsapp_lines if line])
    _log(
        "Sending WhatsApp: "
        f"system_name={system_name}, "
        f"session_name={session_name}, "
        f"links_enabled={config['zellij_web_enable_links']}, "
        f"to={config['notify_phone_number']}"
    )

    send_whatsapp_message(
        message=whatsapp_message,
        to_phone=config["notify_phone_number"],
        token=config["whatsapp_token"],
        phone_number_id=config["phone_number_id"],
    )

    # Send a second standalone message so it can be copied directly in SSH/Termius.
    if config["zellij_send_attach_command"]:
        attach_command = build_zellij_attach_command(session_name)
        if attach_command:
            _log("Sending WhatsApp attach command message")
            send_whatsapp_message(
                message=attach_command,
                to_phone=config["notify_phone_number"],
                token=config["whatsapp_token"],
                phone_number_id=config["phone_number_id"],
            )
