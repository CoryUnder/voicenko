import os
import logging
import tempfile
import ffmpeg
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes
)
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APP_URL = "https://worker-production-b2dd.up.railway.app"

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
        await file.download_to_drive(ogg_file.name)
        ogg_path = ogg_file.name
    mp3_path = ogg_path.replace(".ogg", ".mp3")

    ffmpeg.input(ogg_path).output(mp3_path).run(overwrite_output=True)

    with open(mp3_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1"
        )

    await update.message.reply_text(f"Розшифровка: {transcript.text}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
