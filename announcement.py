import logging
import sqlite3
from telegram import Update, InputFile
from telegram.ext import ContextTypes
import os
from datetime import datetime


class AnnouncementManager:
    def __init__(self, db_name='math_bot.db'):
        self.db_name = db_name
        self.init_announcements_table()
    
    def init_announcements_table(self):
        """Создает таблицу для отслеживания отправленных объявлений"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                announcement_id TEXT UNIQUE,
                user_id INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Таблица объявлений инициализирована")
    
    def get_all_users(self):
        """Получает список всех пользователей бота"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return users
    
    def mark_announcement_sent(self, user_id, announcement_id):
        """Отмечает, что объявление отправлено пользователю"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO announcements (announcement_id, user_id)
                VALUES (?, ?)
            ''', (announcement_id, user_id))
            
            conn.commit()
        except Exception as e:
            logging.error(f"Ошибка при отметке объявления: {e}")
        finally:
            conn.close()
    
    def is_announcement_sent(self, user_id, announcement_id):
        """Проверяет, было ли объявление уже отправлено пользователю"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 1 FROM announcements 
            WHERE user_id = ? AND announcement_id = ?
        ''', (user_id, announcement_id))
        
        result = cursor.fetchone() is not None
        conn.close()
        return result

async def send_global_announcement(context: ContextTypes.DEFAULT_TYPE, 
                                 message_text: str, 
                                 photo_path: str = None,
                                 announcement_id: str = None):
    """
    Отправляет глобальное объявление всем пользователям бота
    
    Args:
        context: Контекст бота
        message_text: Текст объявления
        photo_path: Путь к картинке (опционально)
        announcement_id: Уникальный ID объявления (для избежания дублирования)
    """
    
    announcement_manager = AnnouncementManager()
    all_users = announcement_manager.get_all_users()
    
    if not all_users:
        logging.info("Нет пользователей для отправки объявления")
        return
    
    successful_sends = 0
    failed_sends = 0
    
    # Создаем уникальный ID объявления если не предоставлен
    if announcement_id is None:
        announcement_id = f"announce_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logging.info(f"Начинаю рассылку объявления для {len(all_users)} пользователей")
    
    for user_id in all_users:
        try:
            # Проверяем, не получал ли пользователь уже это объявление
            if announcement_manager.is_announcement_sent(user_id, announcement_id):
                logging.info(f"Пользователь {user_id} уже получал это объявление")
                continue
            
            # Отправляем сообщение с картинкой или без
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=InputFile(photo),
                        caption=message_text,
                        parse_mode='HTML'
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message_text,
                    parse_mode='HTML'
                )
            
            # Отмечаем объявление как отправленное
            announcement_manager.mark_announcement_sent(user_id, announcement_id)
            successful_sends += 1
            
            # Небольшая задержка чтобы не превысить лимиты Telegram
            import asyncio
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logging.error(f"Не удалось отправить объявление пользователю {user_id}: {e}")
            failed_sends += 1
    
    logging.info(f"Рассылка завершена. Успешно: {successful_sends}, Не удалось: {failed_sends}")

def create_announcement_file():
    """Создает пример файла объявления"""
    announcement_template = {
        "message": "🎉 <b>Важное обновление!</b> 🎉\n\n"
                  "Дорогие пользователи! Мы добали новые функции:\n"
                  "✅ Еще больше математических заданий\n"
                  "✅ Улучшенная статистика\n"
                  "✅ Новые типы вопросов\n\n"
                  "<i>Спасибо, что учитесь с нами! 📚</i>",
        "photo_path": "announcement_image.jpg",  # Путь к картинке
        "announcement_id": "update_2024_new_features"  # Уникальный ID
    }
    
    with open('announcement_template.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(announcement_template, f, ensure_ascii=False, indent=2)
    
    print("Создан шаблон announcement_template.json")

if __name__ == "__main__":
    create_announcement_file()