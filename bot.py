import os
import logging
import tempfile
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DEEPGRAM_API_KEY = os.getenv("STT_API_KEY")  # ключ Deepgram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли мені голосове повідомлення, і я перетворю його на текст.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Тут обробляються тільки голосові повідомлення. Надішли voice.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    await update.message.reply_text("🎙️ Обробляю голосове повідомлення, зачекай...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
        await file.download_to_drive(f.name)
        audio_path = f.name

    try:
        # Надсилаємо файл у Deepgram
        with open(audio_path, "rb") as audio_file:
            response = requests.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "audio/ogg"
                },
                data=audio_file
            )

        if response.status_code == 200:
            data = response.json()
            text = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
            if text:
                await update.message.reply_text("📝 Ось ваш текст:\n\n" + text)
            else:
                await update.message.reply_text("🤔 Не вдалося розпізнати текст.")
        else:
            logger.error(f"Deepgram error: {response.status_code} - {response.text}")
            await update.message.reply_text("⚠️ Сталася помилка при обробці аудіо. Спробуйте пізніше.")

    except Exception as e:
        logger.exception("Помилка при обробці голосу:")
        await update.message.reply_text("⚠️ Виникла помилка при обробці повідомлення.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
