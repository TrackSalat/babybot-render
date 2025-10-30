import os
import logging
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder,
    CommandHandler, MessageHandler, ContextTypes, filters
)

# ---------- CONFIG ----------
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Set BOT_TOKEN env var on Render")

EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", EXTERNAL_URL)

WEBHOOK_PATH = f"/webhook/{TOKEN}"
PORT = int(os.environ.get("PORT", "10000"))

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("babybot")

# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! 👶 Бот на Render працює через webhook.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# ---------- APPLICATION ----------
def build_app() -> Application:
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .updater(None)          # важливо на Python 3.13 / для webhook
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return app

# ---------- MAIN ----------
if __name__ == "__main__":
    if not WEBHOOK_URL:
        raise RuntimeError(
            "No EXTERNAL URL. Render must set RENDER_EXTERNAL_URL "
            "or set WEBHOOK_URL env var manually."
        )

    application = build_app()

    full_webhook_url = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
    log.info(f"Starting webhook on port {PORT}")
    log.info(f"Webhook URL: {full_webhook_url}")

    # PTB 20.x: параметр називається url_path
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=full_webhook_url,
    )
