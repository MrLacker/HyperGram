from telegram.ext import Application, CommandHandler

# ТОКЕН В КОДЕ (НЕ ДЕЛАЙ ТАК В БУДУЩЕМ!)
TOKEN = "8439259446:AAEvXaeZkV2Qxz1YfvJ9mOLCG2Gx-9IM6Wg"

async def start(update, context):
    await update.message.reply_text('Бот работает! Токен в коде.')

async def hello(update, context):
    await update.message.reply_text('Привет! Я живой!')

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", hello))
    
    print("Бот запускается...")
    app.run_polling()

if __name__ == '__main__':
    main()
