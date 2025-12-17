import json
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Load JSON file
with open("syllabus.json", "r") as f:
    raw = json.load(f)
    DATA = json.loads(raw)

SUBJECTS = DATA["syllabus"]["subjects"]

def get_subject_syllabus(subject_name: str):
    for subject in SUBJECTS:
        if subject["subject_name"].lower() == subject_name.lower():
            units = subject["syllabus"]
            text = ""
            for unit, content in units.items():
                text += f"{unit.replace('_', ' ').upper()}:\n{content}\n\n"
            return text.strip()
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("BSc Physical Science", callback_data="course_bsc_ps")]]
    await update.message.reply_text(
        "Welcome!\n\nSelect your course:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def course_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["course"] = "BSc Physical Science"

    keyboard = [[InlineKeyboardButton("Semester 4", callback_data="semester_4")]]
    await query.message.reply_text(
        "Select semester:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def semester_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["semester"] = "Semester 4"

    keyboard = [
        [InlineKeyboardButton("Physics", callback_data="subject_Physics")],
        [InlineKeyboardButton("Chemistry", callback_data="subject_Chemistry")],
        [InlineKeyboardButton("Maths", callback_data="subject_Maths")],
    ]

    await query.message.reply_text(
        "Select subject:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subject_name = query.data.replace("subject_", "")
    syllabus_text = get_subject_syllabus(subject_name)

    await query.message.reply_text(
        f"{context.user_data['course']} – {context.user_data['semester']}\n\n"
        f"{subject_name} – Theory Syllabus\n\n{syllabus_text}"
    )
     print("BOT_TOKEN value:", BOT_TOKEN)
async def main():
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(course_handler, pattern="^course_"))
    app.add_handler(CallbackQueryHandler(semester_handler, pattern="^semester_"))
    app.add_handler(CallbackQueryHandler(subject_handler, pattern="^subject_"))

    print("Bot started...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
