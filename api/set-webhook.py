import os
import json
from http.server import BaseHTTPRequestHandler
import httpx
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        async def set_webhook():
            webhook_url = "https://telegram-remodel-bot.vercel.app/api"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data={"url": webhook_url})
                return response.json()
                
        result = asyncio.run(set_webhook())
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode('utf-8'))

def handler(request, response):
    return Handler().do_GET()
