import os
import re
import logging
import pytz
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import fitz  # PyMuPDF

# Конфигурация
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # ID администратора Telegram (опционально)
if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Проверь переменные окружения.")

TEMPLATE_PATH = "template.pdf"
OLD_NAME = "TURSUNOV MUMIN FA4837585"
OLD_DATE = "19.04.2025"
COLOR = (69 / 255, 69 / 255, 69 / 255)  # #454545
FONT_PATH = "fonts/times.ttf"  # Путь к файлу шрифта

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Получение текущей даты по Лондону
def get_london_date():
    london_time = datetime.now(pytz.timezone("Europe/London"))
    return london_time.strftime("%d.%m.%Y")

# Вставка текста поверх старого с сохранением стиля
def replace_text(page, old_text, new_text):
    areas = page.search_for(old_text)
    for area in areas:
        text_info = page.get_text("dict", clip=area)
        font_size = 12
        font_name = "helv"

        for block in text_info["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_size = span.get("size", 12)
                    font_name = span.get("font", "helv")
                    break

        page.add_redact_annot(area, fill=(1, 1, 1))
    page.apply_redactions()

    for area in areas:
        x = area.x0
        y = area.y1 - font_size * 0.2
        page.insert_text(
            (x, y),
            new_text,
            fontname="times_roman",
            fontsize=font_size,
            color=COLOR,
            fontfile=FONT_PATH
        )

# Обработка PDF: заменяем имя и дату
def replace_text_in_pdf(input_path, output_path, old_name, new_name, old_date, new_date):
    doc = fitz.open(input_path)
    for page in doc:
        replace_text(page, old_name, new_name)
        replace_text(page, old_date, new_date)
    doc.save(output_path)

# Уведомление админа об ошибке
async def notify_admin(context, message):
    if ADMIN_ID:
        try:
            await context.bot.send_message(chat_id=int(ADMIN_ID), text=message)
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение админу: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши имя клиента, например: Иван Иванов")

# Обработка сообщения с именем клиента
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client_name = update.message.text.strip()

    if not client_name:
        await update.message.reply_text("Пожалуйста, введите имя клиента.")
        return

    try:
        # Очистка имени от опасных символов
        safe_name = re.sub(r'[^a-zA-Zа-яА-Я0-9\s-]', '', client_name).strip()
        if not safe_name:
            await update.message.reply_text("Имя клиента содержит недопустимые символы.")
            return

        today = get_london_date()
        output_path = f"{safe_name}.pdf"

        replace_text_in_pdf(TEMPLATE_PATH, output_path, OLD_NAME, client_name, OLD_DATE, today)

        with open(output_path, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=output_path))

        os.remove(output_path)
        logging.info(f"Успешно сгенерирован PDF для: {client_name}")

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await notify_admin(context, f"Произошла ошибка у пользователя {update.effective_user.id}: {e}")
        await update.message.reply_text("Произошла ошибка при обработке. Попробуйте позже.")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
