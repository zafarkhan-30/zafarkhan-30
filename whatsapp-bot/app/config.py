import os

from dotenv import load_dotenv

load_dotenv()

PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
GRAPH_VERSION = os.getenv("GRAPH_API_VERSION", "v21.0")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "10"))

KNOWLEDGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge.md")
OWNER_WHATSAPP = os.getenv("OWNER_WHATSAPP", "")  # e.g. 919876543210, gets lead alerts
LEADS_FILE = os.getenv("LEADS_FILE", "leads.jsonl")


def _knowledge() -> str:
    try:
        with open(KNOWLEDGE_FILE, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return "(no knowledge file found)"


DEFAULT_SYSTEM_PROMPT = """You are the WhatsApp sales assistant for Syntechire, a web/software company. \
People message you as leads asking about website prices, services, timelines or other queries.

Rules:
- Reply in the user's language (English, Hindi or Hinglish). Be warm, short and conversational: \
2-5 short lines, plain text only (no markdown, headings or tables).
- Answer prices, services and policies ONLY from the knowledge base below. Never invent prices, \
discounts, timelines or promises. If the answer isn't there, say the team will confirm shortly.
- Understand what the lead needs. Ask at most one or two helpful questions at a time \
(type of website, number of pages, features, budget, timeline).
- Once you have their name and requirement (and ideally budget/timeline), call save_lead. \
Then tell them our team will contact them soon.
- If they ask for a human, are upset, or want a custom quote, call save_lead with needs_human=true.
- Don't discuss anything unrelated to Syntechire's business; politely steer back.

KNOWLEDGE BASE:
{knowledge}
"""
SYSTEM_PROMPT = os.getenv("BOT_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT.format(knowledge=_knowledge())
