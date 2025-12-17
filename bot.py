import telegram
print("RUNNING PTB VERSION:", telegram.__version__)
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Load bot token from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found in environment variables")

# Load syllabus JSON
with open("syllabus.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

COURSES = [DATA["syllabus"]["course_name"]]  # Adjust if more courses added
SEMESTERS = ["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 6"]

# Helper function to generate buttons
def build_buttons(options):
    keyboard = []
    for opt in options:
        keyboard.append([InlineKeyboardButton(opt, callback_data=opt)])
    return InlineKeyboardMarkup(keyboard)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Select your course:",
        reply_markup=build_buttons(COURSES)
    )

# CallbackQuery for buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Step 1: Course selection
    if data in COURSES:
        context.user_data["course"] = data
        await query.edit_message_text(
            text=f"Course selected: {data}\nNow select your semester:",
            reply_markup=build_buttons(SEMESTERS)
        )
        return

    # Step 2: Semester selection
    if data in SEMESTERS:
        context.user_data["semester"] = data
        # Get subjects for this semester from JSON
        subjects = [sub["subject_name"] for sub in DATA["syllabus"]["subjects"]]
        context.user_data["subjects"] = subjects
        await query.edit_message_text(
            text=f"{data} selected.\nNow select your subject:",
            reply_markup=build_buttons(subjects)
        )
        return

    # Step 3: Subject selection
    subjects = context.user_data.get("subjects", [])
    if data in subjects:
        context.user_data["subject"] = data
        # Find syllabus for this subject
        for sub in DATA["syllabus"]["subjects"]:
            if sub["subject_name"] == data:
                syllabus = sub["syllabus"]
                text = ""
                for unit, content in syllabus.items():
                    text += f"*{unit}*\n{content}\n\n"
                await query.edit_message_text(text=text, parse_mode="Markdown")
                return

# Fallback /syllabus command (optional)
async def syllabus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use the buttons to navigate syllabus selection.")

# MAIN
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("syllabus", syllabus_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Run long polling
    print("Bot started and listening for updates")
    app.run_polling()
