import os
import logging
import nest_asyncio
from flask import Flask, request, Response
from telegram import Update, Bot
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import httpx
from threading import Thread

# === Базовая настройка ===
nest_asyncio.apply()
app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("BOT_TOKEN не установлен в переменных окружения!")
else:
    logging.info(f"BOT_TOKEN установлен: {BOT_TOKEN[:5]}...")

bot = Bot(BOT_TOKEN)

# === Состояния диалога ===
CLIENT_NAME, ROOM_TYPE, LOCATION, CLIENT_GOAL, WHAT_DONE, MATERIALS, FEATURES, GDRIVE = range(8)

# === Логирование ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Telegram-приложение ===
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Уведомление админу ===
async def notify_admin(data: dict):
    admin_id = 130060469  # ID администратора
    try:
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
        await bot.send_message(chat_id=admin_id, text=summary, parse_mode="Markdown")
        logger.info(f"Уведомление отправлено админу {admin_id}")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")

# === Хэндлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    context.user_data.clear()
    await update.message.reply_text("🙋‍♂️ What is the client's name?")
    return CLIENT_NAME

async def get_or_skip(update, context, key, next_state, prompt):
    text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Получен ответ от пользователя {user_id} для {key}: {text}")
    
    context.user_data[key] = None if text.strip().lower() == "/skip" else text.strip()
    await update.message.reply_text(prompt)
    return next_state

async def get_client_name(update, context): return await get_or_skip(update, context, "client_name", ROOM_TYPE, "🏗️ What room did you work on?")
async def get_room_type(update, context): return await get_or_skip(update, context, "room_type", LOCATION, "📍 In which city and state was this project completed?")
async def get_location(update, context): return await get_or_skip(update, context, "location", CLIENT_GOAL, "🌟 What was the client's goal for this space? (e.g. more space, modern look, old layout, etc.)")
async def get_goal(update, context): return await get_or_skip(update, context, "goal", WHAT_DONE, "💪 What did your team do in this project?")
async def get_done(update, context): return await get_or_skip(update, context, "what_done", MATERIALS, "🧱 What materials were used? (names, colors)")
async def get_materials(update, context): return await get_or_skip(update, context, "materials", FEATURES, "✨ Any unique features, smart ideas or details to highlight?")
async def get_features(update, context): return await get_or_skip(update, context, "features", GDRIVE, "📂 Paste the Google Drive folder link (with folders: before, after, 3D, drawings)")

async def get_drive_link(update, context):
    text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Получен последний ответ от пользователя {user_id} для drive_link: {text}")
    
    context.user_data["drive_link"] = None if text.strip().lower() == "/skip" else text.strip()
    await update.message.reply_text("🎉 Project saved. Thank you!")
    
    # Логируем полные данные перед отправкой уведомления
    logger.info(f"Сохранены данные проекта: {context.user_data}")
    
    await notify_admin(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} отменил операцию")
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

# === Обработчик для логирования необработанных обновлений ===
async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Необработанное обновление: {update}")

telegram_app.add_handler(MessageHandler(filters.ALL, log_update), group=-1)

# === Webhook для Telegram (Flask) ===
@app.route("/", methods=["POST"])
def webhook():
    logger.info("Получен запрос на webhook")
    try:
        # Логируем полученные данные для отладки
        data = request.get_json(force=True)
        logger.info(f"Получены данные: {data}")
        
        # Создаем объект Update и обрабатываем его асинхронно
        update = Update.de_json(data, bot)
        
        # Запускаем обработку обновления в отдельном потоке
        def process_update():
            import asyncio
            asyncio.run(telegram_app.process_update(update))
        
        Thread(target=process_update).start()
        
        return Response("ok", status=200)
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return Response(f"error: {str(e)}", status=500)

# === Простой маршрут для проверки работоспособности ===
@app.route("/", methods=["GET"])
def health_check():
    logger.info("Проверка работоспособности")
    return "Telegram bot is running!"

# === Установка webhook при запуске ===
async def set_webhook():
    webhook_url = "https://telegram-remodel-bot.vercel.app/api"
    logger.info(f"Устанавливаем webhook на {webhook_url}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data={"url": webhook_url})
            logger.info(f"Ответ от Telegram API: {response.text}")
            return response.json()
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return {"error": str(e)}

# === Ручная установка webhook ===
@app.route("/set-webhook", methods=["GET"])
def set_webhook_route():
    import asyncio
    result = asyncio.run(set_webhook())
    return result

# === Инициализация при запуске ===
# Для serverless окружения Vercel это не будет выполняться при каждом HTTP-запросе
try:
    import asyncio
    asyncio.run(set_webhook())
    logger.info("Webhook установлен при инициализации")
except Exception as e:
    logger.error(f"Не удалось установить webhook при инициализации: {e}")
