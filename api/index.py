import os
import json
from http.server import BaseHTTPRequestHandler
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN")

def process_telegram_update(json_data):
    # Здесь можно добавить логику для обработки обновлений
    # Для начала просто возвращаем успех
    return True

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("Telegram bot is running!".encode())
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            json_data = json.loads(post_data.decode('utf-8'))
            success = process_telegram_update(json_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"ok")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())

def handler(request, response):
    if request['method'] == 'POST':
        return Handler().do_POST()
    return Handler().do_GET()
