"""
WhatsApp notification module for Claude Code hooks.
Uses Meta's WhatsApp Cloud API v17.0.
"""
import sys
from datetime import datetime
from pathlib import Path

import requests


# Log file path
_LOG_FILE = Path(__file__).parent / "hooks.log"


def _log(message: str) -> None:
    """Append a timestamped message to the log file."""
    timestamp = datetime.now().isoformat()
    with open(_LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def send_whatsapp_message(
    message: str,
    to_phone: str,
    token: str,
    phone_number_id: str,
) -> bool:
    """
    Send a WhatsApp message via Meta's Cloud API.

    Args:
        message: The message body to send
        to_phone: Recipient phone number in E.164 format (e.g., +1234567890)
        token: WhatsApp Cloud API Bearer token
        phone_number_id: WhatsApp Business phone number ID

    Returns:
        True if message sent successfully, False otherwise
    """
    _log(f"WhatsApp: Sending to {to_phone}, phone_number_id={phone_number_id}")

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Strip + from phone number for API (expects digits only)
    to_phone_digits = to_phone.lstrip("+")

    # Sanitize message for unicode
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
        else:
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
