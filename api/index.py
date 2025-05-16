import os
import logging
from flask import Flask, request, Response, jsonify
import httpx
from threading import Thread
import nest_asyncio
import asyncio

# === Инициализация Flask и базовых компонентов ===
nest_asyncio.apply()
app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === Настройка логирования ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Проверка токена ===
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен в переменных окружения!")
else:
    logger.info(f"BOT_TOKEN установлен: {BOT_TOKEN[:5]}...")

# === Основной обработчик webhook ===
@app.route("/api", methods=["POST"])
def api_webhook():
    """Основной обработчик для webhook Telegram.
    Этот маршрут должен соответствовать URL, настроенному в Telegram."""
    
    logger.info("=== Получен запрос на /api webhook ===")
    
    try:
        # Получаем и логируем данные запроса
        json_data = request.get_json(force=True)
        logger.info(f"Получены данные: {json_data}")
        
        # Отправляем данные в Telegram API для обработки в отдельном потоке
        def process_update():
            try:
                # Инициализируем библиотеку python-telegram-bot и обрабатываем сообщение
                from telegram import Update, Bot
                from telegram.ext import Application, ApplicationBuilder
                
                # Создаем объекты бота и приложения только для обработки текущего обновления
                bot = Bot(BOT_TOKEN)
                app_builder = ApplicationBuilder().token(BOT_TOKEN)
                tg_app = app_builder.build()
                
                # Создаем объект Update из полученных данных
                update = Update.de_json(json_data, bot)
                
                # Логируем информацию о сообщении
                if update.message:
                    logger.info(f"Получено сообщение от {update.message.from_user.id}: {update.message.text}")
                
                # Обрабатываем обновление
                asyncio.run(tg_app.process_update(update))
                logger.info("Обновление успешно обработано")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке обновления в потоке: {e}")
        
        # Запускаем обработку в отдельном потоке
        Thread(target=process_update).start()
        
        # Немедленно возвращаем ответ Telegram, не дожидаясь завершения обработки
        return Response("ok", status=200)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке webhook: {e}")
        return Response(f"Ошибка: {str(e)}", status=500)

# === Проверка работоспособности ===
@app.route("/", methods=["GET"])
def health_check():
    """Простой маршрут для проверки, что сервер работает."""
    logger.info("Получен запрос на проверку работоспособности")
    return "Telegram bot is running! Webhook is configured."

# === Установка webhook ===
@app.route("/set-webhook", methods=["GET"])
def set_webhook_route():
    """Маршрут для установки webhook URL в Telegram API."""
    logger.info("Получен запрос на установку webhook")
    
    async def set_webhook():
        """Асинхронная функция для установки webhook."""
        webhook_url = "https://telegram-remodel-bot.vercel.app/api"
        logger.info(f"Устанавливаем webhook на {webhook_url}")
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data={"url": webhook_url})
            result = response.json()
            logger.info(f"Ответ от Telegram API: {result}")
            return result
    
    try:
        result = asyncio.run(set_webhook())
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return jsonify({"error": str(e), "success": False})

# === Получение информации о webhook ===
@app.route("/webhook-info", methods=["GET"])
def webhook_info():
    """Маршрут для получения информации о текущих настройках webhook."""
    logger.info("Получен запрос на получение информации о webhook")
    
    async def get_webhook_info():
        """Асинхронная функция для получения информации о webhook."""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            result = response.json()
            logger.info(f"Информация о webhook: {result}")
            return result
    
    try:
        result = asyncio.run(get_webhook_info())
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при получении информации о webhook: {e}")
        return jsonify({"error": str(e), "success": False})

# === Обработка специфичных команд ===
@app.route("/demo-message", methods=["GET"])
def send_demo_message():
    """Дополнительный маршрут для тестирования отправки сообщений."""
    
    async def send_message():
        """Асинхронная функция для отправки тестового сообщения."""
        from telegram import Bot
        bot = Bot(BOT_TOKEN)
        await bot.send_message(chat_id=130060469, text="✅ Бот активен и работает!")
        return {"success": True, "message": "Тестовое сообщение отправлено"}
    
    try:
        result = asyncio.run(send_message())
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при отправке тестового сообщения: {e}")
        return jsonify({"error": str(e), "success": False})

# === Установка webhook при запуске ===
# Не используем этот код для serverless функций, так как он может вызвать проблемы
# Вместо этого, нужно явно вызвать /set-webhook после деплоя
