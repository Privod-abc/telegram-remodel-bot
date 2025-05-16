import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# Flask App
app = Flask(__name__)

# Telegram Token
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

# States
CLIENT_NAME, ROOM_TYPE, LOCATION, CLIENT_GOAL, WHAT_DONE, MATERIALS, FEATURES, GDRIVE = range(8)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram App
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# Admin notification
async def notify_admin(data: dict):
    text = (
        f"📢 *New Project Submitted!*\n\n"
        f"👤 Client: {data.get('client_name') or '—'}\n"
        f"🏗️ Room: {data.get('room_type') or '—'}\n"
        f"📍 Location: {data.get('location') or '—'}\n"
        f"🌟 Goal: {data.get('goal') or '—'}\n"
        f"💪 Work done: {data.get('what_done') or '—'}\n"
        f"🧱 Materials: {data.get('materials') or '—'}\n"
        f"✨ Features: {data.get('features') or '—'}\n"
        f"📂 Google Drive: {data.get('drive_link') or '—'}"
    )
    await bot.send_message(chat_id=130060469, text=text, parse_mode="Markdown")

# Unified handler
async def get_or_skip(update, context, key, next_state, prompt):
    value = update.message.text.strip()
    context.user_data[key] = None if value.lower() == "/skip" else value
    await update.message.reply_text(prompt)
    return next_state

# Step functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🙋‍♂️ What is the client’s name?")
    return CLIENT_NAME

async def get_client_name(update, context): return await get_or_skip(update, context, "client_name", ROOM_TYPE, "🏗️ What room did you work on?")
async def get_room_type(update, context): return await get_or_skip(update, context, "room_type", LOCATION, "📍 In which city and state was this project completed?")
async def get_location(update, context): return await get_or_skip(update, context, "location", CLIENT_GOAL, "🌟 What was the client’s goal for this space?\n(e.g. fix layout, expand storage, modernize style, etc.)")
async def get_goal(update, context): return await get_or_skip(update, context, "goal", WHAT_DONE, "💪 What did your team do in this project?")
async def get_done(update, context): return await get_or_skip(update, context, "what_done", MATERIALS, "🧱 What materials were used? (names, colors)")
async def get_materials(update, context): return await get_or_skip(update, context, "materials", FEATURES, "✨ Unique features or clever solutions?")
async def get_features(update, context): return await get_or_skip(update, context, "features", GDRIVE, "📂 Paste the Google Drive folder link (with folders: before / after / 3D / drawings)")
async def get_drive_link(update, context):
    context.user_data["drive_link"] = update.message.text.strip()
    await update.message.reply_text("🎉 Project saved. Thank you!")
    await notify_admin(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Project canceled.")
    return ConversationHandler.END

# Conversation logic
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)],
        ROOM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_type)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
        CLIENT_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
        WHAT_DONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_done)],
        MATERIALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_materials)],
        FEATURES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_features)],
        GDRIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_drive_link)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True
)

telegram_app.add_handler(conv_handler)

# ✅ Webhook endpoint
@app.route("/", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.process_update(update))

        return "ok", 200
    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return "error", 500
