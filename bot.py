import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========== ENV ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found")

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL not found")

PORT = int(os.environ.get("PORT", 10000))

# ========== DATA ==========
with open("syllabus.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

COURSES = [DATA["syllabus"]["course_name"]]
SEMESTERS = [
    "Semester 1", "Semester 2", "Semester 3",
    "Semester 4", "Semester 5", "Semester 6"
]

# ========== HELPERS ==========
def build_buttons(options):
    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    return InlineKeyboardMarkup(keyboard)

# ========== HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Select your course:",
        reply_markup=build_buttons(COURSES)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in COURSES:
        context.user_data["course"] = data
        await query.edit_message_text(
            f"Course selected: {data}\nNow select your semester:",
            reply_markup=build_buttons(SEMESTERS)
        )
        return

    if data in SEMESTERS:
        context.user_data["semester"] = data
        subjects = [s["subject_name"] for s in DATA["syllabus"]["subjects"]]
        context.user_data["subjects"] = subjects
        await query.edit_message_text(
            f"{data} selected.\nNow select your subject:",
            reply_markup=build_buttons(subjects)
        )
        return

    subjects = context.user_data.get("subjects", [])
    if data in subjects:
        for sub in DATA["syllabus"]["subjects"]:
            if sub["subject_name"] == data:
                text = ""
                for unit, content in sub["syllabus"].items():
                    text += f"*{unit}*\n{content}\n\n"
                await query.edit_message_text(text=text, parse_mode="Markdown")
                return

async def syllabus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use the buttons to navigate the syllabus.")

# ========== MAIN ==========
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("syllabus", syllabus_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Starting webhook...")

    app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )
