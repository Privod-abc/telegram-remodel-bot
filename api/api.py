import os
import logging
from http.server import BaseHTTPRequestHandler
import json
import httpx
from threading import Thread
import asyncio

# Установка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена
BOT_TOKEN = os.getenv("BOT_TOKEN")

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        logger.info("Получен POST запрос на /api")
        
        # Получение данных запроса
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Парсинг JSON
            json_data = json.loads(post_data.decode('utf-8'))
            logger.info(f"Получены данные: {json_data}")
            
            # Обработка в отдельном потоке
            def process_update():
                try:
                    logger.info("Начинаем обработку обновления")
                    # Мы просто логируем обновление
                    # Для полной обработки можно добавить код взаимодействия с Telegram API
                    logger.info("Обновление успешно обработано")
                except Exception as e:
                    logger.error(f"Ошибка в процессе обработки: {e}")
            
            # Запускаем обработку асинхронно
            Thread(target=process_update).start()
            
            # Возвращаем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"ok")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке webhook: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Ошибка: {str(e)}".encode('utf-8'))

# Обработчик функции для Vercel serverless
def handler(request, response):
    return Handler().do_POST()
