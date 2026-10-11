import hashlib
import hmac
import json
import os

os.environ.update(WHATSAPP_VERIFY_TOKEN="vt", META_APP_SECRET="secret")

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402

client = TestClient(main.app)


def sign(body: bytes) -> str:
    return "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()


def test_verify_ok():
    r = client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "vt", "hub.challenge": "123"})
    assert r.status_code == 200 and r.text == "123"


def test_verify_bad_token():
    r = client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "x", "hub.challenge": "1"})
    assert r.status_code == 403


def test_rejects_bad_signature():
    r = client.post("/webhook", content=b"{}", headers={"X-Hub-Signature-256": "sha256=bad"})
    assert r.status_code == 403


def test_message_flow_and_dedupe(monkeypatch):
    sent = []

    async def fake_reply(user, text):
        return f"echo:{text}"

    async def fake_send(to, body):
        sent.append((to, body))

    async def fake_read(_):
        pass

    monkeypatch.setattr(main.ai, "reply_to", fake_reply)
    monkeypatch.setattr(main.whatsapp, "send_text", fake_send)
    monkeypatch.setattr(main.whatsapp, "mark_read", fake_read)
    payload = {"entry": [{"changes": [{"value": {"messages": [
        {"id": "m1", "from": "919999", "type": "text", "text": {"body": "hi"}}]}}]}]}
    body = json.dumps(payload).encode()
    for _ in range(2):  # second delivery must be ignored
        r = client.post("/webhook", content=body, headers={"X-Hub-Signature-256": sign(body)})
        assert r.status_code == 200
    assert sent == [("919999", "echo:hi")]
