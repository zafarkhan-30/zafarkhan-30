import hashlib
import hmac

import httpx

from . import config


def verify_signature(raw_body: bytes, header: str | None) -> bool:
    """Validate Meta's X-Hub-Signature-256 header against the app secret."""
    if not config.APP_SECRET or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(config.APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def _url() -> str:
    return f"https://graph.facebook.com/{config.GRAPH_VERSION}/{config.PHONE_NUMBER_ID}/messages"


async def _post(payload: dict) -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            _url(),
            headers={"Authorization": f"Bearer {config.ACCESS_TOKEN}"},
            json={"messaging_product": "whatsapp", **payload},
        )
        if r.is_error:
            print(f"WhatsApp API error {r.status_code}: {r.text}")


async def send_text(to: str, body: str) -> None:
    # WhatsApp text limit is 4096 chars
    await _post({"to": to, "type": "text", "text": {"body": body[:4096]}})


async def mark_read(message_id: str) -> None:
    await _post({"status": "read", "message_id": message_id})
