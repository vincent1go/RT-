import os
import fitz  # PyMuPDF
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
TEMPLATE_PATH = "template.pdf"
OUTPUT_FOLDER = "output"
OLD_NAME = "John Doe"
OLD_DATE = "01.01.2024"
FONT_PATH = "fonts/times.ttf"  # путь к файлу шрифта

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def replace_text(page, old_text, new_text, color="#000000"):
    areas = page.search_for(old_text)
    for area in areas:
        page.add_redact_annot(area, fill=(1, 1, 1))
    page.apply_redactions()

    for area in areas:
        page.insert_text(
            area.tl,
            new_text,
            fontfile=FONT_PATH,
            fontsize=12,
            color=fitz.parse_color(color),
            overlay=True,
        )

def replace_text_in_pdf(input_path, output_path, old_name, new_name, old_date, new_date):
    doc = fitz.open(input_path)
    for page in doc:
        replace_text(page, old_name, new_name, "#454545")
        replace_text(page, old_date, new_date, "#454545")
    doc.save(output_path)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client_name = update.message.text.strip()
    today = datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=0)))
    today = today.strftime("%d.%m.%Y")

    output_filename = f"{client_name.replace(' ', '_')}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    replace_text_in_pdf(TEMPLATE_PATH, output_path, OLD_NAME, client_name, OLD_DATE, today)

    with open(output_path, "rb") as f:
        await update.message.reply_document(f, filename=output_filename)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started...")
    app.run_polling()
