"""WhatsApp Cloud API dispatch adapter."""

import os
import requests


def send_whatsapp_po(phone_number: str, message_text: str) -> bool:
    """Send PO notification via Meta WhatsApp Cloud API.
    
    If credentials are missing, falls back cleanly to dry-run simulation.
    """
    token = os.getenv("WHATSAPP_API_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    if not token or not phone_id:
        print(f"   [WhatsApp Sim] Dispatched to {phone_number}: {message_text[:80]}...")
        return True

    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message_text},
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False
