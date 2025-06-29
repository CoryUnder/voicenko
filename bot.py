import os
import logging
import subprocess
import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI, OpenAIError

# Ініціалізація OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Встановлення логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішліть голосове повідомлення, і я розпізнаю його в текст.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Цей бот працює тільки з голосовими повідомленнями. Надішліть голосове!")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        ogg_path = "voice.ogg"
        mp3_path = "voice.mp3"
        await file.download_to_drive(ogg_path)

        await update.message.reply_text("🧠 Обробляю голос...")

        # Прелоадер (імітація)
        for i in range(0, 101, 25):
            await update.message.reply_text(f"⏳ Розпізнаю... {i}%")
            time.sleep(0.4)

        # Конвертація в mp3
        subprocess.run([
            "ffmpeg", "-i", ogg_path, mp3_path, "-y"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with open(mp3_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )

        await update.message.reply_text(f"✅ Ось ваш текст:\n\n{transcription}")

    except OpenAIError as e:
        logger.error("OpenAI error: %s", e)
        await update.message.reply_text("❌ Сталася помилка з OpenAI: ймовірно, вичерпано ліміт. Спробуйте пізніше.")
    except Exception as e:
        logger.error("Інша помилка: %s", e)
        await update.message.reply_text("⚠️ Виникла помилка під час обробки. Перевірте файл і спробуйте ще раз.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))

    app.run_webhook(
        listen="0.0.0.0",
        port=8000,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
