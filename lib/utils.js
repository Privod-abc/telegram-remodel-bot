// Функция для проверки формата ссылки на Google Drive
export function validateDriveLink(link) {
  return link.includes('drive.google.com');
}

// Функция для создания текста уведомления администратору
export function createAdminNotification(data) {
  return `
📢 New Project Submitted!
👤 Client: ${data.client_name}
🏗️ Room: ${data.room_type}
📍 Location: ${data.location}
🌟 Goal: ${data.goal}
💪 Work done: ${data.what_done}
🧱 Materials: ${data.materials}
✨ Features: ${data.features}
📂 Drive: ${data.drive_link}
  `.trim();
}

// Функция для проверки структуры папки в Google Drive
export function checkDriveFolderStructure(driveLink) {
  // В реальном приложении здесь можно реализовать проверку через Google Drive API
  return true;
}
