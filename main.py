import os
import logging
import pytz
import fitz  # PyMuPDF
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Проверь переменные окружения.")
logging.basicConfig(level=logging.INFO)

TEMPLATE_PATH = "template.pdf"

def get_london_date():
    london_time = datetime.now(pytz.timezone("Europe/London"))
    return london_time.strftime("%d.%m.%Y")

def replace_text_in_pdf(input_path, output_path, old_name, new_name, old_date, new_date):
    doc = fitz.open(input_path)

    for page in doc:
        # Заменяем имя
        name_boxes = page.search_for(old_name)
        for box in name_boxes:
            page.add_redact_annot(box, fill=(1, 1, 1))  # белая подложка
        page.apply_redactions()
        for box in name_boxes:
            page.insert_text(box[:2], new_name, fontsize=11, color=(0, 0, 0))

        # Заменяем дату
        date_boxes = page.search_for(old_date)
        for box in date_boxes:
            page.add_redact_annot(box, fill=(1, 1, 1))
        page.apply_redactions()
        for box in date_boxes:
            page.insert_text(box[:2], new_date, fontsize=11, color=(0, 0, 0))

    doc.save(output_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши имя клиента, например: Иван Иванов")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client_name = update.message.text.strip()

    if len(client_name.split()) >= 2:
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
