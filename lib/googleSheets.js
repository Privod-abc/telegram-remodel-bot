import { GoogleSpreadsheet } from 'google-spreadsheet';
import { JWT } from 'google-auth-library';

// Колонки таблицы, соответствующие данным, собранным ботом
const COLUMN_HEADERS = [
  'Date',
  'Client Name',
  'Room Type',
  'Location',
  'Goal',
  'Work Done',
  'Materials',
  'Features',
  'Drive Link'
];

export async function initializeGoogleSheets() {
  try {
    // Парсим учетные данные сервисного аккаунта из переменных окружения
    const serviceAccountKey = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_KEY);
    
    // Создаем JWT клиент для аутентификации
    const serviceAccountAuth = new JWT({
      email: serviceAccountKey.client_email,
      key: serviceAccountKey.private_key,
      scopes: [
        'https://www.googleapis.com/auth/spreadsheets',
      ],
    });

    // Инициализируем документ
    const doc = new GoogleSpreadsheet(process.env.GOOGLE_SHEET_ID, serviceAccountAuth);
    await doc.loadInfo();
    
    // Получаем первый лист или создаем новый, если его нет
    let sheet = doc.sheetsByIndex[0];
    if (!sheet) {
      sheet = await doc.addSheet({ title: 'Renovation Projects' });
    }
    
    // Проверяем, установлены ли заголовки колонок
    const rows = await sheet.getRows();
    if (rows.length === 0) {
      // Если таблица пуста, добавляем заголовки
      await sheet.setHeaderRow(COLUMN_HEADERS);
    }
    
    return sheet;
  } catch (error) {
    console.error('Error initializing Google Sheets:', error);
    throw error;
  }
}

export async function addRowToSheet(projectData) {
  try {
    const sheet = await initializeGoogleSheets();
    
    // Создаем новую строку с сегодняшней датой и данными проекта
    const newRow = {
      'Date': new Date().toLocaleDateString(),
      'Client Name': projectData.client_name,
      'Room Type': projectData.room_type,
      'Location': projectData.location,
      'Goal': projectData.goal,
      'Work Done': projectData.what_done,
      'Materials': projectData.materials,
      'Features': projectData.features,
      'Drive Link': projectData.drive_link
    };
    
    // Добавляем строку в таблицу
    await sheet.addRow(newRow);
    
    return true;
  } catch (error) {
    console.error('Error adding row to sheet:', error);
    throw error;
  }
}
