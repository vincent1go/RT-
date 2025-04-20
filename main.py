import os
import logging
import pytz
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PyPDF2 import PdfReader, PdfWriter

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

TEMPLATE_PATH = "template.pdf"

def get_london_date():
    london_time = datetime.now(pytz.timezone("Europe/London"))
    return london_time.strftime("%d.%m.%Y")

def replace_text_in_pdf(input_path, output_path, old_name, new_name, old_date, new_date):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        content = page.extract_text()
        if content:
            content = content.replace(old_name, new_name).replace(old_date, new_date)
        writer.add_page(page)
    
    writer.write(output_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши имя клиента, например:
Имя клиента: Иван Иванов")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    if message.lower().startswith("имя клиента:"):
        client_name = message.split(":", 1)[1].strip()
        old_name = "TURSUNOV MUMIN FA4837585"
        old_date = "19.04.2025"
        today = get_london_date()

        output_path = f"{client_name}.pdf"
        replace_text_in_pdf(TEMPLATE_PATH, output_path, old_name, client_name, old_date, today)

        with open(output_path, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=output_path))

        os.remove(output_path)
    else:
        await update.message.reply_text("Пожалуйста, введите имя клиента в формате:
Имя клиента: Иван Иванов")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
