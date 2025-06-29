import os
import subprocess
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import uuid

# Ініціалізація
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-railway-url.up.railway.app

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)

# Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот для розпізнавання голосових повідомлень. Просто надішли мені voice, і я надішлю текст!"
    )

# Обробка тексту — ігноруємо
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Надішли голосове повідомлення. Я працюю тільки з voice/audio.")

# Обробка голосових
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🎧 Обробляю аудіо… (0%)")

        file = await context.bot.get_file(update.message.voice.file_id)
        ogg_path = f"voice_{uuid.uuid4().hex}.oga"
        mp3_path = ogg_path.replace(".oga", ".mp3")
        await file.download_to_drive(ogg_path)

        await update.message.reply_text("🔄 Конвертація в MP3… (33%)")
        subprocess.run(["ffmpeg", "-i", ogg_path, mp3_path], check=True)

        await update.message.reply_text("🧠 Надсилаю на OpenAI… (66%)")
        with open(mp3_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        await update.message.reply_text(f"✅ Готово! Ось ваш текст:\n\n{transcription.text}")

    except Exception as e:
        logging.error("Помилка при обробці голосу:", exc_info=True)
        await update.message.reply_text("❌ Сталася помилка під час обробки. Можливо, перевищено ліміт OpenAI або файл пошкоджено.")
    finally:
        # Очищення файлів
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(mp3_path): os.remove(mp3_path)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Запуск як вебхук
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
