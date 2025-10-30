import os
import logging
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder,
    CommandHandler, MessageHandler, ContextTypes, filters
)

# --------- CONFIG ---------
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Set BOT_TOKEN env var on Render")

# Render дає публічну адресу в змінній RENDER_EXTERNAL_URL
EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
# Фолбек, якщо раптом її нема — можеш вручну вказати в Render як WEBHOOK_URL
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", EXTERNAL_URL)

WEBHOOK_PATH = f"/webhook/{TOKEN}"          # унікальний шлях
PORT = int(os.environ.get("PORT", "10000")) # Render передасть свій порт у PORT

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("babybot")

# --------- HANDLERS (приклад) ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! 👶 Бот запущено на Render (webhook).")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def build_app() -> Application:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return app

if __name__ == "__main__":
    if not WEBHOOK_URL:
        raise RuntimeError("No EXTERNAL URL. Render must set RENDER_EXTERNAL_URL, "
                           "or set WEBHOOK_URL env var yourself.")

    application = build_app()

    full_webhook_url = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
    log.info("Starting webhook...")
    log.info(f"Listen on 0.0.0.0:{PORT}, path={WEBHOOK_PATH}")
    log.info(f"Set webhook URL -> {full_webhook_url}")

    # PTB сам підніме aiohttp-сервер і поставить webhook у Telegram
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=full_webhook_url,
        webhook_path=WEBHOOK_PATH,
        # без SSL — Render термінує TLS перед сервісом
    )
