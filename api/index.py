import os
import logging
import asyncio
import nest_asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from datetime import datetime
import platform

# === Flask (keep-alive for Render port 8080) ===
app_keep_alive = Flask(__name__)

@app_keep_alive.route('/')
def home():
    return '✅ Bot is running.'

def run_flask():
    app_keep_alive.run(host='0.0.0.0', port=8080)

# === Conversation states ===
ROOM_TYPE, LOCATION, CLIENT_ISSUES, CLIENT_GOALS, WHAT_DONE, SPECIAL_FEATURES, MEDIA_BEFORE, MEDIA_AFTER, MEDIA_VISUAL, DONE = range(10)

# === Logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏗️ Let's start a new remodeling project.\n"
        "What room did you work on? (e.g. kitchen, bathroom, laundry room)"
    )
    return ROOM_TYPE

async def get_room_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['room_type'] = update.message.text
    await update.message.reply_text("📍 In which city and state was this project completed?")
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text
    await update.message.reply_text("❓ What wasn’t working or needed improvement in that space before the remodel?")
    return CLIENT_ISSUES

async def get_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['issues'] = update.message.text
    await update.message.reply_text("🌟 What did the homeowner want to achieve or change?")
    return CLIENT_GOALS

async def get_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['goals'] = update.message.text
    await update.message.reply_text("💪 What did your team do in this project? (Key work completed)")
    return WHAT_DONE

async def get_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['what_done'] = update.message.text
    await update.message.reply_text("✨ Did you use any special materials, custom features, or design ideas?")
    return SPECIAL_FEATURES

async def get_special(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['special'] = update.message.text
    context.user_data['media'] = {'before': [], 'after': [], 'visualization': []}
    await update.message.reply_text(
        "📸 Let's upload media now.\n"
        "Step 1: Please send photos/videos taken BEFORE the remodel.\n"
        "When you're finished, type /next to continue.\n\n"
        "⚠️ Telegram size limits:\n- Photos: max 20 MB\n- Videos: max 50 MB"
    )
    return MEDIA_BEFORE

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    file = update.message.photo[-1] if update.message.photo else update.message.video
    file_id = file.file_id
    file_obj = await context.bot.get_file(file_id)
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{file_id}.jpg" if update.message.photo else f"downloads/{file_id}.mp4"
    await file_obj.download_to_drive(file_path)

    context.user_data['media'][category].append(file_path)
    logger.info(f"Saved {category} file: {file_path}")

    await update.message.reply_text("✅ File saved. You can send more or type /next to continue.")

    try:
        os.remove(file_path)
        logger.info(f"Deleted file after processing: {file_path}")
    except Exception as e:
        logger.warning(f"Could not delete file {file_path}: {e}")
    return getattr(globals(), f"MEDIA_{category.upper()}")

async def get_media_before(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handle_media(update, context, 'before')

async def get_media_after(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handle_media(update, context, 'after')

async def get_media_visual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handle_media(update, context, 'visualization')

async def next_to_after(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Step 2: Now send AFTER photos/videos of the finished space.\nWhen done, type /next to continue.")
    return MEDIA_AFTER

async def next_to_visual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📐 Step 3: Send any 3D visualizations (if available).\nWhen done, type /done to finish.")
    return MEDIA_VISUAL

async def finish_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 All project info and media have been saved. Thank you!")
    logger.info(f"Final project data: {context.user_data}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Project entry canceled.")
    return ConversationHandler.END

# === Debug Command ===
async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    launch_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    env = os.getenv("ENV", "not set")
    token = os.getenv("BOT_TOKEN", "none")[:10] + "..."

    debug_info = (
        f"🤖 *Bot Debug Info*\n\n"
        f"📅 Launch Time: `{launch_time}`\n"
        f"🖥 Platform: `{platform.system()} {platform.release()}`\n"
        f"🌐 ENV: `{env}`\n"
        f"🔐 BOT_TOKEN: `{token}`\n"
        f"📁 Current dir: `{os.getcwd()}`"
    )

    await update.message.reply_text(debug_info, parse_mode="Markdown")

# === Main ===
async def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ROOM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_type)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            CLIENT_ISSUES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issues)],
            CLIENT_GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goals)],
            WHAT_DONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_done)],
            SPECIAL_FEATURES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_special)],
            MEDIA_BEFORE: [
                MessageHandler(filters.PHOTO | filters.VIDEO, get_media_before),
                CommandHandler("next", next_to_after)
            ],
            MEDIA_AFTER: [
                MessageHandler(filters.PHOTO | filters.VIDEO, get_media_after),
                CommandHandler("next", next_to_visual)
            ],
            MEDIA_VISUAL: [
                MessageHandler(filters.PHOTO | filters.VIDEO, get_media_visual),
                CommandHandler("done", finish_media)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("debug", debug))

    await app.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
