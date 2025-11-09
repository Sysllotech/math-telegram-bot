import logging
import json
import os
import sqlite3
from datetime import datetime
from telegram import Update, MenuButtonCommands
from telegram.ext import ContextTypes, CommandHandler
from announcement import send_global_announcement



# ⚠️ ЗАМЕНИТЕ ЭТОТ ID НА СВОЙ! ⚠️
ADMIN_IDS = [1302211108]

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS




async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для отправки глобального объявления"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /announce <текст>\n\n"
            "Пример: /announce Привет всем! Мы добавили новые задания! 🎉"
        )
        return
    
    # Простое текстовое объявление
    message_text = " ".join(context.args)
    message_text = f"📢 <b>Объявление от администратора:</b>\n\n{message_text}"
    
    try:
        await update.message.reply_text("🔄 Начинаю рассылку...")
        await send_global_announcement(context, message_text)
        await update.message.reply_text("✅ Объявление отправлено всем пользователям!")
    except Exception as e:
        logging.error(f"Ошибка при рассылке: {e}")
        await update.message.reply_text("❌ Ошибка при отправке объявления")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая команда для простых объявлений"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /broadcast <текст>")
        return
    
    message_text = " ".join(context.args)
    message_text = f"📢 <b>Объявление:</b>\n\n{message_text}"
    
    try:
        await update.message.reply_text("🔄 Начинаю рассылку...")
        await send_global_announcement(context, message_text, announcement_id=f"quick_{user_id}_{datetime.now().strftime('%H%M%S')}")
        await update.message.reply_text("✅ Объявление отправлено!")
    except Exception as e:
        logging.error(f"Ошибка при рассылке: {e}")
        await update.message.reply_text("❌ Ошибка при отправке")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает подробную статистику бота - ТО САМАЯ КОМАНДА ДЛЯ СТАТИСТИКИ!"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    from database import Database
    db = Database()
    
    conn = sqlite3.connect('math_bot.db')
    cursor = conn.cursor()
    
    # Статистика по пользователям
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE total_questions > 0')
    active_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE total_questions = 0')
    new_users = cursor.fetchone()[0]
    
    # Общая статистика по ответам
    cursor.execute('SELECT SUM(total_questions), SUM(correct_answers) FROM users')
    result = cursor.fetchone()
    total_questions = result[0] or 0
    total_correct = result[1] or 0
    
    # Точность
    accuracy = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0
    
    # Самые активные пользователи
    cursor.execute('''
        SELECT first_name, total_questions, correct_answers 
        FROM users 
        WHERE total_questions > 0 
        ORDER BY total_questions DESC 
        LIMIT 5
    ''')
    top_users = cursor.fetchall()
    
    # Статистика по датам (последние 7 дней)
    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as new_users
        FROM users 
        WHERE created_at >= date('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ''')
    recent_users = cursor.fetchall()
    
    # Формируем красивый отчет
    stats_text = f"""
📊 <b>ПОЛНАЯ СТАТИСТИКА БОТА</b>
━━━━━━━━━━━━━━━━━━━━

👥 <b>Пользователи:</b>
• Всего пользователей: <b>{total_users}</b>
• Активных (отвечали): <b>{active_users}</b>
• Новых (еще не играли): <b>{new_users}</b>

🎯 <b>Общая активность:</b>
• Всего вопросов: <b>{total_questions}</b>
• Правильных ответов: <b>{total_correct}</b>
• Общая точность: <b>{accuracy}%</b>

"""
    
    # Добавляем топ пользователей
    if top_users:
        stats_text += "🏆 <b>Топ-5 самых активных:</b>\n"
        for i, (name, total, correct) in enumerate(top_users, 1):
            user_accuracy = round((correct / total) * 100, 2) if total > 0 else 0
            stats_text += f"{i}. {name}: {total} вопросов ({user_accuracy}%)\n"
    
    # Добавляем статистику по дням
    if recent_users:
        stats_text += "\n📈 <b>Новые пользователи по дням:</b>\n"
        for date, count in recent_users:
            stats_text += f"• {date}: +{count} чел.\n"
    
    stats_text += f"\n⏰ <b>Последнее обновление:</b>\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    await update.message.reply_text(stats_text, parse_mode='HTML')
    conn.close()
    async def quick_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    conn = sqlite3.connect('math_bot.db')
    cursor = conn.cursor()
    
    # Основные метрики
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE total_questions > 0')
    active_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(total_questions), SUM(correct_answers) FROM users')
    result = cursor.fetchone()
    total_questions = result[0] or 0
    total_correct = result[1] or 0
    
    accuracy = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0
    
    quick_text = f"""
📊 <b>Быстрая статистика:</b>

👥 Пользователи: {total_users}
🎮 Активных: {active_users}
❓ Вопросов: {total_questions}
✅ Правильно: {total_correct}
🎯 Точность: {accuracy}%
    """
    
    await update.message.reply_text(quick_text, parse_mode='HTML')
    conn.close()

async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика по конкретному пользователю"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    if context.args:
        # Если передан username или ID
        target = context.args[0]
        conn = sqlite3.connect('math_bot.db')
        cursor = conn.cursor()
        
        # Пробуем найти по ID или username
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, total_questions, correct_answers, created_at
            FROM users 
            WHERE user_id = ? OR username = ?
        ''', (target, target.replace('@', '')))
        
        user_data = cursor.fetchone()
        
        if user_data:
            user_id, username, first_name, last_name, total, correct, created_at = user_data
            accuracy = round((correct / total) * 100, 2) if total > 0 else 0
            
            user_text = f"""
👤 <b>Статистика пользователя:</b>

Имя: {first_name} {last_name or ''}
Username: @{username or 'нет'}
ID: {user_id}
Дата регистрации: {created_at[:10]}

❓ Всего вопросов: {total}
✅ Правильных: {correct}
🎯 Точность: {accuracy}%
            """
            await update.message.reply_text(user_text, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Пользователь не найден")
        
        conn.close()
    else:
        await update.message.reply_text("Использование: /user_stats <id или username>")

async def quick_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая статистика - короткая версия"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    conn = sqlite3.connect('math_bot.db')
    cursor = conn.cursor()
    
    try:
        # Основные метрики
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE total_questions > 0')
        active_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_questions), SUM(correct_answers) FROM users')
        result = cursor.fetchone()
        total_questions = result[0] or 0
        total_correct = result[1] or 0
        
        accuracy = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0
        
        quick_text = f"""
📊 <b>Быстрая статистика:</b>

👥 Пользователи: {total_users}
🎮 Активных: {active_users}
❓ Вопросов: {total_questions}
✅ Правильно: {total_correct}
🎯 Точность: {accuracy}%
        """
        
        await update.message.reply_text(quick_text, parse_mode='HTML')
    
    except Exception as e:
        logging.error(f"Ошибка при получении статистики: {e}")
        await update.message.reply_text("❌ Ошибка при получении статистики")
    
    finally:
        conn.close()


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит список всех пользователей"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    conn = sqlite3.connect('math_bot.db')
    
    try:
        cursor = conn.cursor()
        
        # Получаем всех пользователей
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, total_questions, correct_answers, created_at
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        all_users = cursor.fetchall()
        
        if not all_users:
            await update.message.reply_text("📭 В базе нет пользователей")
            return
        
        users_text = "👥 <b>Список всех пользователей:</b>\n\n"
        
        for i, (user_id, username, first_name, last_name, total, correct, created_at) in enumerate(all_users, 1):
            accuracy = round((correct / total) * 100, 2) if total > 0 else 0
            users_text += f"{i}. {first_name} {last_name or ''} (@{username or 'нет'})\n"
            users_text += f"   ID: {user_id} | Вопросов: {total} | Точность: {accuracy}%\n"
            users_text += f"   Зарегистрирован: {created_at[:10]}\n\n"
        
        # Если сообщение слишком длинное, разбиваем на части
        if len(users_text) > 4000:
            parts = [users_text[i:i+4000] for i in range(0, len(users_text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
        else:
            await update.message.reply_text(users_text, parse_mode='HTML')
    
    except Exception as e:
        logging.error(f"Ошибка при получении списка пользователей: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка пользователей")
    
    finally:
        conn.close()


def setup_admin_handlers(application):
    """Добавляет обработчики команд администратора"""
    application.add_handler(CommandHandler("announce", announce))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))  # Полная статистика
    application.add_handler(CommandHandler("quick_stats", quick_stats))  # Быстрая статистика
    application.add_handler(CommandHandler("user_stats", user_stats))  # Статистика пользователя
    application.add_handler(CommandHandler("list_users", list_users))

