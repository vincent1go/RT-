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

    def replace_text(page, old_text, new_text):
        areas = page.search_for(old_text)
        for area in areas:
            # Попытка извлечь стиль текста
            text_info = page.get_text("dict", clip=area)
            font_size = 12
            font_name = "helv"
            color = (0, 0, 0)

            for block in text_info["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_size = span.get("size", 12)
                        font_name = span.get("font", "helv")
                        color = span.get("color", 0)
                        break

            # Удаляем оригинальный текст
            page.add_redact_annot(area, fill=(1, 1, 1))
        page.apply_redactions()

        for area in areas:
            x, y = area.x0, area.y1 - font_size * 0.2  # выравнивание по базовой линии
            page.insert_text(
                (x, y),
                new_text,
                fontname=font_name,
                fontsize=font_size,
                color=fitz.utils.get_color(color)
            )

    for page in doc:
        replace_text(page, old_name, new_name)
        replace_text(page, old_date, new_date)

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
