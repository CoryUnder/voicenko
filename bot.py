import os
import logging
import tempfile

import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from openai import OpenAI

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Секрети
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://worker-production-b2dd.up.railway.app"

client = OpenAI(api_key=OPENAI_API_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Надішли мені голосове повідомлення — я розпізнаю його текст.\n\n"
        "🎙 Підтримуються короткі повідомлення (до 1 хв).\n"
        "❗ Якщо буде помилка — я скажу."
    )

# Голосові
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Обробляю голосове повідомлення...")

    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        with tempfile.TemporaryDirectory() as tmp_dir:
            ogg_path = os.path.join(tmp_dir, "voice.ogg")
            await file.download_to_drive(ogg_path)

            with open(ogg_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )

            text = transcription.text.strip()
            if text:
                await update.message.reply_text(f"📝 Ось ваш текст:\n\n{text}")
            else:
                await update.message.reply_text("⚠️ Не вдалося розпізнати голос. Спробуйте ще раз.")

    except Exception as e:
        logging.exception("Помилка при обробці голосу:")
        await update.message.reply_text("❌ Сталася помилка під час обробки. Спробуйте пізніше.")

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        webhook_url=f"{WEBHOOK_URL}/"
    )
