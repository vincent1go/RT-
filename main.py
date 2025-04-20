import os
import logging
import pytz
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import fitz  # PyMuPDF

# Конфигурация
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Проверь переменные окружения.")

TEMPLATE_PATH = "template.pdf"
OLD_NAME = "TURSUNOV MUMIN FA4837585"
OLD_DATE = "19.04.2025"
COLOR = (69 / 255, 69 / 255, 69 / 255)  # #454545
FONT_PATH = "fonts/times.ttf"  # Путь к файлу шрифта

logging.basicConfig(level=logging.INFO)

# Получение текущей даты по Лондону
def get_london_date():
    london_time = datetime.now(pytz.timezone("Europe/London"))
    return london_time.strftime("%d.%m.%Y")

# Вставка текста поверх старого с сохранением стиля
def replace_text(page, old_text, new_text):
    areas = page.search_for(old_text)
    for area in areas:
        # Извлечение оригинального стиля текста
        text_info = page.get_text("dict", clip=area)
        font_size = 12
        font_name = "helv"

        for block in text_info["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_size = span.get("size", 12)
                    font_name = span.get("font", "helv")
                    break

        # Закрасить старый текст
        page.add_redact_annot(area, fill=(1, 1, 1))  # белый прямоугольник
    page.apply_redactions()

    # Вставить новый текст в найденные области
    for area in areas:
        x = area.x0
        y = area.y1 - font_size * 0.2  # выравнивание по базовой линии

        # Используем шрифт из папки "folders"
        page.insert_text(
            (x, y),
            new_text,
            fontname="times_roman",  # Название шрифта
            fontsize=font_size,
            color=COLOR,
            fontfile=FONT_PATH  # Путь к файлу шрифта
        )

# Обработка PDF: заменяем имя и дату
def replace_text_in_pdf(input_path, output_path, old_name, new_name, old_date, new_date):
    doc = fitz.open(input_path)

    for page in doc:
        replace_text(page, old_name, new_name)
        replace_text(page, old_date, new_date)

    doc.save(output_path)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши имя клиента, например: Иван Иванов")

# Обработка сообщения с именем клиента
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client_name = update.message.text.strip()
    
    if len(client_name.split()) >= 2:
        today = get_london_date()
        output_path = f"{client_name}.pdf"

        replace_text_in_pdf(TEMPLATE_PATH, output_path, OLD_NAME, client_name, OLD_DATE, today)

        with open(output_path, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=output_path))

        os.remove(output_path)
    else:
        await update.message.reply_text("Пожалуйста, введите полное имя клиента (имя и фамилию).")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

