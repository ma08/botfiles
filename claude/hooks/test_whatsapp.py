#!/usr/bin/env python3
"""
Test script for WhatsApp notifications.
Run with: uv run python test_whatsapp.py
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).parent / ".env")

from whatsapp import send_whatsapp_message


def main():
    token = os.getenv("WHATSAPP_TOKEN", "")
    phone_number_id = os.getenv("PHONE_NUMBER_ID", "")
    notify_phone = os.getenv("NOTIFY_PHONE_NUMBER", "")
    system_name = os.getenv("SYSTEM_NAME", "Test")

    print("=== WhatsApp Test ===")
    print(f"Token: {token[:20]}..." if token else "Token: NOT SET")
    print(f"Phone Number ID: {phone_number_id}")
    print(f"Notify Phone: {notify_phone}")
    print(f"System Name: {system_name}")
    print()

    if not all([token, phone_number_id, notify_phone]):
        print("ERROR: Missing required environment variables")
        return

    message = f"[{system_name}]\nTest Message\nThis is a test from the hooks test script."
    print(f"Sending message to {notify_phone}...")
    print(f"Message:\n{message}")
    print()

    success = send_whatsapp_message(
        message=message,
        to_phone=notify_phone,
        token=token,
        phone_number_id=phone_number_id,
    )

    if success:
        print("SUCCESS: Message sent!")
    else:
        print("FAILED: Check hooks.log for details")


if __name__ == "__main__":
    main()
