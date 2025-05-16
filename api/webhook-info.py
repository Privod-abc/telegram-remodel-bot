import os
import json
from http.server import BaseHTTPRequestHandler
import httpx
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        async def get_webhook_info():
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.json()
                
        result = asyncio.run(get_webhook_info())
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode('utf-8'))

def handler(request, response):
    return Handler().do_GET()
