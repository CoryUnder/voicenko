import os
import openai
import ffmpeg
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    ogg_path = "voice.ogg"
    mp3_path = "voice.mp3"

    await file.download_to_drive(ogg_path)

    # Конвертуємо .ogg в .mp3
    ffmpeg.input(ogg_path).output(mp3_path).run(overwrite_output=True)

    # Відправляємо в Whisper
    with open(mp3_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    
    await update.message.reply_text(transcript["text"])

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.run_polling()
