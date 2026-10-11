from collections import OrderedDict

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request, Response

from . import ai, config, whatsapp

app = FastAPI(title="WhatsApp AI bot")

_seen: OrderedDict[str, None] = OrderedDict()  # dedupe: Meta retries webhooks


def _already_seen(message_id: str) -> bool:
    if message_id in _seen:
        return True
    _seen[message_id] = None
    if len(_seen) > 5000:
        _seen.popitem(last=False)
    return False


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/webhook")
async def verify(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    if mode == "subscribe" and config.VERIFY_TOKEN and token == config.VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(403, "Verification failed")


async def handle_message(msg: dict) -> None:
    sender = msg["from"]
    await whatsapp.mark_read(msg["id"])
    if msg.get("type") == "text":
        answer = await ai.reply_to(sender, msg["text"]["body"])
    else:
        answer = "I can only read text messages for now. Please type your question."
    await whatsapp.send_text(sender, answer)


@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not whatsapp.verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(403, "Invalid signature")
    data = await request.json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if not _already_seen(msg["id"]):
                    background.add_task(handle_message, msg)
    return {"status": "ok"}  # respond fast; Meta retries on slow/non-200
