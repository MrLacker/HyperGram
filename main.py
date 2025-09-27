from telegram.ext import Application, CommandHandler, MessageHandler, filters
import json
import os

TOKEN = "8439259446:AAEvXaeZkV2Qxz1YfvJ9mOLCG2Gx-9IM6Wg"

# Файл для хранения данных пользователей
DATA_FILE = "user_data.json"

# Загрузка данных пользователей
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохранение данных пользователей
def save_user_data(user_data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

# Получение баланса пользователя
def get_user_balance(user_id):
    user_data = load_user_data()
    return user_data.get(str(user_id), 0)

# Обновление баланса пользователя
def update_user_balance(user_id, amount):
    user_data = load_user_data()
    user_id_str = str(user_id)
    current_balance = user_data.get(user_id_str, 0)
    user_data[user_id_str] = current_balance + amount
    save_user_data(user_data)
    return user_data[user_id_str]

async def start(update, context):
    user_id = update.effective_user.id
    balance = get_user_balance(user_id)
    await update.message.reply_text(
        f'👋 Добро пожаловать!\n'
        f'💰 Ваш баланс: ${balance}\n\n'
        f'💡 Доступные команды:\n'
        f'/start - начать работу\n'
        f'/hello - приветствие\n'
        f'/balance - проверить баланс\n'
        f'📝 Просто напишите "Клик" чтобы заработать $1!'
    )

async def hello(update, context):
    await update.message.reply_text('Привет! Я живой! 👋')

async def balance(update, context):
    user_id = update.effective_user.id
    balance = get_user_balance(user_id)
    await update.message.reply_text(f'💰 Ваш баланс: ${balance}')

async def handle_click(update, context):
    user_id = update.effective_user.id
    message_text = update.message.text.lower().strip()
    
    if message_text == 'клик':
        new_balance = update_user_balance(user_id, 1)
        await update.message.reply_text(
            f'🎉 +$1 добавлено на ваш баланс!\n'
            f'💰 Теперь у вас: ${new_balance}'
        )

def main():
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("balance", balance))
    
    # Добавляем обработчик текстовых сообщений для кликов
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_click))
    
    print("Бот запускается...")
    
    # Запускаем бота
    try:
        app.run_polling()
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
