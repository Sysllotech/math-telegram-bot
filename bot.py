import logging
import random
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database
from admin_commands import setup_admin_handlers


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class MathBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.db = Database()
        self.setup_handlers()
            
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("stats", self.show_stats_callback))
        self.application.add_handler(CommandHandler("quiz", self.start_quiz))
        self.application.add_handler(CallbackQueryHandler(self.handle_answer, pattern="^answer_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_operation, pattern="^op_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_navigation, pattern="^(back|show_stats|main_menu)$"))
        setup_admin_handlers(self.application)  # Добавляем команды админа
    
    def get_main_menu_keyboard(self):
        """Клавиатура главного меню"""
        keyboard = [
            [InlineKeyboardButton("➕ Сложение", callback_data="op_addition")],
            [InlineKeyboardButton("➖ Вычитание", callback_data="op_subtraction")],
            [InlineKeyboardButton("✖️ Умножение", callback_data="op_multiplication")],
            [InlineKeyboardButton("➗ Деление", callback_data="op_division")],
            [InlineKeyboardButton("🎲 Случайная операция", callback_data="op_random")],
            # Кнопки внизу клавиатуры
            [InlineKeyboardButton("⬅️ Назад", callback_data="back"),
             InlineKeyboardButton("📊 Статистика", callback_data="show_stats")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_quiz_keyboard(self):
        """Клавиатура во время викторины"""
        keyboard = [
            # Кнопки внизу клавиатуры
            [InlineKeyboardButton("⬅️ Назад", callback_data="back"),
             InlineKeyboardButton("📊 Статистика", callback_data="show_stats")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_stats_keyboard(self):
        """Клавиатура для страницы статистики"""
        keyboard = [
            [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu"),
             InlineKeyboardButton("🎮 Продолжить", callback_data="back")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = f"""
Привет, {user.first_name}! 👋

Я бот для тренировки математических навыков!

Доступные команды:
/quiz - начать викторину
/stats - посмотреть статистику

Выбери операцию для начала:
        """
        
        await update.message.reply_text(welcome_text, reply_markup=self.get_main_menu_keyboard())
    
    async def start_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /quiz"""
        await update.message.reply_text("Выбери тип операций:", reply_markup=self.get_main_menu_keyboard())
    
    async def handle_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора операции"""
        query = update.callback_query
        await query.answer()
        
        operation = query.data.replace("op_", "")
        await self.send_question(update, context, operation)
    
    async def handle_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик навигационных кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "back":
            await self.show_main_menu(update, context)
        elif data == "show_stats":
            await self.show_stats_callback(update, context)
        elif data == "main_menu":
            await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        text = "Выбери тип операций для викторины:"
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(text, reply_markup=self.get_main_menu_keyboard())
        else:
            await update.message.reply_text(text, reply_markup=self.get_main_menu_keyboard())
    
    async def show_stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику через callback"""
        query = update.callback_query
        user = update.effective_user
        stats = self.db.get_user_stats(user.id)
        
        if stats:
            text = f"""
📊 Твоя статистика, {user.first_name}:

Всего вопросов: {stats['total_questions']}
Правильных ответов: {stats['correct_answers']}
Точность: {stats['accuracy']}%
            """
        else:
            text = "Статистика не найдена. Начни викторину!"
        
        await query.edit_message_text(text, reply_markup=self.get_stats_keyboard())
    
    def generate_question(self, operation_type, context=None):
        if operation_type == "random":
            operation_type = random.choice(["addition", "subtraction", "multiplication", "division"])
        
        if operation_type == "addition":
            # Сложение: числа от 1 до 100
            a = random.randint(1, 500)
            b = random.randint(1, 500)
            question = f"{a} + {b}"
            answer = a + b
            
        elif operation_type == "subtraction":
            # Вычитание: гарантируем положительный результат
            a = random.randint(10, 250)
            b = random.randint(1, a - 1)
            question = f"{a} - {b}"
            answer = a - b
            
        elif operation_type == "multiplication":
            # Умножение: числа от 2 до 12 (таблица умножения)
            a = random.randint(2, 15)
            b = random.randint(2, 15)
            question = f"{a} × {b}"
            answer = a * b
            
        elif operation_type == "division":
            # Деление: гарантируем целый результат
            b = random.randint(2, 15)
            a = b * random.randint(2, 15)  # a кратно b
            question = f"{a} ÷ {b}"
            answer = a // b
        
        # Генерация неправильных ответов
        wrong_answers = []
        while len(wrong_answers) < 3:
            # Создаем варианты, близкие к правильному ответу
            variation = random.choice([-3, -2, -1, 1, 2, 3])
            wrong_answer = answer + variation
            
            # Проверяем, чтобы неправильный ответ был положительным и уникальным
            if (wrong_answer > 0 and 
                wrong_answer != answer and 
                wrong_answer not in wrong_answers):
                wrong_answers.append(wrong_answer)
        
        # Создание списка всех ответов и их перемешивание
        all_answers = wrong_answers + [answer]
        random.shuffle(all_answers)
        
        return {
            "question": question,
            "correct_answer": answer,
            "all_answers": all_answers,
            "operation_type": operation_type
        }




    
    async def send_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, operation_type):
        """Отправка вопроса пользователю"""
        question_data = self.generate_question(operation_type, context)  # ← передаем context
        
        # Сохраняем правильный ответ в контексте
        context.user_data['current_question'] = {
            'correct_answer': question_data["correct_answer"],
            'operation_type': question_data["operation_type"]
        }
        
        # Создаем клавиатуру с вариантами ответов
        keyboard = []
        for i, answer in enumerate(question_data["all_answers"]):
            keyboard.append([InlineKeyboardButton(str(answer), callback_data=f"answer_{answer}")])
        
        # Добавляем навигационные кнопки
        keyboard.extend(self.get_quiz_keyboard().inline_keyboard)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"Вопрос: {question_data['question']} = ?"
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)



    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ответа пользователя с автоматическим переходом к следующему вопросу"""
        query = update.callback_query
        user_answer = float(query.data.replace("answer_", ""))
        
        correct_answer = context.user_data['current_question']['correct_answer']
        operation_type = context.user_data['current_question']['operation_type']
        
        user = update.effective_user
        is_correct = user_answer == correct_answer
        
        # Обновляем статистику
        self.db.update_user_stats(user.id, is_correct)
        
        # Отправляем результат
        if is_correct:
            message = "✅ Отлично! Продолжаем!"
        else:
            message = f"❌ Почти! Правильный ответ: {correct_answer}"
        
        await query.answer()
        
        # Показываем результат на 2 секунды
        await query.edit_message_text(message)
        
        # Ждем 2 секунды и автоматически показываем следующий вопрос
        import asyncio
        await asyncio.sleep(1.15)
        
        # Автоматически переходим к следующему вопросу
        await self.send_question(update, context, operation_type)

    

    
    def run(self):
            """Запуск бота"""
            self.application.run_polling()

# Запуск бота
if __name__ == "__main__":
    import os
    # Получите токен у @BotFather в Telegram
    BOT_TOKEN = os.environ.get('BOT_TOKEN','8528078230:AAFf1YQJ7fRbzlO_VYR_TKpUTKk7V37b7Rk')
    
    bot = MathBot(BOT_TOKEN)
    bot.run()
