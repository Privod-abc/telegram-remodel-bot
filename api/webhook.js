import 'dotenv/config';
import { createBot } from '../lib/bot.js';

// Создаем экземпляр бота
const bot = createBot();

// Функция для настройки webhook
async function setupWebhook() {
  try {
    const webhookUrl = process.env.WEBHOOK_URL;
    if (!webhookUrl) {
      console.error('WEBHOOK_URL not set in environment variables');
      return;
    }

    // Устанавливаем webhook для бота
    await bot.telegram.setWebhook(webhookUrl);
    console.log(`Webhook set to ${webhookUrl}`);
  } catch (error) {
    console.error('Error setting webhook:', error);
  }
}

// В режиме разработки, запускаем бота в режиме long polling
if (process.env.NODE_ENV === 'development') {
  bot.launch();
  console.log('Bot is running in development mode (long polling)');
  
  // Включаем graceful stop
  process.once('SIGINT', () => bot.stop('SIGINT'));
  process.once('SIGTERM', () => bot.stop('SIGTERM'));
} else {
  // В режиме production, настраиваем webhook
  setupWebhook().catch(console.error);
}

// Обработчик для serverless функции Vercel
export default async function handler(req, res) {
  try {
    // Проверяем, что запрос - это POST
    if (req.method !== 'POST') {
      res.status(200).json({ message: 'This endpoint handles Telegram webhook events' });
      return;
    }
    
    // Обрабатываем webhook обновление
    await bot.handleUpdate(req.body);
    res.status(200).json({ ok: true });
  } catch (error) {
    console.error('Error handling webhook:', error);
    res.status(500).json({ error: 'Failed to process webhook' });
  }
}
