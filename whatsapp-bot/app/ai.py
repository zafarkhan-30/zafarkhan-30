from collections import defaultdict, deque

from anthropic import AsyncAnthropic

from . import config, leads

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
    messages = list(hist)
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    try:
        resp = None
        for _ in range(3):  # allow a few tool round-trips
            resp = await _get_client().messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=700,
                system=config.SYSTEM_PROMPT,
                tools=[leads.LEAD_TOOL],
                messages=messages,
            )
            if resp.stop_reason != "tool_use":
                break
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for b in resp.content:
                if b.type == "tool_use":
                    out = await leads.save_lead(user_id, b.input)
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
            messages.append({"role": "user", "content": results})
        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not answer:
            answer = "Thanks! Our team will get back to you shortly."
    except Exception as e:  # keep the bot alive on API errors
        print(f"Claude error: {e}")
        hist.pop()
        return "Sorry, I'm having trouble right now. Our team will reach out shortly."
    hist.append({"role": "assistant", "content": answer})
    return answer
