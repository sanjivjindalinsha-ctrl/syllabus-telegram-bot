import json
from pathlib import Path
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ----------------- LOAD DATA -----------------



BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

with open(DATA_DIR / "courses.json", encoding="utf-8") as f:
    COURSES = json.load(f)["courses"]

with open(DATA_DIR / "syllabus.json", encoding="utf-8") as f:
    SYLLABUS = json.load(f)
# ----------------- KEYBOARD BUILDERS -----------------

def build_course_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(course["display_name"], callback_data=f"C|{cid}")]
        for cid, course in COURSES.items()
    ])


def build_semester_keyboard(course_id):
    duration = COURSES[course_id]["duration"]
    keyboard = [
        [InlineKeyboardButton(f"Semester {i}", callback_data=f"S|{course_id}|{i}")]
        for i in range(1, duration + 1)
    ]
    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="B|COURSE")])
    return InlineKeyboardMarkup(keyboard)


def build_role_keyboard(course_id, semester):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Major", callback_data=f"R|{course_id}|{semester}|major"),
            InlineKeyboardButton("Minor", callback_data=f"R|{course_id}|{semester}|minor")
        ],
        [InlineKeyboardButton("⬅ Back", callback_data=f"B|SEM|{course_id}")]
    ])


def build_subject_keyboard(course_id, semester, role):
    keyboard = []

    for sid, subject in SYLLABUS.items():

        # Common components (AEC/MDC/SEC/VAC)
        if subject.get("common_component"):
            if semester > 4:
                continue
        else:
            if course_id not in subject.get("applicable_courses", []):
                continue

        if role not in subject["syllabus_by_role"]:
            continue

        if str(semester) not in subject["syllabus_by_role"][role]["semesters"]:
            continue

        keyboard.append([
            InlineKeyboardButton(
                subject["display_name"],
                callback_data=f"U|{course_id}|{semester}|{role}|{sid}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data=f"B|ROLE|{course_id}|{semester}")
    ])

    return InlineKeyboardMarkup(keyboard)


def build_content_keyboard(course_id, semester, role, subject_id):
    subject = SYLLABUS[subject_id]
    semester_data = subject["syllabus_by_role"][role]["semesters"][str(semester)]

    keyboard = []

    if "theory" in semester_data:
        keyboard.append([
            InlineKeyboardButton(
                "📘 Theory",
                callback_data=f"T|{course_id}|{semester}|{role}|{subject_id}|theory"
            )
        ])

    if subject["type"] == "theory_practical":
        keyboard.append([
            InlineKeyboardButton(
                "🧪 Practical",
                callback_data=f"T|{course_id}|{semester}|{role}|{subject_id}|practical"
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("❓ Important Questions",
                              callback_data=f"T|{course_id}|{semester}|{role}|{subject_id}|important")],
        [InlineKeyboardButton("📄 Previous Year Papers",
                              callback_data=f"T|{course_id}|{semester}|{role}|{subject_id}|papers")],
        [InlineKeyboardButton("⬅ Back",
                              callback_data=f"B|SUB|{course_id}|{semester}|{role}")]
    ])

    return InlineKeyboardMarkup(keyboard)


# ----------------- HANDLERS -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Select your course:",
        reply_markup=build_course_keyboard()
    )


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|")
    action = parts[0]

    # ---------- COURSE ----------
    if action == "C":
        course_id = parts[1]
        await query.edit_message_text(
            "Select Semester:",
            reply_markup=build_semester_keyboard(course_id)
        )

    # ---------- SEMESTER ----------
    elif action == "S":
        course_id, semester = parts[1], int(parts[2])
        if semester in (1, 2):
            await query.edit_message_text(
                "Select Major / Minor:",
                reply_markup=build_role_keyboard(course_id, semester)
            )
        else:
            await query.edit_message_text(
                "Select Subject:",
                reply_markup=build_subject_keyboard(course_id, semester, "regular")
            )

    # ---------- ROLE ----------
    elif action == "R":
        course_id, semester, role = parts[1], int(parts[2]), parts[3]
        await query.edit_message_text(
            "Select Subject:",
            reply_markup=build_subject_keyboard(course_id, semester, role)
        )

    # ---------- SUBJECT ----------
    elif action == "U":
        course_id, semester, role, subject_id = parts[1], int(parts[2]), parts[3], parts[4]
        await query.edit_message_text(
            f"{SYLLABUS[subject_id]['display_name']} – Options:",
            reply_markup=build_content_keyboard(course_id, semester, role, subject_id)
        )

    # ---------- CONTENT ----------
    elif action == "T":
        course_id, semester, role, subject_id, content = parts[1], int(parts[2]), parts[3], parts[4], parts[5]
        subject = SYLLABUS[subject_id]
        data = subject["syllabus_by_role"][role]["semesters"][str(semester)]

        text = f"*{subject['display_name']} – Semester {semester}*\n\n"

        if content == "theory":
            units = data.get("theory", {}).get("units", {})
            text += "\n".join(f"• {u}: {v}" for u, v in units.items()) or "Theory syllabus will be added soon."

        elif content == "practical":
            practicals = data.get("practical", [])
            text += "\n".join(practicals) or "Practical syllabus will be added soon."

        elif content == "important":
            text += "Important questions will be added soon."

        elif content == "papers":
            text += "Previous year papers will be added soon."

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=build_content_keyboard(course_id, semester, role, subject_id)
        )

    # ---------- BACK ----------
    elif action == "B":
        target = parts[1]

        if target == "COURSE":
            await query.edit_message_text("Select your course:", reply_markup=build_course_keyboard())

        elif target == "SEM":
            course_id = parts[2]
            await query.edit_message_text("Select Semester:", reply_markup=build_semester_keyboard(course_id))

        elif target == "ROLE":
            course_id, semester = parts[2], int(parts[3])
            await query.edit_message_text(
                "Select Major / Minor:",
                reply_markup=build_role_keyboard(course_id, semester)
            )

        elif target == "SUB":
            course_id, semester, role = parts[2], int(parts[3]), parts[4]
            await query.edit_message_text(
                "Select Subject:",
                reply_markup=build_subject_keyboard(course_id, semester, role)
            )


# ----------------- APP ENTRY -----------------

def main():
    app = Application.builder().token("8595562875:AAFwY3aIS7fKB-fR1AqhOgLIbAgD9g9BEuE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_router))

    app.run_webhook(
        listen="0.0.0.0",
        port=8443,
        webhook_url="https://syllabus-telegram-bot.onrender.com"
    )


if __name__ == "__main__":
    main()
