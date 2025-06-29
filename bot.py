import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI
import logging

# Init
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.environ.get("PORT", 8443))
URL = "https://worker-production-b2dd.up.railway.app"

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Надішли мені голосове повідомлення 🎙️")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    ogg_path = "voice.ogg"
    mp3_path = "voice.mp3"

    await file.download_to_drive(ogg_path)

    # Конвертація в mp3
    import ffmpeg
    ffmpeg.input(ogg_path).output(mp3_path).run(overwrite_output=True)

    # Відправка в OpenAI
    with open(mp3_path, "rb") as f:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
    
    await update.message.reply_text(f"Розпізнаний текст: {transcript.text}")

# Init app
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

# Webhook запуск
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=URL,
)
