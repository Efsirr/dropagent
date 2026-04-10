# DropAgent Hosted Mode

Hosted mode lets a non-technical user find a public DropAgent Telegram bot, open the dashboard, finish setup, and connect their own service API keys.

Self-hosted mode still works. Hosted mode is an easier entry path, not a replacement.

---

## Mental Model

```text
Telegram user
-> public DropAgent bot
-> Telegram webhook
-> DropAgent API/backend
-> Supabase Postgres
-> Vercel dashboard
```

Users do not need to clone the repo for hosted mode.

They still own their marketplace/intelligence API keys.

---

## Instance-Level Secrets

These are configured by the person hosting DropAgent.

Keep them in the hosting provider's secret/env settings.

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
DASHBOARD_PUBLIC_URL=
DATABASE_URL=
APP_SECRET_KEY=
```

What they do:

- `TELEGRAM_BOT_TOKEN` runs the public bot.
- `TELEGRAM_WEBHOOK_SECRET` verifies that webhook requests came from Telegram.
- `DASHBOARD_PUBLIC_URL` lets `/start` and `/setup` show an "Open setup dashboard" button.
- `DATABASE_URL` points to Supabase Postgres or another Postgres database.
- `APP_SECRET_KEY` seals user-owned API keys before database storage.

Use a long random `APP_SECRET_KEY`. If it is lost, saved user API keys cannot be opened.

---

## User-Owned Service Keys

Do not put user-owned service keys in `.env`.

Users connect them from setup UI or Telegram:

```text
/connect keepa <api_key>
/disconnect keepa
```

The backend stores encrypted/sealed keys in `user_integration_credentials`.

API responses must show only:

```text
service name
status
masked hint
last checked time
```

Never return the raw key.

---

## Supabase Notes

DropAgent uses normal Postgres tables through SQLAlchemy.

For hosted mode:

1. Create a Supabase project.
2. Copy the Postgres connection string.
3. Set `DATABASE_URL` in the backend hosting provider.
4. Run DropAgent migrations against that database before launch.
5. Keep Supabase service credentials out of frontend code.

Row Level Security (RLS) is enabled on all tables. No permissive policies are defined — all access must go through the Python backend using the service role `DATABASE_URL`. Direct anon/public Supabase API access is blocked by default.

Never expose the Supabase service role key or `DATABASE_URL` in browser JavaScript or frontend code.

---

## Telegram Webhook

The hosted bot should use a webhook instead of long polling.

The framework-agnostic handler is:

```text
bot/webhook.py
```

It accepts Telegram update JSON, checks the optional webhook secret header, and reuses the existing bot router.

### Registering the webhook with Telegram

After deploying to Vercel, register the webhook URL once:

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<your-vercel-domain>/telegram/webhook",
    "secret_token": "<TELEGRAM_WEBHOOK_SECRET>",
    "allowed_updates": ["message", "callback_query"]
  }'
```

Replace:
- `<TELEGRAM_BOT_TOKEN>` — your bot token from @BotFather
- `<your-vercel-domain>` — the domain shown in Vercel project settings (e.g. `dropagent.vercel.app`)
- `<TELEGRAM_WEBHOOK_SECRET>` — the value you set in `TELEGRAM_WEBHOOK_SECRET` env var

Verify the webhook is active:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

A successful response includes `"url"` and `"has_custom_certificate": false`.

To remove the webhook (revert to long-polling for local dev):

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/deleteWebhook"
```

Self-hosted polling still starts with:

```bash
python3 -m bot.main
```

---

## Dashboard Link

If `DASHBOARD_PUBLIC_URL` is configured, Telegram setup messages include a safe dashboard button.

Example:

```text
https://your-dashboard.example/?telegram_chat_id=123&username=totik
```

This link must never include API keys, bot tokens, app secrets, or Supabase secrets.

---

## Public Launch Checklist

- Rotate and set the official Telegram bot token.
- Set `TELEGRAM_WEBHOOK_SECRET`.
- Set `DASHBOARD_PUBLIC_URL`.
- Set `DATABASE_URL`.
- Set a long random `APP_SECRET_KEY`.
- Run database migrations.
- Configure Telegram `setWebhook` with the hosted webhook URL and secret token.
- Open the public bot in Telegram.
- Send `/start`.
- Press `Open setup dashboard`.
- Connect one test service key.
- Confirm API responses show only a masked hint.
- Send `/status`.
- Send `/track airpods pro`.

---

## What Hosted Mode Does Not Mean

Hosted mode does not mean DropAgent pays for every user's Keepa, StoreLeads, ZIK, PiPiADS, Minea, Amazon, Walmart, AliExpress, or CJ access.

Users bring their own keys. DropAgent makes connecting them simple.
