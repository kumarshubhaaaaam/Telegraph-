# Telegraph Image Article Bot

Sends a batch of images → uploads each to ImgBB → creates one Telegraph
article with the images embedded in the exact order they were sent.

## How it works

1. `/newarticle` → bot shows **✅ Done** / **❌ Cancel** buttons.
2. Send images, one by one or as albums (media groups) — any order works.
3. Tap **✅ Done**.
4. Bot uploads every image to ImgBB (original quality, no compression),
   shows live progress (`Uploading image 3/12...`), then creates a
   Telegraph article and replies with the link.

Each Telegram user has an independent session, so multiple people can use
the bot at once without mixing up images.

## Project structure

```
bot.py              # entry point (polling mode)
server.py           # optional entry point (webhook mode, FastAPI)
config.py           # env var loading
utils.py            # per-user session management
imgbb.py            # ImgBB upload client (with retries)
telegraph_client.py # Telegraph article creation (see naming note below)
image_processor.py  # uploads a batch of images, preserves order, progress
handlers/
  commands.py        # /start, /newarticle
  images.py           # photo + album message handling
  callbacks.py        # ✅ Done / ❌ Cancel button logic
requirements.txt
.env.example
```

**Naming note:** the Telegraph module is called `telegraph_client.py`
instead of `telegraph.py`. If it were named `telegraph.py`, its own
`from telegraph import Telegraph` line would import itself instead of the
installed `telegraph` package, breaking the bot. `telegraph_client.py`
avoids that collision.

## Setup

```bash
git clone <your-repo>
cd telegraph_image_bot
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

| Variable | Required | Notes |
|---|---|---|
| `BOT_TOKEN` | yes | From [@BotFather](https://t.me/BotFather) |
| `IMGBB_API_KEY` | yes | From [api.imgbb.com](https://api.imgbb.com/) |
| `TELEGRAPH_SHORT_NAME` | no | Display name for the Telegraph account (default `ImageBot`) |
| `TELEGRAPH_ACCESS_TOKEN` | no | Reuse an existing Telegraph account across restarts instead of creating a new one each boot |
| `ADMIN_ID` | no | Reserved for future admin-only commands |
| `MAX_IMAGES_PER_ARTICLE` | no | Safety cap, default 200 |
| `UPLOAD_CONCURRENCY` | no | Parallel ImgBB uploads, default 5 |

Run locally (polling mode — simplest, works anywhere):

```bash
python bot.py
```

## Deploying

### Option A — Render Background Worker (polling, recommended)

1. Push this repo to GitHub.
2. On Render: **New → Background Worker** → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Add the env vars from `.env.example` under **Environment**.

Background Workers don't need an open port, so `bot.py`'s polling loop
works as-is, and this sidesteps Render free-tier's "no open ports" issue
that affects Web Services.

### Option B — Render Web Service (webhook mode)

If you need a Web Service instead (e.g. free tier only offers that):

1. Build command: `pip install -r requirements.txt`
2. Start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
3. Env vars: same as above. Render sets `PORT` and `RENDER_EXTERNAL_URL`
   automatically — `server.py` picks up `RENDER_EXTERNAL_URL` and
   registers the webhook on startup, so you don't need to set
   `WEBHOOK_BASE_URL` manually on Render (only needed for other hosts).

### Koyeb

Same two options apply — either run `bot.py` as a worker process, or
`server.py` behind Koyeb's assigned port for webhook mode.

## Error handling

- Each ImgBB upload retries up to 3 times with backoff before being
  skipped; skipped images don't shift the position of the ones after them.
- If every upload fails, the bot reports failure and does not create an
  empty article.
- Temporary files live under `temp_images/<user>_<random>/` and are
  deleted immediately after the article is created (or the session is
  cancelled) — nothing is stored permanently.

## Limitations / things to know

- PTB's `Application` processes updates sequentially by default
  (`concurrent_updates=False`), which is what keeps album/photo order
  intact. Don't turn on `concurrent_updates` without adding explicit
  sequence numbers, or ordering can break.
- ImgBB's free tier has its own rate limits; if you're sending 100+ images
  routinely, consider lowering `UPLOAD_CONCURRENCY`.
- The bot currently accepts Telegram photos (compressed by Telegram itself
  at the "best available" resolution Telegram offers, which is the
  highest quality accessible via the Bot API — Telegram does not expose
  the original uncompressed file through this API). If you need truly
  original files, send them as **documents** (uncompressed) — that would
  require a small addition to `handlers/images.py` to also accept
  `filters.Document.IMAGE`.
