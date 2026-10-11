import json
import time

from . import config, whatsapp

LEAD_TOOL = {
    "name": "save_lead",
    "description": "Save a sales lead once you know their requirement. Call again to update details.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "requirement": {"type": "string", "description": "What they want built / asked about"},
            "budget": {"type": "string"},
            "timeline": {"type": "string"},
            "needs_human": {"type": "boolean", "description": "True if they want a person or custom quote"},
        },
        "required": ["requirement"],
    },
}


async def save_lead(phone: str, data: dict) -> str:
    record = {"ts": int(time.time()), "phone": phone, **data}
    with open(config.LEADS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    if config.OWNER_WHATSAPP:
        lines = "\n".join(f"{k}: {v}" for k, v in record.items() if k != "ts")
        await whatsapp.send_text(config.OWNER_WHATSAPP, f"New Syntechire lead\n{lines}")
    return "Lead saved."
