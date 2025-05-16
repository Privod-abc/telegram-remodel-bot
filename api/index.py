import os
import logging
import nest_asyncio
from flask import Flask, request
from telegram import Update, Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

nest_asyncio.apply()
app = Flask(__name__)

# Telegram config
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

# States
CLIENT_NAME, ROOM_TYPE, LOCATION, CLIENT_GOAL, WHAT_DONE, MATERIALS, FEATURES, GDRIVE = range(8)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot app
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# Admin ID
ADMIN_CHAT_ID = 130060469  # Replace if needed

# Keyboard
def get_main_keyboard():
    return ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)

# Notify admin
async def notify_admin(data: dict):
    summary = (
        f"📢 *Новый проект!*\n\n"
        f"👤 Клиент: {data.get('client_name') or '—'}\n"
        f"🏗️ Комната: {data.get('room_type') or '—'}\n"
        f"📍 Локация: {data.get('location') or '—'}\n"
        f"🌟 Цель: {data.get('goal') or '—'}\n"
        f"💪 Выполнено: {data.get('what_done') or '—'}\n"
        f"🧱 Материалы: {data.get('materials') or '—'}\n"
        f"✨ Особенности: {data.get('features') or '—'}\n"
        f"📂 Google Drive: {data.get('drive_link') or '—'}"
    )
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary, parse_mode="Markdown")

# Helpers
async def get_or_skip(update, context, key, next_state, prompt):
    text = update.message.text
    context.user_data[key] = None if text.lower().strip() == "/skip" else text.strip()
    await update.message.reply_text(prompt)
    return next_state

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🙋‍♂️ Как зовут клиента?",
        reply_markup=ReplyKeyboardRemove()
    )
    return CLIENT_NAME

async def get_client_name(update, context): return await get_or_skip(update, context, "client_name", ROOM_TYPE, "🏗️ Какое помещение было отремонтировано?")
async def get_room_type(update, context): return await get_or_skip(update, context, "room_type", LOCATION, "📍 В каком городе и штате был сделан проект?")
async def get_location(update, context): return await get_or_skip(update, context, "location", CLIENT_GOAL, "🌟 Что хотел изменить/достичь клиент? (например: устаревший ремонт, нерациональное пространство)")
async def get_goal(update, context): return await get_or_skip(update, context, "goal", WHAT_DONE, "💪 Что было сделано вашей командой?")
async def get_done(update, context): return await get_or_skip(update, context, "what_done", MATERIALS, "🧱 Какие материалы использовались? (названия, цвета)")
async def get_materials(update, context): return await get_or_skip(update, context, "materials", FEATURES, "✨ Были ли реализованы интересные идеи или нестандартные решения?")
async def get_features(update, context): return await get_or_skip(update, context, "features", GDRIVE, "📂 Вставьте ссылку на папку Google Drive.\nВнутри неё должны быть папки: before, after, 3D, drawings.")

async def get_drive_link(update, context):
    context.user_data["drive_link"] = update.message.text.strip()
    await update.message.reply_text("🎉 Спасибо! Проект сохранён.", reply_markup=get_main_keyboard())
    await notify_admin(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ввод проекта отменён.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

# Setup conversation
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

# Webhook handler
@app.route("/", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await telegram_app.process_update(update)
    return "ok"
