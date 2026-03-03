"""
Shared notification utilities for Claude Code and Codex hooks.
"""
from __future__ import annotations

import base64
import json
import os
import re
import socket
import sys
import uuid
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from shutil import which
from shlex import quote as shell_quote
from urllib.parse import quote as url_quote

import requests


_BOTFILES_ROOT = Path(__file__).resolve().parents[1]
_CLAUDE_HOOKS_DIR = _BOTFILES_ROOT / "claude" / "hooks"
_ENV_FILES = [
    _BOTFILES_ROOT / "secrets" / "local" / "machine.rc",
    _BOTFILES_ROOT / "secrets" / "local" / "claude-hooks.rc",
]
WHATSAPP_TEXT_MAX_CHARS = 4096
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
DEFAULT_EMAIL_SUBJECT_PREFIX = "AgentAlert"
DEFAULT_GMAIL_TOKEN_PATH = _BOTFILES_ROOT / "secrets" / "local" / "gmail-token.json"
DEFAULT_GMAIL_THREAD_STATE_PATH = (
    _BOTFILES_ROOT / "secrets" / "local" / "gmail-thread-state.json"
)
_DATE_FOLDER_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TASK_FOLDER_TIME_PREFIX_RE = re.compile(r"^\d{2}h\d{2}m\d{2}sPST-")
_TASK_HASH_SUFFIX_RE = re.compile(r"-[0-9a-f]{8,}$")
_ISSUE_SLUG_WITH_SEMANTIC_RE = re.compile(r"^(.+-issue-\d+)(?:-(.+))?$")
_AGENT_SESSION_ENV_KEYS = (
    "CODEX_THREAD_ID",
    "CODEX_SESSION_ID",
    "AGENT_SESSION_ID",
    "CLAUDE_SESSION_ID",
)

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
    for env_path in _ENV_FILES:
        if not env_path.exists():
            continue
        for line in env_path.read_text().splitlines():
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

            if override or key not in os.environ or not str(os.environ.get(key, "")).strip():
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
        "email_enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        "email_provider": os.getenv("EMAIL_PROVIDER", "gmail").strip().lower(),
        "email_to": os.getenv("EMAIL_TO", "").strip(),
        "email_from": os.getenv("EMAIL_FROM", "").strip(),
        "email_subject_prefix": os.getenv(
            "EMAIL_SUBJECT_PREFIX", DEFAULT_EMAIL_SUBJECT_PREFIX
        ).strip()
        or DEFAULT_EMAIL_SUBJECT_PREFIX,
        "email_task_label": os.getenv("EMAIL_TASK_LABEL", "").strip(),
        "gmail_oauth_client_secret_path": os.getenv(
            "GMAIL_OAUTH_CLIENT_SECRET_PATH", ""
        ).strip(),
        "gmail_oauth_token_path": os.getenv(
            "GMAIL_OAUTH_TOKEN_PATH",
            str(DEFAULT_GMAIL_TOKEN_PATH),
        ).strip(),
        "gmail_thread_state_path": os.getenv(
            "GMAIL_THREAD_STATE_PATH",
            str(DEFAULT_GMAIL_THREAD_STATE_PATH),
        ).strip(),
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


def build_context_header(system_name: str, session_name: str, agent_session_id: str) -> str:
    """Build a compact context header for outbound chat notifications."""
    resolved_agent_session_id = agent_session_id or "none"
    return f"[{system_name} | sid:{resolved_agent_session_id} | zj:{session_name}]"


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


def build_email_subject(
    system_name: str,
    agent_session_id: str,
    subject_prefix: str,
    task_label: str,
) -> str:
    """Build a stable subject for per-session email thread grouping."""
    resolved_agent_session_id = agent_session_id or "none"
    return (
        f"{subject_prefix} "
        f"[task:{task_label}] "
        f"[{system_name}] "
        f"[sid:{resolved_agent_session_id}]"
    )


def _sanitize_task_label(raw_value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw_value.strip())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        return ""
    return normalized[:80]


def _extract_semantic_task_label(raw_value: str) -> str:
    """Extract a clean task label while preserving issue prefix + semantic suffix."""
    sanitized = _sanitize_task_label(raw_value)
    if not sanitized:
        return ""

    without_time_prefix = _TASK_FOLDER_TIME_PREFIX_RE.sub("", sanitized)

    candidate = _TASK_HASH_SUFFIX_RE.sub("", without_time_prefix).strip("-")
    if not candidate:
        candidate = without_time_prefix

    issue_match = _ISSUE_SLUG_WITH_SEMANTIC_RE.match(candidate)
    if issue_match:
        issue_prefix = issue_match.group(1).strip("-")
        semantic_suffix = (issue_match.group(2) or "").strip("-")
        if semantic_suffix:
            candidate = f"{issue_prefix}-{semantic_suffix}"
        else:
            candidate = issue_prefix

    return _sanitize_task_label(candidate)


def _task_label_from_cwd_context_path() -> str:
    """
    Resolve task folder label from cwd when running inside context/daily/<date>/<task>/...
    """
    cwd_parts = Path.cwd().resolve().parts
    for index in range(len(cwd_parts) - 3):
        if cwd_parts[index] == "context" and cwd_parts[index + 1] == "daily":
            date_component = cwd_parts[index + 2]
            if _DATE_FOLDER_RE.match(date_component):
                return _extract_semantic_task_label(cwd_parts[index + 3])
    return ""


def _get_agent_session_id() -> str:
    for env_key in _AGENT_SESSION_ENV_KEYS:
        value = os.getenv(env_key, "").strip()
        if value:
            return value
    return ""


def _task_label_from_status_files(agent_session_id: str) -> str:
    """
    Resolve task label by finding a matching task status file in the current repo.
    """
    if not agent_session_id:
        return ""

    context_daily = Path.cwd() / "context" / "daily"
    if not context_daily.exists():
        return ""

    date_dirs = [
        d for d in context_daily.iterdir() if d.is_dir() and _DATE_FOLDER_RE.match(d.name)
    ]
    date_dirs.sort(key=lambda d: d.name, reverse=True)

    for date_dir in date_dirs[:14]:
        status_files = list(date_dir.glob("*/status.md")) + list(date_dir.glob("*/README.md"))
        status_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for status_file in status_files:
            try:
                content = status_file.read_text()
            except Exception:
                continue

            if agent_session_id in content:
                return _extract_semantic_task_label(status_file.parent.name)

    return ""


def get_task_label(config: dict) -> str:
    """Resolve a task label for email subject/thread grouping."""
    for env_key in ("email_task_label",):
        value = str(config.get(env_key, "")).strip()
        semantic = _extract_semantic_task_label(value)
        if semantic:
            return semantic

    cwd_task = _task_label_from_cwd_context_path()
    if cwd_task:
        return cwd_task

    for env_key in ("TASK_SLUG", "TASK_NAME", "PROJECT_SLUG"):
        value = os.getenv(env_key, "").strip()
        semantic = _extract_semantic_task_label(value)
        if semantic:
            return semantic

    status_task = _task_label_from_status_files(_get_agent_session_id())
    if status_task:
        return status_task

    cwd_name = _extract_semantic_task_label(Path.cwd().name)
    if cwd_name:
        return cwd_name

    return "unknown-task"


def _load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        _log(f"JSON read failed: {path}")
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _save_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def _build_gmail_service(config: dict):
    """Build an authenticated Gmail API service client."""
    try:
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        _log("Gmail: missing dependencies; install google-api-python-client/google-auth-oauthlib")
        print(
            "Gmail enabled but required packages are missing. "
            "Install: google-api-python-client google-auth-oauthlib google-auth-httplib2",
            file=sys.stderr,
        )
        return None

    token_path = Path(config["gmail_oauth_token_path"]).expanduser()
    client_secret_raw = config["gmail_oauth_client_secret_path"]
    client_secret_path = Path(client_secret_raw).expanduser() if client_secret_raw else None
    scopes = [GMAIL_SEND_SCOPE]

    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), scopes=scopes)
        except Exception as e:
            _log(f"Gmail: failed loading token file {token_path}: {e}")

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleAuthRequest())
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
            _log("Gmail: refreshed access token")
        except Exception as e:
            _log(f"Gmail: token refresh failed: {e}")
            creds = None

    if not creds or not creds.valid:
        if not client_secret_path or not client_secret_path.exists():
            _log("Gmail: missing token and client secret path")
            print(
                "Gmail enabled but OAuth is not initialized. Set GMAIL_OAUTH_CLIENT_SECRET_PATH "
                "and bootstrap a token in GMAIL_OAUTH_TOKEN_PATH.",
                file=sys.stderr,
            )
            return None

        if not sys.stdin.isatty():
            _log("Gmail: non-interactive mode with missing/invalid token")
            print(
                "Gmail token missing/invalid in non-interactive hook run. "
                "Run once interactively to complete OAuth bootstrap.",
                file=sys.stderr,
            )
            return None

        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), scopes=scopes)
            creds = flow.run_local_server(port=0, open_browser=False)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
            _log(f"Gmail: OAuth bootstrap completed and token saved to {token_path}")
        except Exception as e:
            _log(f"Gmail: OAuth bootstrap failed: {e}")
            print(f"Gmail OAuth bootstrap failed: {e}", file=sys.stderr)
            return None

    try:
        return build("gmail", "v1", credentials=creds, cache_discovery=False)
    except Exception as e:
        _log(f"Gmail: failed to build API service: {e}")
        print(f"Gmail API client setup failed: {e}", file=sys.stderr)
        return None


def _resolve_gmail_to_email(service, configured_to_email: str) -> str:
    if configured_to_email:
        return configured_to_email
    try:
        profile = service.users().getProfile(userId="me").execute()
        profile_email = str(profile.get("emailAddress", "")).strip()
        if profile_email:
            return profile_email
    except Exception as e:
        _log(f"Gmail: failed to resolve profile email: {e}")
    return ""


def _send_gmail_raw_message(
    service,
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
    reply_to_message_id: str | None = None,
) -> tuple[bool, str | None, str]:
    """Send a Gmail message with optional threading metadata."""
    email_message = EmailMessage()
    email_message["To"] = to_email
    if from_email:
        email_message["From"] = from_email
    email_message["Subject"] = subject

    client_message_id = f"<{uuid.uuid4()}@personal-os.local>"
    email_message["Message-ID"] = client_message_id
    if reply_to_message_id:
        email_message["In-Reply-To"] = reply_to_message_id
        email_message["References"] = reply_to_message_id

    email_message.set_content(body)
    encoded_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode("utf-8")

    payload = {"raw": encoded_message}
    if thread_id:
        payload["threadId"] = thread_id

    try:
        response = service.users().messages().send(userId="me", body=payload).execute()
        return True, response.get("threadId"), client_message_id
    except Exception as e:
        if thread_id:
            _log(f"Gmail: send with thread_id failed, retrying without thread_id: {e}")
            fallback_payload = {"raw": encoded_message}
            try:
                response = service.users().messages().send(
                    userId="me",
                    body=fallback_payload,
                ).execute()
                return True, response.get("threadId"), client_message_id
            except Exception as e2:
                _log(f"Gmail: send retry failed: {e2}")
                print(f"Gmail send failed: {e2}", file=sys.stderr)
                return False, None, client_message_id

        _log(f"Gmail: send failed: {e}")
        print(f"Gmail send failed: {e}", file=sys.stderr)
        return False, None, client_message_id


def send_email_notification(
    config: dict,
    title: str,
    message: str,
    system_name: str,
    agent_session_id: str,
    context_header: str,
    session_url: str | None,
    attach_command: str | None,
) -> None:
    """Send notification through configured email provider."""
    provider = config["email_provider"] or "gmail"
    if provider != "gmail":
        _log(f"Email: unsupported provider '{provider}'")
        print(f"Unsupported EMAIL_PROVIDER '{provider}'", file=sys.stderr)
        return

    service = _build_gmail_service(config)
    if service is None:
        return

    to_email = _resolve_gmail_to_email(service, config["email_to"])
    if not to_email:
        _log("Gmail: could not determine recipient email")
        print("Gmail recipient email is not configured and profile lookup failed.", file=sys.stderr)
        return

    from_email = config["email_from"]
    task_label = get_task_label(config)
    subject = build_email_subject(
        system_name=system_name,
        agent_session_id=agent_session_id,
        subject_prefix=config["email_subject_prefix"],
        task_label=task_label,
    )

    body_lines = [
        context_header,
        f"Agent Session ID: {agent_session_id or 'none'}",
        f"Title: {title}",
        "",
        str(message).strip(),
        "",
        f"Open Session: {session_url or 'n/a'}",
        f"Attach Command: {attach_command or 'n/a'}",
    ]
    body_text = "\n".join([line for line in body_lines if line is not None])

    thread_state_path = Path(config["gmail_thread_state_path"]).expanduser()
    thread_state = _load_json_file(thread_state_path)
    thread_key = f"{system_name}::{agent_session_id or 'none'}::{task_label}"
    existing_thread = thread_state.get(thread_key, {})
    thread_id = str(existing_thread.get("thread_id", "")).strip() or None
    last_message_id = str(existing_thread.get("last_message_id", "")).strip() or None

    _log(
        "Sending Email (gmail): "
        f"to={to_email}, "
        f"subject={subject}, "
        f"thread_key={thread_key}, "
        f"thread_id={thread_id or 'none'}"
    )

    sent_ok, new_thread_id, sent_message_id = _send_gmail_raw_message(
        service=service,
        to_email=to_email,
        from_email=from_email,
        subject=subject,
        body=body_text,
        thread_id=thread_id,
        reply_to_message_id=last_message_id,
    )
    if not sent_ok:
        return

    effective_thread_id = new_thread_id or thread_id or ""
    latest_message_id = sent_message_id

    thread_state[thread_key] = {
        "thread_id": effective_thread_id,
        "last_message_id": latest_message_id,
        "last_updated_at": datetime.now().isoformat(),
    }
    _save_json_file(thread_state_path, thread_state)


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
    if len(sanitized_message) > WHATSAPP_TEXT_MAX_CHARS:
        sanitized_message = sanitized_message[: WHATSAPP_TEXT_MAX_CHARS - 1].rstrip() + "…"
        _log(f"WhatsApp: message truncated to {WHATSAPP_TEXT_MAX_CHARS} chars before send")

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


def send_notification(
    title: str,
    message: str,
    send_local: bool = True,
    agent_session_id_override: str | None = None,
) -> None:
    """Send notification to all enabled channels (local + WhatsApp + Email)."""
    _log(f"send_notification called: title={title}")

    if send_local:
        send_local_notification(title, message)
        _log("Local notification attempted")
    else:
        _log("Local notification disabled by caller")

    config = get_config()
    system_name = get_system_name()
    session_name = get_zellij_session_name()
    agent_session_id = (agent_session_id_override or "").strip() or _get_agent_session_id()
    context_header = build_context_header(system_name, session_name, agent_session_id)
    session_url = build_zellij_session_url(
        session_name=session_name,
        base_url=config["zellij_web_base_url"],
        links_enabled=config["zellij_web_enable_links"],
    )
    attach_command = build_zellij_attach_command(session_name)

    _log(
        "Config: "
        f"whatsapp_enabled={config['whatsapp_enabled']}, "
        f"email_enabled={config['email_enabled']}, "
        f"email_provider={config['email_provider'] or 'unset'}"
    )

    if config["whatsapp_enabled"]:
        if not all(
            [
                config["whatsapp_token"],
                config["phone_number_id"],
                config["notify_phone_number"],
            ]
        ):
            _log("WhatsApp enabled but missing required config")
            print(
                "WhatsApp enabled but missing required config "
                "(WHATSAPP_TOKEN, PHONE_NUMBER_ID, NOTIFY_PHONE_NUMBER)",
                file=sys.stderr,
            )
        else:
            body_text = str(message).strip()
            open_session_line = (
                f"Open Session: {session_url or 'n/a'}" if config["zellij_web_enable_links"] else None
            )
            session_id_line = f"Agent Session ID: {agent_session_id or 'none'}"
            fixed_lines = [context_header, title, session_id_line]
            if open_session_line:
                fixed_lines.append(open_session_line)
            fixed_text = "\n".join([line for line in fixed_lines if line])

            if body_text:
                available_body_chars = WHATSAPP_TEXT_MAX_CHARS - len(fixed_text) - 1
                if len(body_text) > available_body_chars:
                    if available_body_chars <= 0:
                        body_text = ""
                    elif available_body_chars == 1:
                        body_text = "…"
                    else:
                        body_text = body_text[: available_body_chars - 1].rstrip() + "…"
                    _log("WhatsApp: notification body truncated to preserve context + session link")

            whatsapp_lines = [context_header, title, session_id_line]
            if body_text:
                whatsapp_lines.append(body_text)
            if open_session_line:
                whatsapp_lines.append(open_session_line)

            whatsapp_message = "\n".join([line for line in whatsapp_lines if line])
            _log(
                "Sending WhatsApp: "
                f"system_name={system_name}, "
                f"session_name={session_name}, "
                f"agent_session_id={agent_session_id or 'none'}, "
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
            if config["zellij_send_attach_command"] and attach_command:
                _log("Sending WhatsApp attach command message")
                send_whatsapp_message(
                    message=attach_command,
                    to_phone=config["notify_phone_number"],
                    token=config["whatsapp_token"],
                    phone_number_id=config["phone_number_id"],
                )
    else:
        _log("WhatsApp not enabled, skipping")

    if config["email_enabled"]:
        send_email_notification(
            config=config,
            title=title,
            message=message,
            system_name=system_name,
            agent_session_id=agent_session_id,
            context_header=context_header,
            session_url=session_url,
            attach_command=attach_command,
        )
    else:
        _log("Email not enabled, skipping")
