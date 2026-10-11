from collections import defaultdict, deque

from anthropic import AsyncAnthropic

from . import config

_client: AsyncAnthropic | None = None
# In-memory per-user history. Swap for Redis/DB if you run multiple workers.
_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=config.MAX_HISTORY_TURNS * 2))


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY
    return _client


async def reply_to(user_id: str, text: str) -> str:
    hist = _history[user_id]
    hist.append({"role": "user", "content": text})
    # History must start with a user turn
    messages = list(hist)
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    try:
        resp = await _get_client().messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=700,
            system=config.SYSTEM_PROMPT,
            messages=messages,
        )
        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception as e:  # keep the bot alive on API errors
        print(f"Claude error: {e}")
        hist.pop()
        return "Sorry, I'm having trouble right now. Please try again in a moment."
    hist.append({"role": "assistant", "content": answer})
    return answer
