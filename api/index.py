import os
import logging
from flask import Flask, request, Response, jsonify
import httpx
import asyncio

# Создание Flask приложения
app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен в переменных окружения!")

# Корневой маршрут для проверки работоспособности
@app.route('/', methods=['GET'])
def home():
    return "Telegram Bot is running!"

# Маршрут для webhook
@app.route('/api', methods=['POST'])
def webhook():
    logger.info("Получен POST запрос на /api")
    try:
        # Логируем полученные данные
        data = request.get_json(force=True) if request.is_json else request.data
        logger.info(f"Получены данные: {data}")
        
        # Просто возвращаем OK, чтобы Telegram знал, что запрос успешно получен
        return Response("ok", status=200)
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return Response(f"Error: {str(e)}", status=500)

# Маршрут для установки webhook
@app.route('/set-webhook', methods=['GET'])
def set_webhook():
    webhook_url = "https://telegram-remodel-bot.vercel.app/api"
    
    try:
        # Делаем синхронный запрос для простоты
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
        response = httpx.get(url)
        result = response.json()
        logger.info(f"Результат установки webhook: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return jsonify({"error": str(e)})

# Маршрут для получения информации о webhook
@app.route('/webhook-info', methods=['GET'])
def webhook_info():
    try:
        # Делаем синхронный запрос для простоты
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = httpx.get(url)
        result = response.json()
        logger.info(f"Информация о webhook: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при получении информации о webhook: {e}")
        return jsonify({"error": str(e)})
