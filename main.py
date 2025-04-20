import os
import logging
import pytz
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import fitz  # PyMuPDF

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Проверь переменные окружения.")
logging.basicConfig(level=logging.INFO)

TEMPLATE_PATH = "template.pdf"

def get_london_date():
    london_time = datetime.now(pytz.timezone("Europe/London"))
    return london_time.strftime("%d.%m.%Y")

def replace_text_in_pdf(input_path, output_path, old_name, new_name, old_date, new_date):
    # Открываем PDF с помощью PyMuPDF
    doc = fitz.open(input_path)

    for page in doc:
        text_instances = page.search_for(old_name)
        for inst in text_instances:
            page.insert_text(inst[:2], new_name, fontsize=12)  # Заменить имя

        text_instances = page.search_for(old_date)
        for inst in text_instances:
            page.insert_text(inst[:2], new_date, fontsize=12)  # Заменить дату

    doc.save(output_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши имя клиента, например: Иван Иванов")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client_name = update.message.text.strip()
    
    if len(client_name.split()) >= 2:  # Простейшая проверка — есть ли имя и фамилия
        old_name = "TURSUNOV MUMIN FA4837585"
        old_date = "19.04.2025"
        today = get_london_date()

        output_path = f"{client_name}.pdf"
        replace_text_in_pdf(TEMPLATE_PATH, output_path, old_name, client_name, old_date, today)

        with open(output_path, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=output_path))

        os.remove(output_path)
    else:
        await update.message.reply_text("Пожалуйста, введите полное имя клиента (имя и фамилию).")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
