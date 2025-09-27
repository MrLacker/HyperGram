from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = "8439259446:AAEvXaeZkV2Qxz1YfvJ9mOLCG2Gx-9IM6Wg"

# Простой словарь для хранения балансов (вместо файла)
user_balances = {}

async def start(update, context):
    user_id = update.effective_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
    
    await update.message.reply_text(
        f'👋 Добро пожаловать!\n'
        f'💰 Ваш баланс: ${user_balances[user_id]}\n\n'
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
    balance = user_balances.get(user_id, 0)
    await update.message.reply_text(f'💰 Ваш баланс: ${balance}')

async def handle_message(update, context):
    user_id = update.effective_user.id
    message_text = update.message.text.lower().strip()
    
    if user_id not in user_balances:
        user_balances[user_id] = 0
    
    if message_text == 'клик':
        user_balances[user_id] += 1
        await update.message.reply_text(
            f'🎉 +$1 добавлено на ваш баланс!\n'
            f'💰 Теперь у вас: ${user_balances[user_id]}'
        )
    else:
        # Игнорируем другие текстовые сообщения, которые не являются командами
        pass

def main():
    print("Бот запускается...")
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики команд
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("hello", hello))
        app.add_handler(CommandHandler("balance", balance))
        
        # Добавляем обработчик текстовых сообщений для кликов
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Обработчики добавлены, запускаем polling...")
        
        # Запускаем бота
        app.run_polling()
        
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
