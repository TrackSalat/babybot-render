import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, BotCommand
from telegram.ext import (
    Application, ApplicationBuilder,
    CommandHandler, MessageHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("babybot")

# --- ENV ---
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN env var is required")

# Render зазвичай ставить цю змінну сам
BASE_URL = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WEBHOOK_URL")
if not BASE_URL:
    # можна також вручну додати WEBHOOK_URL у Render → Environment (типу https://babybot-render.onrender.com)
    raise RuntimeError("No BASE_URL. Set RENDER_EXTERNAL_URL (Render sets it) or WEBHOOK_URL")

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "babybot-secret-123")

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! 👶 Бот на Render працює через FastAPI webhook.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def build_app() -> Application:
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return app

tg_app: Application = build_app()
api = FastAPI()

@api.on_event("startup")
async def on_startup():
    # 1) ініціалізуємо і запускаємо PTB
    await tg_app.initialize()
    # команди в меню Telegram (необов'язково)
    await tg_app.bot.set_my_commands([
        BotCommand("start", "Почати"),
    ])
    await tg_app.start()

    # 2) ставимо вебхук на наш FastAPI endpoint
    url = BASE_URL.rstrip("/") + f"/webhook/{WEBHOOK_SECRET}"
    ok = await tg_app.bot.set_webhook(url)
    log.info(f"Set webhook to: {url} (ok={ok})")

@api.on_event("shutdown")
async def on_shutdown():
    await tg_app.stop()
    await tg_app.shutdown()

@api.get("/")
async def root():
    return {"ok": True, "service": "babybot", "webhook": f"/webhook/{WEBHOOK_SECRET}"}

@api.post("/webhook/{secret}")
async def webhook(secret: str, request: Request):
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="forbidden")
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
