import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# Flask app
app = Flask(__name__)

# Telegram Bot config
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.index")

# States
CLIENT_NAME, ROOM_TYPE, LOCATION, CLIENT_GOAL, WHAT_DONE, MATERIALS, FEATURES, GDRIVE = range(8)

# Telegram Application
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# Handler functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🙋‍♂️ What is the client’s name?")
    return CLIENT_NAME

async def get_or_skip(update, context, key, next_state, prompt):
    context.user_data[key] = None if update.message.text.lower() == "/skip" else update.message.text
    await update.message.reply_text(prompt)
    return next_state

async def get_client_name(update, context): return await get_or_skip(update, context, "client_name", ROOM_TYPE, "🏗️ What room did you work on?")
async def get_room_type(update, context): return await get_or_skip(update, context, "room_type", LOCATION, "📍 In which city and state was this project completed?")
async def get_location(update, context): return await get_or_skip(update, context, "location", CLIENT_GOAL, "🌟 What was the client’s goal for this space?")
async def get_goal(update, context): return await get_or_skip(update, context, "goal", WHAT_DONE, "💪 What did your team do in this project?")
async def get_done(update, context): return await get_or_skip(update, context, "what_done", MATERIALS, "🧱 What materials were used? (names, colors)")
async def get_materials(update, context): return await get_or_skip(update, context, "materials", FEATURES, "✨ Unique features or smart solutions?")
async def get_features(update, context): return await get_or_skip(update, context, "features", GDRIVE, "📂 Paste the Google Drive folder link")

async def get_drive(update, context):
    context.user_data["drive_link"] = update.message.text
    await update.message.reply_text("🎉 Project saved. Thank you!")
    await bot.send_message(
        chat_id=130060469,
        text=(
            f"📢 *New Project Submitted!*\n\n"
            f"👤 Client: {context.user_data.get('client_name') or '—'}\n"
            f"🏗️ Room: {context.user_data.get('room_type') or '—'}\n"
            f"📍 Location: {context.user_data.get('location') or '—'}\n"
            f"🌟 Goal: {context.user_data.get('goal') or '—'}\n"
            f"💪 Work done: {context.user_data.get('what_done') or '—'}\n"
            f"🧱 Materials: {context.user_data.get('materials') or '—'}\n"
            f"✨ Features: {context.user_data.get('features') or '—'}\n"
            f"📂 Drive: {context.user_data.get('drive_link') or '—'}"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Project canceled.")
    return ConversationHandler.END

# Conversation handler
telegram_app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)],
        ROOM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_type)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
        CLIENT_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
        WHAT_DONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_done)],
        MATERIALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_materials)],
        FEATURES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_features)],
        GDRIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_drive)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True
))

# Webhook endpoint
@app.route("/", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)

        # Обрабатываем update без остановки приложения
        asyncio.get_event_loop().create_task(telegram_app.process_update(update))
        return "ok", 200

    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return "error", 500
