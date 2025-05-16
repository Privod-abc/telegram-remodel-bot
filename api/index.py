import os
import logging
import asyncio
import nest_asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

nest_asyncio.apply()
app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

CLIENT_NAME, ROOM_TYPE, LOCATION, CLIENT_GOAL, WHAT_DONE, MATERIALS, FEATURES, GDRIVE = range(8)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.index")

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# Notify admin
async def notify_admin(data: dict):
    text = (
        f"📢 *New Project Submitted!*\n\n"
        f"👤 Client: {data.get('client_name')}\n"
        f"🏗️ Room: {data.get('room_type')}\n"
        f"📍 Location: {data.get('location')}\n"
        f"🌟 Goal: {data.get('goal')}\n"
        f"💪 Work done: {data.get('what_done')}\n"
        f"🧱 Materials: {data.get('materials')}\n"
        f"✨ Features: {data.get('features')}\n"
        f"📂 Drive: {data.get('drive_link')}"
    )
    await bot.send_message(chat_id=130060469, text=text, parse_mode="Markdown")

# Steps
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
    await notify_admin(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Project canceled.")
    return ConversationHandler.END

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

@app.route("/", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)

        async def process():
            await telegram_app.initialize()
            await telegram_app.process_update(update)
            await telegram_app.shutdown()

        asyncio.run(process())
        return "ok", 200

    except Exception as e:
        logger.exception(f"Exception on / [POST]: {e}")
        return "error", 500
