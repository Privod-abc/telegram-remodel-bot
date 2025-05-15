import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# Настройки логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# Хэндлер команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь описание проекта, а затем фото или видео. Я сохраню их в облаке.")

# =========================
# Хэндлер текста (описание проекта)
project_descriptions = {}

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    project_descriptions[user_id] = text
    await update.message.reply_text("✅ Описание сохранено. Теперь отправь фото или видео этого проекта.")

# =========================
# Хэндлер медиафайлов (фото и видео)
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = update.message.photo[-1] if update.message.photo else update.message.video
    file_id = file.file_id
    file_obj = await context.bot.get_file(file_id)
    
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{file_id}.jpg" if update.message.photo else f"downloads/{file_id}.mp4"
    await file_obj.download_to_drive(file_path)
    
    # Здесь будет подключение к Google Drive (позже)
    logger.info(f"Файл сохранён локально: {file_path}")
    
    await update.message.reply_text("📁 Файл получен. В следующем шаге подключим сохранение на Google Диск.")

# =========================
# Запуск бота
if __name__ == '__main__':
    import asyncio

    async def main():
        app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

        await app.run_polling()

    asyncio.run(main())
