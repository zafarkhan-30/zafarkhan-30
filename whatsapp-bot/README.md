# WhatsApp AI bot (Meta Cloud API + Claude)

Incoming WhatsApp message -> webhook -> Claude -> reply via the Cloud API.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in the blanks
uvicorn app.main:app --port 8000
ngrok http 8000             # or cloudflared; gives a public HTTPS URL
```

## Meta setup
1. App Dashboard -> WhatsApp -> API Setup: copy the access token into `.env`, add your own number as a test recipient.
2. App Settings -> Basic: copy **App Secret** into `META_APP_SECRET`.
3. WhatsApp -> Configuration -> Webhook:
   - Callback URL: `https://<public-host>/webhook`
   - Verify token: same value as `WHATSAPP_VERIFY_TOKEN`
   - Subscribe to the **messages** field.
4. Message the test number from WhatsApp; the bot should reply.

## Notes
- Webhook signatures (`X-Hub-Signature-256`) are verified; requests without a valid one get 403.
- Duplicate deliveries are ignored; conversation history is in-memory (use Redis/DB if scaling out).
- Temporary tokens expire in 24h. For production create a System User permanent token.
- Customize behaviour with `BOT_SYSTEM_PROMPT`.
- Tests: `python -m pytest`
