"""
Utils for claude code hooks
https://docs.anthropic.com/en/docs/claude-code/hooks-guide
"""
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from whatsapp import send_whatsapp_message


# Load .env from the same directory as this file
_hooks_dir = Path(__file__).parent
load_dotenv(_hooks_dir / ".env")

# Log file path
_LOG_FILE = _hooks_dir / "hooks.log"


def _log(message: str) -> None:
    """Append a timestamped message to the log file."""
    timestamp = datetime.now().isoformat()
    with open(_LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# Sample of input data
# {
#   "session_id": "86ef4460-fb77-4cb9-9d1e-308a41151d2f",
#   "transcript_path": "/Users/sourya4/.claude/projects/-Users-sourya4-pro-ladduu-agent-stack/86ef4460-fb77-4cb9-9d1e-308a41151d2f.jsonl",
#   "hook_event_name": "Stop",
#   "stop_hook_active": false
# }

# Sample of transcript file
# {"parentUuid":null,"isSidechain":false,"userType":"external","cwd":"/Users/sourya4/pro/ladduu_agent_stack","sessionId":"86ef4460-fb77-4cb9-9d1e-308a41151d2f","version":"1.0.53","type":"user","message":{"role":"user","content":"yooo"},"uuid":"766d14e1-909e-40ff-bc0c-d064e120abbb","timestamp":"2025-07-17T18:26:33.694Z"}
# {"parentUuid":"766d14e1-909e-40ff-bc0c-d064e120abbb","isSidechain":false,"userType":"external","cwd":"/Users/sourya4/pro/ladduu_agent_stack","sessionId":"86ef4460-fb77-4cb9-9d1e-308a41151d2f","version":"1.0.53","message":{"id":"msg_bdrk_01GLm24oXXTygMs5LDJGRN9i","type":"message","role":"assistant","model":"claude-sonnet-4-20250514","content":[{"type":"text","text":"Hey! What's up? What can I help you with today?"}],"stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":4,"cache_creation_input_tokens":39074,"cache_read_input_tokens":0,"output_tokens":1}},"type":"assistant","uuid":"8d891d13-ed84-45bf-920e-83072988a9ef","timestamp":"2025-07-17T18:26:40.459Z"}
# {"parentUuid":"8d891d13-ed84-45bf-920e-83072988a9ef","isSidechain":false,"userType":"external","cwd":"/Users/sourya4/pro/ladduu_agent_stack","sessionId":"86ef4460-fb77-4cb9-9d1e-308a41151d2f","version":"1.0.53","type":"user","message":{"role":"user","content":"helloo"},"uuid":"8003b7e3-b4d7-4689-a48e-0359dc546856","timestamp":"2025-07-17T18:27:13.247Z"}
# {"parentUuid":"8003b7e3-b4d7-4689-a48e-0359dc546856","isSidechain":false,"userType":"external","cwd":"/Users/sourya4/pro/ladduu_agent_stack","sessionId":"86ef4460-fb77-4cb9-9d1e-308a41151d2f","version":"1.0.53","message":{"id":"msg_bdrk_01KRz7XBf3PRj4sYgGYP38nu","type":"message","role":"assistant","model":"claude-sonnet-4-20250514","content":[{"type":"text","text":"Hello! How can I help you today?"}],"stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":4,"cache_creation_input_tokens":22,"cache_read_input_tokens":39074,"output_tokens":12}},"type":"assistant","uuid":"a3e20381-ed13-4b51-94a8-809fd0826543","timestamp":"2025-07-17T18:27:16.428Z"}
# {"parentUuid":"a3e20381-ed13-4b51-94a8-809fd0826543","isSidechain":false,"userType":"external","cwd":"/Users/sourya4/pro/ladduu_agent_stack","sessionId":"86ef4460-fb77-4cb9-9d1e-308a41151d2f","version":"1.0.53","type":"user","message":{"role":"user","content":"yooo"},"uuid":"14aed825-4b8c-4f6e-b7bc-d8305db19fbd","timestamp":"2025-07-17T18:27:39.871Z"}
# {"parentUuid":"14aed825-4b8c-4f6e-b7bc-d8305db19fbd","isSidechain":false,"userType":"external","cwd":"/Users/sourya4/pro/ladduu_agent_stack","sessionId":"86ef4460-fb77-4cb9-9d1e-308a41151d2f","version":"1.0.53","message":{"id":"msg_bdrk_0126dgNsHoAGXFipN1x9FL1B","type":"message","role":"assistant","model":"claude-sonnet-4-20250514","content":[{"type":"text","text":"What's good! What do you need help with?"}],"stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":4,"cache_creation_input_tokens":18,"cache_read_input_tokens":39096,"output_tokens":14}},"type":"assistant","uuid":"9dba1cca-1fed-41bb-9326-9ef86f74a91d","timestamp":"2025-07-17T18:27:42.120Z"}

# {
#     "parentUuid": "14aed825-4b8c-4f6e-b7bc-d8305db19fbd",
#     "isSidechain": false,
#     "userType": "external",
#     "cwd": "/Users/sourya4/pro/ladduu_agent_stack",
#     "sessionId": "86ef4460-fb77-4cb9-9d1e-308a41151d2f",
#     "version": "1.0.53",
#     "message": {
#         "id": "msg_bdrk_0126dgNsHoAGXFipN1x9FL1B",
#         "type": "message",
#         "role": "assistant",
#         "model": "claude-sonnet-4-20250514",
#         "content": [
#             {"type": "text", "text": "What's good! What do you need help with?"}
#         ],
#         "stop_reason": null,
#         "stop_sequence": null,
#         "usage": {
#             "input_tokens": 4,
#             "cache_creation_input_tokens": 18,
#             "cache_read_input_tokens": 39096,
#             "output_tokens": 14,
#         },
#     },
#     "type": "assistant",
#     "uuid": "9dba1cca-1fed-41bb-9326-9ef86f74a91d",
#     "timestamp": "2025-07-17T18:27:42.120Z",
# }



def get_latest_message_from_transcript(transcript_path_jsonl: str) -> str:
    try:
        # Read and parse JSONL file line by line
        messages = []
        with open(transcript_path_jsonl, "r") as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
        
        if not messages:
            return ""

        last_message_dict = messages[-1].get("message", {})
        last_message_content_list = last_message_dict.get("content", [])

        curated_content = ""

        for content_item in last_message_content_list:
            if content_item.get("type") == "text":
                curated_content += content_item.get("text") + "\n"

        return curated_content
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return ""


def get_config() -> dict:
    """
    Get configuration from environment variables.

    Returns:
        Dictionary with configuration values
    """
    return {
        "whatsapp_enabled": os.getenv("WHATSAPP_ENABLED", "false").lower() == "true",
        "whatsapp_token": os.getenv("WHATSAPP_TOKEN", ""),
        "phone_number_id": os.getenv("PHONE_NUMBER_ID", ""),
        "notify_phone_number": os.getenv("NOTIFY_PHONE_NUMBER", ""),
        "system_name": os.getenv("SYSTEM_NAME", ""),
    }


def get_system_name() -> str:
    """
    Get system name from SYSTEM_NAME env var, fallback to hostname.

    Returns:
        System identifier string
    """
    system_name = os.getenv("SYSTEM_NAME", "")
    if system_name:
        return system_name
    return socket.gethostname()


def send_local_notification(title: str, message: str) -> None:
    """
    Send a local macOS notification using terminal-notifier.

    Args:
        title: Notification title
        message: Notification body
    """
    # Escape double quotes in message for shell
    safe_message = message.replace('"', '\\"')
    safe_title = title.replace('"', '\\"')
    os.system(f'terminal-notifier -message "{safe_message}" -title "{safe_title}" -sound default')


def send_notification(title: str, message: str) -> None:
    """
    Send notification to all enabled channels (local + WhatsApp).

    Args:
        title: Notification title
        message: Notification body
    """
    _log(f"send_notification called: title={title}")

    # Always send local notification
    send_local_notification(title, message)
    _log("Local notification sent")

    # Send WhatsApp if enabled
    config = get_config()
    _log(f"Config: whatsapp_enabled={config['whatsapp_enabled']}")

    if config["whatsapp_enabled"]:
        if not all([config["whatsapp_token"], config["phone_number_id"], config["notify_phone_number"]]):
            _log("WhatsApp enabled but missing required config")
            print("WhatsApp enabled but missing required config (WHATSAPP_TOKEN, PHONE_NUMBER_ID, NOTIFY_PHONE_NUMBER)", file=sys.stderr)
            return

        system_name = get_system_name()
        whatsapp_message = f"[{system_name}]\n{title}\n{message}"
        _log(f"Sending WhatsApp: system_name={system_name}, to={config['notify_phone_number']}")

        send_whatsapp_message(
            message=whatsapp_message,
            to_phone=config["notify_phone_number"],
            token=config["whatsapp_token"],
            phone_number_id=config["phone_number_id"],
        )
    else:
        _log("WhatsApp not enabled, skipping")
