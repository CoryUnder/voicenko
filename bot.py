import os
import logging
import ffmpeg
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from uuid import uuid4

# Логи
logging.basicConfig(level=logging.INFO)

# Токени
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = "https://worker-production-b2dd.up.railway.app"

# OpenAI клієнт
client = OpenAI(api_key=OPENAI_API_KEY)

# Привітання
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Це бот, який розпізнає голосові повідомлення та перетворює їх на текст.\n\n"
        "🎙 Надішли мені голосове повідомлення — і я розшифрую його в текст.\n\n"
        "⚠️ Підтримуються тільки повідомлення, записані у Telegram (формат .ogg)."
    )

# Обробка голосу
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    ogg_path = f"{uuid4()}.ogg"
    mp3_path = f"{uuid4()}.mp3"

    await file.download_to_drive(ogg_path)

    # Конвертація ogg → mp3
    ffmpeg.input(ogg_path).output(mp3_path).run(overwrite_output=True)

    # Відправка в OpenAI
    with open(mp3_path, "rb") as f:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)

    await update.message.reply_text(f"📝 Текст повідомлення:\n{transcript.text}")

    # Очистка
    os.remove(ogg_path)
    os.remove(mp3_path)

# Ініціалізація
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

# Webhook-запуск
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    webhook_url=WEBHOOK_URL
)
