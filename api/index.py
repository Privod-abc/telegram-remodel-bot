import os
import logging
import nest_asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import httpx

# === Базовая настройка ===
nest_asyncio.apply()
app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

# === Состояния диалога ===
CLIENT_NAME, ROOM_TYPE, LOCATION, CLIENT_GOAL, WHAT_DONE, MATERIALS, FEATURES, GDRIVE = range(8)

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Telegram-приложение ===
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# === Уведомление админу ===
async def notify_admin(data: dict):
    summary = (
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
    await bot.send_message(chat_id=130060469, text=summary, parse_mode="Markdown")

# === Хэндлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🙋‍♂️ What is the client’s name?")
    return CLIENT_NAME

async def get_or_skip(update, context, key, next_state, prompt):
    text = update.message.text
    context.user_data[key] = None if text.strip().lower() == "/skip" else text.strip()
    await update.message.reply_text(prompt)
    return next_state

async def get_client_name(update, context): return await get_or_skip(update, context, "client_name", ROOM_TYPE, "🏗️ What room did you work on?")
async def get_room_type(update, context): return await get_or_skip(update, context, "room_type", LOCATION, "📍 In which city and state was this project completed?")
async def get_location(update, context): return await get_or_skip(update, context, "location", CLIENT_GOAL, "🌟 What was the client’s goal for this space? (e.g. more space, modern look, old layout, etc.)")
async def get_goal(update, context): return await get_or_skip(update, context, "goal", WHAT_DONE, "💪 What did your team do in this project?")
async def get_done(update, context): return await get_or_skip(update, context, "what_done", MATERIALS, "🧱 What materials were used? (names, colors)")
async def get_materials(update, context): return await get_or_skip(update, context, "materials", FEATURES, "✨ Any unique features, smart ideas or details to highlight?")
async def get_features(update, context): return await get_or_skip(update, context, "features", GDRIVE, "📂 Paste the Google Drive folder link (with folders: before, after, 3D, drawings)")
async def get_drive_link(update, context):
    text = update.message.text
    context.user_data["drive_link"] = None if text.strip().lower() == "/skip" else text.strip()
    await update.message.reply_text("🎉 Project saved. Thank you!")
    await notify_admin(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Project canceled.")
    return ConversationHandler.END

# === Обработка диалога ===
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
    allow_reentry=True,
)

telegram_app.add_handler(conv_handler)

# === Webhook для Telegram (Flask) ===
@app.route("/", methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        await telegram_app.process_update(update)
        return "ok"
    return "ping"

# === Автоустановка Webhook при запуске ===
async def set_webhook():
    webhook_url = "https://telegram-remodel-bot.vercel.app/"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    async with httpx.AsyncClient() as client:
        await client.post(url, data={"url": webhook_url})

telegram_app.post_init = set_webhook
