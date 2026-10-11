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

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful WhatsApp assistant. Reply in the same language the user writes in "
    "(English, Hindi or Hinglish). Keep replies short and conversational, plain text only "
    "(WhatsApp does not render markdown headings or tables). If you don't know something, "
    "say so instead of guessing."
)
SYSTEM_PROMPT = os.getenv("BOT_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT
