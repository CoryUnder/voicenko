import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from pydub import AudioSegment
import openai
import tempfile

AudioSegment.converter = "ffmpeg"

TELEGRAM_TOKEN = "7666854886:AAGtKS47fqbAAFXykQFo-DS9_SZTSDF9JYg"
openai.api_key = "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"

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice or update.message.audio
    if not voice:
        await update.message.reply_text("Будь ласка, надішли голосове або аудіофайл.")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_ogg:
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(tmp_ogg.name)
        audio = AudioSegment.from_file(tmp_ogg.name)
        wav_path = tmp_ogg.name.replace(".ogg", ".wav")
        audio.export(wav_path, format="wav")

    with open(wav_path, "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
    text = transcription["text"]
    await update.message.reply_text(f"📝 Розпізнаний текст:
{text}")

    summary_prompt = f"Скороти і стисни суть:
{text}"
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ти асистент, що створює короткі резюме."},
            {"role": "user", "content": summary_prompt}
        ]
    )
    result = summary.choices[0].message.content
    await update.message.reply_text(f"📌 Резюме:
{result}")

    os.remove(tmp_ogg.name)
    os.remove(wav_path)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.run_polling()
