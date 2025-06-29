import os
import logging
import tempfile
import asyncio
import aiohttp

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # наприклад: "https://worker-production-xxxx.up.railway.app"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === START MESSAGE ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Я розпізнаю голосові повідомлення 🎙️.\n\n"
        "📤 Просто надішли мені голосове — я розшифрую його в текст!\n\n"
        "❌ Текстові повідомлення не обробляються."
    )

# === TEXT MESSAGE ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Надішли голосове повідомлення, а не текст 🙃")

# === VOICE MESSAGE ===
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        # завантажуємо .oga у тимчасовий файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as temp_ogg:
            await file.download_to_drive(custom_path=temp_ogg.name)
            ogg_path = temp_ogg.name

        await update.message.reply_text("⏳ Розпізнаю голос... [0%]")

        # читаємо файл та надсилаємо до Deepgram
        with open(ogg_path, "rb") as audio_file:
            headers = {
                "Authorization": f"Token {DEEPGRAM_API_KEY}"
            }
            params = {
                "punctuate": "true",
                "language": "uk"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.deepgram.com/v1/listen",
                    headers=headers,
                    params=params,
                    data=audio_file
                ) as response:
                    if response.status != 200:
                        error_json = await response.text()
                        logger.error(f"Deepgram error: {response.status} - {error_json}")
                        await update.message.reply_text("⚠️ Помилка при розпізнаванні. Спробуйте ще раз пізніше.")
                        return

                    data = await response.json()

        text = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
        if text:
            await update.message.reply_text(f"✅ Ось ваш текст:\n\n{text}")
        else:
            await update.message.reply_text("😕 Не вдалося розпізнати голос. Спробуйте ще раз!")

    except Exception as e:
        logger.exception("Помилка при обробці голосу:")
        await update.message.reply_text("❌ Сталася технічна помилка при обробці. Повідомлення не розпізнано.")

# === MAIN ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
