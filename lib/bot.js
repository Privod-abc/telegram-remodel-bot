import { Telegraf, Scenes, session } from 'telegraf';
import { addRowToSheet } from './googleSheets.js';
import { validateDriveLink, createAdminNotification } from './utils.js';

// Создаем экземпляр бота
export function createBot() {
  const bot = new Telegraf(process.env.BOT_TOKEN);
  
  // Добавляем middleware для обработки сессий
  bot.use(session());
  
  // Создаем сцену для опроса
  const surveyScene = new Scenes.WizardScene(
    'SURVEY_SCENE',
    // Шаг 1: Имя клиента
    (ctx) => {
      ctx.wizard.state.data = {}; // Инициализируем объект для хранения данных
      ctx.reply('🙋‍♂️ What is the *client\'s name*? (Как зовут клиента?)', {
        parse_mode: 'Markdown',
        reply_markup: {
          keyboard: [
            [{ text: 'Skip this question ⏭️' }]
          ],
          resize_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Шаг 2: Тип комнаты
    (ctx) => {
      if (ctx.message.text !== 'Skip this question ⏭️') {
        ctx.wizard.state.data.client_name = ctx.message.text;
      } else {
        ctx.wizard.state.data.client_name = "Not specified";
      }
      
      ctx.reply('🏗️ What *room* did you work on? (e.g. kitchen, bathroom, laundry room) (Какую комнату ремонтировали?)', {
        parse_mode: 'Markdown',
        reply_markup: {
          keyboard: [
            [{ text: 'Skip this question ⏭️' }]
          ],
          resize_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Шаг 3: Локация (город, штат)
    (ctx) => {
      if (ctx.message.text !== 'Skip this question ⏭️') {
        ctx.wizard.state.data.room_type = ctx.message.text;
      } else {
        ctx.wizard.state.data.room_type = "Not specified";
      }
      
      ctx.reply('📍 In which *city and state* was this project completed? (В каком городе и штате выполнен проект?)', {
        parse_mode: 'Markdown',
        reply_markup: {
          keyboard: [
            [{ text: 'Skip this question ⏭️' }]
          ],
          resize_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Шаг 4: Цель клиента
    (ctx) => {
      if (ctx.message.text !== 'Skip this question ⏭️') {
        ctx.wizard.state.data.location = ctx.message.text;
      } else {
        ctx.wizard.state.data.location = "Not specified";
      }
      
      ctx.reply('🌟 What was the *client\'s goal* for this space? (e.g. modernize layout, fix poor lighting, update style, old renovation, etc.) (Чего хотел добиться клиент в этом помещении?)', {
        parse_mode: 'Markdown',
        reply_markup: {
          keyboard: [
            [{ text: 'Skip this question ⏭️' }]
          ],
          resize_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Шаг 5: Выполненная работа
    (ctx) => {
      if (ctx.message.text !== 'Skip this question ⏭️') {
        ctx.wizard.state.data.goal = ctx.message.text;
      } else {
        ctx.wizard.state.data.goal = "Not specified";
      }
      
      ctx.reply('💪 What *work was done* during the remodel? (Что было сделано в проекте?)', {
        parse_mode: 'Markdown',
        reply_markup: {
          keyboard: [
            [{ text: 'Skip this question ⏭️' }]
          ],
          resize_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Шаг 6: Использованные материалы
    (ctx) => {
      if (ctx.message.text !== 'Skip this question ⏭️') {
        ctx.wizard.state.data.what_done = ctx.message.text;
      } else {
        ctx.wizard.state.data.what_done = "Not specified";
      }
      
      ctx.reply('🧱 What *materials* were used? (Include names, colors, manufacturers if possible) (Какие материалы использовались? Название, цвет, производитель)', {
        parse_mode: 'Markdown',
        reply_markup: {
          keyboard: [
            [{ text: 'Skip this question ⏭️' }]
          ],
          resize_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Шаг 7: Интересные особенности
    (ctx) => {
      if (ctx.message.text !== 'Skip this question ⏭️') {
        ctx.wizard.state.data.materials = ctx.message.text;
      } else {
        ctx.wizard.state.data.materials = "Not specified";
      }
      
      ctx.reply('✨ Were there any *interesting features* or smart solutions implemented? (e.g. round lighting, hidden drawers, custom panels) (Были ли интересные решения или особенности в проекте?)', {
        parse_mode: 'Markdown',
        reply_markup: {
          keyboard: [
            [{ text: 'Skip this question ⏭️' }]
          ],
          resize_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Шаг 8: Ссылка на Google Drive
    (ctx) => {
      if (ctx.message.text !== 'Skip this question ⏭️') {
        ctx.wizard.state.data.features = ctx.message.text;
      } else {
        ctx.wizard.state.data.features = "Not specified";
      }
      
      ctx.reply('📂 Please *paste the Google Drive folder link* (with subfolders: before / after / 3D / drawings) (Вставьте ссылку на папку Google Drive с подпапками: до / после / 3D / чертёж)', {
        parse_mode: 'Markdown',
        reply_markup: {
          remove_keyboard: true
        }
      });
      return ctx.wizard.next();
    },
    // Завершающий шаг: обработка данных
    async (ctx) => {
      if (!ctx.message || !ctx.message.text) {
        ctx.reply('Please provide a valid Google Drive link.');
        return;
