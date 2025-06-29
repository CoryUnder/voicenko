import os
import logging
import tempfile
import ffmpeg
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI, RateLimitError, AuthenticationError

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DOMAIN = os.environ.get("DOMAIN")  # наприклад: 'https://worker-production-b2dd.up.railway.app'

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    await message.reply_text("🎧 Отримано голосове повідомлення. Обробляю його...")

    try:
        file = await context.bot.get_file(message.voice.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as ogg_file:
            await file.download_to_drive(custom_path=ogg_file.name)
            ogg_path = ogg_file.name

        mp3_path = ogg_path.replace(".oga", ".mp3")

        for i in range(1, 11):
            await message.reply_text(f"🔄 Обробка {i * 10}%")

        ffmpeg.input(ogg_path).output(mp3_path).run(overwrite_output=True)

        with open(mp3_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        text = transcription.text
        await message.reply_text(f"📄 Ось ваш текст:\n{text}")

    except RateLimitError:
        await message.reply_text("⚠️ Перевищено ліміт OpenAI. Спробуйте пізніше або перевірте баланс.")
    except AuthenticationError:
        await message.reply_text("❌ API ключ OpenAI недійсний або відсутній.")
    except Exception as e:
        logger.error("Помилка при обробці голосу:", exc_info=e)
        await message.reply_text("❗️ Сталася помилка при розпізнаванні голосу. Спробуйте ще раз.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Надсилати потрібно *голосові повідомлення*, а не текст.", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=f"{DOMAIN}/webhook"
    )
