import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI
from pydub import AudioSegment
import uuid

# Завантаження .env
load_dotenv()

# Налаштування
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Логування
logging.basicConfig(level=logging.INFO)

# OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# FFmpeg шлях (для Render/хостингу не потрібно)
AudioSegment.converter = "ffmpeg"  # або повний шлях, якщо локально

# Обробка голосових повідомлень
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)

    # Завантажуємо файл
    ogg_path = f"{uuid.uuid4()}.ogg"
    wav_path = f"{uuid.uuid4()}.wav"
    await file.download_to_drive(ogg_path)

    # Конвертація .ogg → .wav
    sound = AudioSegment.from_file(ogg_path)
    sound.export(wav_path, format="wav")

    # Розпізнавання через OpenAI Whisper
    with open(wav_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    # Відправляємо розпізнаний текст
    await update.message.reply_text(f"📝 Розпізнаний текст:\n{transcript.text}")

    # Очищення
    os.remove(ogg_path)
    os.remove(wav_path)

# Головна функція
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()

if __name__ == "__main__":
    main()
