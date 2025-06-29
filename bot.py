import os
import logging
import tempfile

import httpx
import ffmpeg

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from openai import OpenAI

# Ініціалізація логування
logging.basicConfig(level=logging.INFO)

# Змінні середовища
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://worker-production-b2dd.up.railway.app"

client = OpenAI(api_key=OPENAI_API_KEY)

# Привітання при /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Надішли мені голосове повідомлення — я розпізнаю його текст.\n\n"
        "🎙 Підтримуються короткі повідомлення (до 1 хв).\n"
        "❗ Якщо буде помилка — я скажу."
    )

# Обробка голосових повідомлень
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Повідомлення що бот працює
    await update.message.reply_text("🔄 Обробляю голосове повідомлення...")

    try:
        # Отримання файлу
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        # Збереження .ogg файлу
        with tempfile.TemporaryDirectory() as tmp_dir:
            ogg_path = os.path.join(tmp_dir, "audio.ogg")
            mp3_path = os.path.join(tmp_dir, "audio.mp3")

            await file.download_to_drive(ogg_path)

            # Конвертація в mp3
            ffmpeg.input(ogg_path).output(mp3_path).run(overwrite_output=True)

            # Відкриття файлу для OpenAI
            with open(mp3_path, "rb") as audio_file:
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

# Старт бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команди
    app.add_handler(CommandHandler("start", start))

    # Голосові повідомлення
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Запуск через webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        webhook_url=f"{WEBHOOK_URL}/"
    )
