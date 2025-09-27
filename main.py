import telebot
import json
import random
import os
import datetime
import time
import threading
import aiohttp
import asyncio

# Токены
TOKEN = '7925425735:AAGqffm_l2GCAF9DjLQqF1LqpP9vVU6sH4E'
NEUROIMG_TOKEN = 'c505ab11-1058-42e8-a280-0bf6fd950b61'
bot = telebot.TeleBot(TOKEN)

# Структура для хранения данных
class ChatData:
    def __init__(self):
        self.words = []
        self.talking_mode = True
        self.rules = "Правила еще не установлены. Администратор может установить правила командой /setrules"
        self.image_generation = True
        self.muted_users = {}

class UserData:
    def __init__(self):
        self.balance = 5.0
        self.user_id = None
        self.username = ""
        self.first_name = ""
        self.inventory = {}
        self.active_gift = None
        self.warnings = 0

class MarketItem:
    def __init__(self, seller_id, gift_name, price, quantity):
        self.seller_id = seller_id
        self.gift_name = gift_name
        self.price = price
        self.quantity = quantity
        self.slot_id = f"{seller_id}_{gift_name}_{int(time.time())}"

# Глобальные словари для хранения данных
chat_data = {}
user_data = {}
market_items = {}
user_states = {}  # Для отслеживания состояний пользователей

# Файлы для хранения данных
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Загрузка подарков из файла
def load_gifts():
    try:
        with open('gifts.txt', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return [gift.strip() for gift in content.split(',')]
            else:
                return ["❤️", "🔥", "⭐", "🎁", "🎉", "💎", "👑", "🏆", "✨", "🌟"]
    except:
        return ["❤️", "🔥", "⭐", "🎁", "🎉", "💎", "👑", "🏆", "✨", "🌟"]

def save_gifts(gifts_list):
    try:
        with open('gifts.txt', 'w', encoding='utf-8') as f:
            f.write(','.join(gifts_list))
    except:
        pass

GIFTS = load_gifts()
REACTIONS = ["🤨", "❤️", "👍", "🔥", "🤔"]

def get_chat_filename(chat_id):
    return os.path.join(DATA_DIR, f"{chat_id}_words.json")

def get_user_filename(user_id):
    return os.path.join(DATA_DIR, f"user_{user_id}.json")

def get_market_filename():
    return os.path.join(DATA_DIR, "market.json")

def load_chat_data(chat_id):
    filename = get_chat_filename(chat_id)
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chat_data[chat_id] = ChatData()
                chat_data[chat_id].words = data.get('words', [])
                chat_data[chat_id].talking_mode = data.get('talking_mode', True)
                chat_data[chat_id].rules = data.get('rules', "Правила еще не установлены. Администратор может установить правила командой /setrules")
                chat_data[chat_id].image_generation = data.get('image_generation', True)
                chat_data[chat_id].muted_users = data.get('muted_users', {})
        except Exception as e:
            print(f"Error loading chat data: {e}")
            chat_data[chat_id] = ChatData()
    else:
        chat_data[chat_id] = ChatData()
    return chat_data[chat_id]

def load_user_data(user_id, username="", first_name=""):
    filename = get_user_filename(user_id)
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_data[user_id] = UserData()
                user_data[user_id].balance = data.get('balance', 5.0)
                user_data[user_id].user_id = user_id
                user_data[user_id].username = data.get('username', username)
                user_data[user_id].first_name = data.get('first_name', first_name)
                user_data[user_id].inventory = data.get('inventory', {})
                user_data[user_id].active_gift = data.get('active_gift')
                user_data[user_id].warnings = data.get('warnings', 0)
        except Exception as e:
            print(f"Error loading user data: {e}")
            user_data[user_id] = UserData()
            user_data[user_id].balance = 5.0
            user_data[user_id].user_id = user_id
            user_data[user_id].username = username
            user_data[user_id].first_name = first_name
            user_data[user_id].inventory = {}
            user_data[user_id].active_gift = None
            user_data[user_id].warnings = 0
    else:
        user_data[user_id] = UserData()
        user_data[user_id].balance = 5.0
        user_data[user_id].user_id = user_id
        user_data[user_id].username = username
        user_data[user_id].first_name = first_name
        user_data[user_id].inventory = {}
        user_data[user_id].active_gift = None
        user_data[user_id].warnings = 0
        save_user_data(user_id)
    return user_data[user_id]

def load_market_data():
    global market_items
    filename = get_market_filename()
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                market_items = data
        except:
            market_items = {}

def save_market_data():
    filename = get_market_filename()
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(market_items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving market data: {e}")

def save_chat_data(chat_id):
    filename = get_chat_filename(chat_id)
    if chat_id in chat_data:
        data = {
            'words': chat_data[chat_id].words,
            'talking_mode': chat_data[chat_id].talking_mode,
            'rules': chat_data[chat_id].rules,
            'image_generation': chat_data[chat_id].image_generation,
            'muted_users': chat_data[chat_id].muted_users
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def save_user_data(user_id):
    filename = get_user_filename(user_id)
    if user_id in user_data:
        data = {
            'balance': user_data[user_id].balance,
            'user_id': user_data[user_id].user_id,
            'username': user_data[user_id].username,
            'first_name': user_data[user_id].first_name,
            'inventory': user_data[user_id].inventory,
            'active_gift': user_data[user_id].active_gift,
            'warnings': user_data[user_id].warnings
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(chat_id, user_id):
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['administrator', 'creator']
    except:
        return False

def is_muted(chat_id, user_id):
    data = load_chat_data(chat_id)
    if str(user_id) in data.muted_users:
        mute_time = data.muted_users[str(user_id)]
        if mute_time > time.time():
            return True
        else:
            del data.muted_users[str(user_id)]
            save_chat_data(chat_id)
    return False

def extract_words(text):
    words = []
    for word in text.split():
        clean_word = ''.join(char for char in word if char.isalnum()).lower()
        if clean_word and len(clean_word) > 1:
            words.append(clean_word)
    return words

def get_random_response(chat_id):
    data = load_chat_data(chat_id)
    if not data.words:
        return "Я еще не научился разговаривать... Напишите что-нибудь!"
    
    word_count = 3 if random.random() < 0.3 else 2
    
    if len(data.words) >= word_count:
        response_words = random.sample(data.words, word_count)
    else:
        response_words = data.words
    
    return ' '.join(response_words)

async def generate_image(prompt: str):
    async with aiohttp.ClientSession() as session:
        payload = {
            "token": NEUROIMG_TOKEN,
            "prompt": prompt,
            "stream": True
        }
        
        async with session.post(
            "https://neuroimg.art/api/v1/free-generate",
            json=payload
        ) as response:
            async for line in response.content:
                if line:
                    try:
                        data = json.loads(line)
                        if data["status"] == "SUCCESS":
                            return data["image_url"]
                        print(f"Статус: {data['status']}")
                    except:
                        pass
    return None

def process_txt_file(file_content, chat_id):
    try:
        text = file_content.decode('utf-8')
        words = extract_words(text)
        
        data = load_chat_data(chat_id)
        data.words.extend(words)
        data.words = list(set(data.words))
        save_chat_data(chat_id)
        
        return len(words)
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        return 0

def get_user_display_name(user_id):
    user = load_user_data(user_id)
    if user.active_gift:
        return f"{user.active_gift} {user.first_name}"
    return user.first_name

def get_market_items_page(page, items_per_page=4):
    items = list(market_items.values())
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    return items[start_idx:end_idx], len(items)

def add_market_item(seller_id, gift_name, price, quantity):
    slot_id = f"{seller_id}_{gift_name}_{int(time.time())}"
    market_items[slot_id] = {
        'seller_id': seller_id,
        'gift_name': gift_name,
        'price': price,
        'quantity': quantity,
        'slot_id': slot_id
    }
    save_market_data()
    return slot_id

def remove_market_item(slot_id):
    if slot_id in market_items:
        del market_items[slot_id]
        save_market_data()
        return True
    return False

# Загрузка данных при старте
load_market_data()

# ========== КОМАНДЫ МОДЕРАЦИИ ==========

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите замутить!")
        return
    
    target_user_id = message.reply_to_message.from_user.id
    target_username = message.reply_to_message.from_user.first_name
    
    if is_admin(chat_id, target_user_id):
        bot.reply_to(message, "❌ Нельзя замутить администратора!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Используйте: /mute время_в_минутах [причина]")
        return
    
    try:
        mute_minutes = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "Не указана"
        
        mute_until = time.time() + (mute_minutes * 60)
        data = load_chat_data(chat_id)
        data.muted_users[str(target_user_id)] = mute_until
        save_chat_data(chat_id)
        
        bot.reply_to(message, f"🔇 Пользователь {target_username} замьючен на {mute_minutes} минут.\nПричина: {reason}")
        
    except ValueError:
        bot.reply_to(message, "❌ Укажите корректное время в минутах!")

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите размутить!")
        return
    
    target_user_id = message.reply_to_message.from_user.id
    target_username = message.reply_to_message.from_user.first_name
    
    data = load_chat_data(chat_id)
    if str(target_user_id) in data.muted_users:
        del data.muted_users[str(target_user_id)]
        save_chat_data(chat_id)
        bot.reply_to(message, f"🔊 Пользователь {target_username} размучен!")
    else:
        bot.reply_to(message, f"❌ Пользователь {target_username} не замьючен!")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите забанить!")
        return
    
    target_user_id = message.reply_to_message.from_user.id
    target_username = message.reply_to_message.from_user.first_name
    
    if is_admin(chat_id, target_user_id):
        bot.reply_to(message, "❌ Нельзя забанить администратора!")
        return
    
    reason = " ".join(message.text.split()[1:]) if len(message.text.split()) > 1 else "Не указана"
    
    try:
        bot.ban_chat_member(chat_id, target_user_id)
        bot.reply_to(message, f"🚫 Пользователь {target_username} забанен.\nПричина: {reason}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при бане: {e}")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Используйте: /unban user_id")
        return
    
    try:
        target_user_id = int(args[1])
        bot.unban_chat_member(chat_id, target_user_id)
        bot.reply_to(message, f"✅ Пользователь разбанен!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при разбане: {e}")

@bot.message_handler(commands=['warn'])
def warn_user(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите предупредить!")
        return
    
    target_user_id = message.reply_to_message.from_user.id
    target_username = message.reply_to_message.from_user.first_name
    
    if is_admin(chat_id, target_user_id):
        bot.reply_to(message, "❌ Нельзя предупредить администратора!")
        return
    
    reason = " ".join(message.text.split()[1:]) if len(message.text.split()) > 1 else "Не указана"
    
    user = load_user_data(target_user_id)
    user.warnings += 1
    save_user_data(target_user_id)
    
    if user.warnings >= 3:
        try:
            bot.ban_chat_member(chat_id, target_user_id)
            bot.reply_to(message, f"🚫 Пользователь {target_username} забанен за 3 предупреждения!")
        except:
            bot.reply_to(message, f"⚠️ {target_username} получил 3 предупреждения, но бан не удался!")
    else:
        bot.reply_to(message, f"⚠️ {target_username} получил предупреждение ({user.warnings}/3)\nПричина: {reason}")

# ========== КОМАНДЫ ПРОФИЛЯ И МАГАЗИНА ==========

@bot.message_handler(commands=['profile'])
def show_profile(message):
    user_id = message.from_user.id
    user = load_user_data(user_id, message.from_user.username, message.from_user.first_name)
    
    user.username = message.from_user.username or ""
    user.first_name = message.from_user.first_name
    save_user_data(user_id)
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🎒 Инвентарь", callback_data=f"inventory_{user_id}"))
    
    active_gift_display = user.active_gift if user.active_gift else "Не выбран"
    
    profile_text = (
        f"👤 **Профиль пользователя**\n\n"
        f"🆔 ID: {user_id}\n"
        f"👋 Имя: {get_user_display_name(user_id)}\n"
        f"📛 Username: @{user.username if user.username else 'нет'}\n"
        f"💰 Баланс: ${user.balance}\n"
        f"🎁 Активный подарок: {active_gift_display}\n"
        f"⚠️ Предупреждения: {user.warnings}/3\n"
        f"🎒 Предметов в инвентаре: {sum(user.inventory.values())}\n\n"
        f"*Используйте /shop для покупки подарков*"
    )
    
    bot.reply_to(message, profile_text, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['inventory'])
def show_inventory(message):
    user_id = message.from_user.id
    user = load_user_data(user_id)
    
    if not user.inventory:
        bot.reply_to(message, "🎒 **Ваш инвентарь пуст**\n\nЗдесь будут отображаться ваши подарки")
        return
    
    inventory_text = "🎒 **Ваш инвентарь:**\n\n"
    for gift, count in user.inventory.items():
        inventory_text += f"{gift} - {count} шт.\n"
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    for gift in user.inventory.keys():
        if user.inventory[gift] > 0:
            keyboard.add(telebot.types.InlineKeyboardButton(
                f"Использовать {gift}", 
                callback_data=f"use_gift_{user_id}_{gift}"
            ))
            keyboard.add(telebot.types.InlineKeyboardButton(
                f"Продать {gift}", 
                callback_data=f"sell_gift_{user_id}_{gift}"
            ))
    
    bot.reply_to(message, inventory_text, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['shop'])
def show_shop(message):
    user_id = message.from_user.id
    user = load_user_data(user_id)
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🎁 Кейсы", callback_data=f"cases_{user_id}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🏪 Рынок", callback_data=f"market_main_{user_id}_1"))
    
    shop_text = (
        f"🏪 **Магазин подарков**\n\n"
        f"💰 Ваш баланс: ${user.balance}\n\n"
        f"🎁 **Кейсы** - случайный подарок за $2\n"
        f"🏪 **Рынок** - купить/продать подарки\n\n"
        f"*Выберите раздел:*"
    )
    
    bot.reply_to(message, shop_text, reply_markup=keyboard, parse_mode='Markdown')

# ========== CALLBACK ОБРАБОТЧИКИ ==========

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        if call.data.startswith('inventory_'):
            user_id = int(call.data.split('_')[1])
            if user_id != call.from_user.id:
                bot.answer_callback_query(call.id, "❌ Это не ваш инвентарь!")
                return
            
            user = load_user_data(user_id)
            if not user.inventory:
                bot.edit_message_text("🎒 **Ваш инвентарь пуст**", 
                                    call.message.chat.id, 
                                    call.message.message_id,
                                    parse_mode='Markdown')
                return
            
            inventory_text = "🎒 **Ваш инвентарь:**\n\n"
            for gift, count in user.inventory.items():
                inventory_text += f"{gift} - {count} шт.\n"
            
            keyboard = telebot.types.InlineKeyboardMarkup()
            for gift in user.inventory.keys():
                if user.inventory[gift] > 0:
                    keyboard.add(telebot.types.InlineKeyboardButton(
                        f"Использовать {gift}", 
                        callback_data=f"use_gift_{user_id}_{gift}"
                    ))
                    keyboard.add(telebot.types.InlineKeyboardButton(
                        f"Продать {gift}", 
                        callback_data=f"sell_gift_{user_id}_{gift}"
                    ))
            
            bot.edit_message_text(inventory_text, 
                                call.message.chat.id, 
                                call.message.message_id,
                                reply_markup=keyboard,
                                parse_mode='Markdown')
            bot.answer_callback_query(call.id)
        
        elif call.data.startswith('use_gift_'):
            parts = call.data.split('_')
            user_id = int(parts[2])
            gift = parts[3]
            
            if user_id != call.from_user.id:
                bot.answer_callback_query(call.id, "❌ Это не ваш подарок!")
                return
            
            user = load_user_data(user_id)
            if gift in user.inventory and user.inventory[gift] > 0:
                user.active_gift = gift
                save_user_data(user_id)
                bot.answer_callback_query(call.id, f"✅ Подарок {gift} активирован!")
            else:
                bot.answer_callback_query(call.id, "❌ У вас нет этого подарка!")
        
        elif call.data.startswith('sell_gift_'):
            parts = call.data.split('_')
            user_id = int(parts[2])
            gift = parts[3]
            
            if user_id != call.from_user.id:
                bot.answer_callback_query(call.id, "❌ Это не ваш подарок!")
                return
            
            user = load_user_data(user_id)
            if gift not in user.inventory or user.inventory[gift] <= 0:
                bot.answer_callback_query(call.id, "❌ У вас нет этого подарка!")
                return
            
            user_states[user_id] = {'action': 'sell_gift', 'gift': gift}
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, f"💸 Продажа подарка {gift}\n\nВведите количество для продажи (до {user.inventory[gift]} шт.):")
        
        elif call.data.startswith('cases_'):
            user_id = int(call.data.split('_')[1])
            if user_id != call.from_user.id:
                bot.answer_callback_query(call.id, "❌ Это не ваш магазин!")
                return
            
            user = load_user_data(user_id)
            
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton(
                "🎁 Купить кейс за $2", 
                callback_data=f"buy_case_{user_id}"
            ))
            keyboard.add(telebot.types.InlineKeyboardButton(
                "🔙 Назад", 
                callback_data=f"back_to_shop_{user_id}"
            ))
            
            cases_text = (
                f"🎁 **Кейсы**\n\n"
                f"💰 Ваш баланс: ${user.balance}\n\n"
                f"За $2 вы получаете случайный подарок:\n"
                f"{', '.join(GIFTS)}\n\n"
                f"*Попробуйте удачу!*"
            )
            
            bot.edit_message_text(cases_text, 
                                call.message.chat.id, 
                                call.message.message_id,
                                reply_markup=keyboard,
                                parse_mode='Markdown')
            bot.answer_callback_query(call.id)
        
        elif call.data.startswith('buy_case_'):
            user_id = int(call.data.split('_')[2])
            if user_id != call.from_user.id:
                bot.answer_callback_query(call.id, "❌ Это не ваш магазин!")
                return
            
            user = load_user_data(user_id)
            
            if user.balance < 2:
                bot.answer_callback_query(call.id, "❌ Недостаточно средств!")
                return
            
            user.balance -= 2
            random_gift = random.choice(GIFTS)
            
            if random_gift in user.inventory:
                user.inventory[random_gift] += 1
            else:
                user.inventory[random_gift] = 1
            
            save_user_data(user_id)
            
            bot.answer_callback_query(call.id, f"🎁 Вы получили: {random_gift}!")
            
            user = load_user_data(user_id)
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton(
                "🎁 Купить еще кейс за $2", 
                callback_data=f"buy_case_{user_id}"
            ))
            keyboard.add(telebot.types.InlineKeyboardButton(
                "🔙 Назад", 
                callback_data=f"back_to_shop_{user_id}"
            ))
            
            cases_text = (
                f"🎁 **Кейсы**\n\n"
                f"💰 Ваш баланс: ${user.balance}\n\n"
                f"🎉 Вы получили: {random_gift}!\n\n"
                f"За $2 вы получаете случайный подарок:\n"
                f"{', '.join(GIFTS)}\n\n"
                f"*Попробуйте удачу еще раз!*"
            )
            
            bot.edit_message_text(cases_text, 
                                call.message.chat.id, 
                                call.message.message_id,
                                reply_markup=keyboard,
                                parse_mode='Markdown')
        
        elif call.data.startswith('market_main_'):
            parts = call.data.split('_')
            user_id = int(parts[2])
            page = int(parts[3])
            
            if user_id != call.from_user.id:
                bot.answer_callback_query(call.id, "❌ Это не ваш магазин!")
                return
            
            market_items_list, total_items = get_market_items_page(page)
            user = load_user_data(user_id)
            
            market_text = f"🏪 **Рынок** - Страница {page}\n\n"
            market_text += f"💰 Ваш баланс: ${user.balance}\n"
            market_text += f"📦 Всего товаров: {total_items}\n\n"
            
            if not market_items_list:
                market_text += "📭 На рынке пока нет товаров\n"
            else:
                for i, item in enumerate(market_items_list, 1):
                    seller = load_user_data(item['seller_id'])
                    market_text += f"{i}. {item['gift_name']} - {item['quantity']}шт. - ${item['price']} за шт.\n"
                    market_text += f"   Продавец: {seller.first_name}\n\n"
            
            keyboard = telebot.types.InlineKeyboardMarkup()
            
            if market_items_list:
                for i, item in enumerate(market_items_list, 1):
                    keyboard.add(telebot.types.InlineKeyboardButton(
                        f"Купить {item['gift_name']} - ${item['price']}", 
                        callback_data=f"buy_item_{user_id}_{item['slot_id']}"
                    ))
            
            nav_buttons = []
            if page > 1:
                nav_buttons.append(telebot.types.InlineKeyboardButton(
                    "⬅️ Назад", callback_data=f"market_main_{user_id}_{page-1}"
                ))
            if len(market_items_list) == 4:
                nav_buttons.append(telebot.types.InlineKeyboardButton(
                    "Вперед ➡️", callback_data=f"market_main_{user_id}_{page+1}"
                ))
            
            if nav_buttons:
                keyboard.add(*nav_buttons)
            
            keyboard.add(telebot.types.InlineKeyboardButton(
                "🔙 Назад", callback_data=f"back_to_shop_{user_id}"
            ))
            
            bot.edit_message_text(market_text, 
                                call.message.chat.id, 
                                call.message.message_id,
                                reply_markup=keyboard,
                                parse_mode='Markdown')
            bot.answer_callback_query(call.id)
        
        elif call.data.startswith('buy_item_'):
            parts = call.data.split('_')
            user_id = int(parts[2])
            slot_id = parts[3]
            
            if user_id != call.from_user.id:
                bot.answer_callback_query(call.id, "❌ Ошибка!")
                return
            
            if slot_id not in market_items:
                bot.answer_callback_query(call.id, "❌ Товар уже продан!")
                return
            
            item = market_items[slot_id]
            user = load_user_data(user_id)
            total_price = item['price'] * item['quantity']
            
            if user.balance < total_price:
                bot.answer_callback_query(call.id, "❌ Недостаточно средств!")
                return
            
            # Совершаем покупку
            user.balance -= total_price
            if item['gift_name'] in user.inventory:
                user.inventory[item['gift_name']] += item['quantity']
            else:
                user.inventory[item['gift_name']] = item['quantity']
            
            # Переводим деньги продавцу
            seller = load_user_data(item['seller_id'])
            seller.balance += total_price
            save_user_data(item['seller_id'])
            
            save_user_data(user_id)
            remove_market_item(slot_id)
            
            bot.answer_callback_query(call.id, f"✅ Покупка совершена! Получено {item['quantity']} {item['gift_name']}")
            
            # Уведомляем продавца
            try:
                bot.send_message(item['seller_id'], f"🎉 Ваш товар {item['gift_name']} продан! Получено ${total_price}")
            except:
                pass
        
        elif call.data.startswith('back_to_shop_'):
            user_id = int(call.data.split('_')[3])
            user = load_user_data(user_id)
            
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton("🎁 Кейсы", callback_data=f"cases_{user_id}"))
            keyboard.add(telebot.types.InlineKeyboardButton("🏪 Рынок", callback_data=f"market_main_{user_id}_1"))
            
            shop_text = (
                f"🏪 **Магазин подарков**\n\n"
                f"💰 Ваш баланс: ${user.balance}\n\n"
                f"🎁 **Кейсы** - случайный подарок за $2\n"
                f"🏪 **Рынок** - купить/продать подарки\n\n"
                f"*Выберите раздел:*"
            )
            
            bot.edit_message_text(shop_text, 
                                call.message.chat.id, 
                                call.message.message_id,
                                reply_markup=keyboard,
                                parse_mode='Markdown')
            bot.answer_callback_query(call.id)
            
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!")

# ========== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ДЛЯ РЫНКА ==========

@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def handle_user_state(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if state.get('action') == 'sell_gift':
        try:
            quantity = int(message.text)
            gift = state['gift']
            user = load_user_data(user_id)
            
            if quantity <= 0 or quantity > user.inventory.get(gift, 0):
                bot.send_message(user_id, f"❌ Неверное количество! У вас есть {user.inventory.get(gift, 0)} шт.")
                return
            
            user_states[user_id] = {'action': 'set_price', 'gift': gift, 'quantity': quantity}
            bot.send_message(user_id, f"💵 Установите цену за один {gift} (от $1 до $50):")
            
        except ValueError:
            bot.send_message(user_id, "❌ Введите число!")
    
    elif state.get('action') == 'set_price':
        try:
            price = float(message.text)
            gift = state['gift']
            quantity = state['quantity']
            
            if price < 1 or price > 50:
                bot.send_message(user_id, "❌ Цена должна быть от $1 до $50!")
                return
            
            # Добавляем товар на рынок
            slot_id = add_market_item(user_id, gift, price, quantity)
            
            # Убираем подарки из инвентаря
            user = load_user_data(user_id)
            user.inventory[gift] -= quantity
            if user.inventory[gift] <= 0:
                del user.inventory[gift]
            save_user_data(user_id)
            
            del user_states[user_id]
            
            bot.send_message(user_id, f"✅ Товар добавлен на рынок!\n{gift} x{quantity} по ${price} за шт.\nСлот: {slot_id[:8]}...")
            
        except ValueError:
            bot.send_message(user_id, "❌ Введите число!")

# ========== СУЩЕСТВУЮЩИЕ КОМАНДЫ ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Я работаю только в группах! Добавьте меня в группу.")
    else:
        bot.reply_to(message, "Привет! Я Лакер - бот для общения. Используйте /menu для настроек (только для админов).")

@bot.message_handler(commands=['menu'])
def show_menu(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Я работаю только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    data = load_chat_data(chat_id)
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    talk_status = "✅ ВКЛ" if data.talking_mode else "❌ ВЫКЛ"
    image_status = "✅ ВКЛ" if data.image_generation else "❌ ВЫКЛ"
    
    keyboard.add(telebot.types.InlineKeyboardButton(
        f"Режим разговора {talk_status}", 
        callback_data=f"talk_mode_{chat_id}"
    ))
    keyboard.add(telebot.types.InlineKeyboardButton(
        f"Генерация изображений {image_status}", 
        callback_data=f"image_mode_{chat_id}"
    ))
    
    bot.send_message(
        chat_id, 
        f"⚙️ **Меню настроек (только для админов)**\n\n"
        f"💬 Режим разговора: {talk_status}\n"
        f"🎨 Генерация изображений: {image_status}\n\n"
        f"*Режим разговора* - бот отвечает на сообщения\n"
        f"*Генерация изображений* - позволяет использовать /img",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['setrules'])
def set_rules(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    args = message.text.split(' ', 1)
    if len(args) < 2:
        bot.reply_to(message, "Используйте: /setrules ваши_правила_здесь")
        return
    
    rules_text = args[1]
    data = load_chat_data(chat_id)
    data.rules = rules_text
    save_chat_data(chat_id)
    
    bot.reply_to(message, "✅ Правила успешно установлены!")

@bot.message_handler(commands=['rules'])
def show_rules(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    data = load_chat_data(chat_id)
    
    bot.reply_to(message, f"📜 **Правила чата:**\n\n{data.rules}")

@bot.message_handler(commands=['ping'])
def ping(message):
    start_time = time.time()
    sent_message = bot.reply_to(message, "🏓 Понг!")
    end_time = time.time()
    
    ping_time = round((end_time - start_time) * 1000, 2)
    bot.edit_message_text(
        f"🏓 Понг! Пинг: {ping_time} мс",
        chat_id=message.chat.id,
        message_id=sent_message.message_id
    )

@bot.message_handler(commands=['reset'])
def reset_words(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам!")
        return
    
    data = load_chat_data(chat_id)
    word_count = len(data.words)
    data.words = []
    save_chat_data(chat_id)
    
    bot.reply_to(message, f"✅ Словарь очищен! Удалено {word_count} слов.")

@bot.message_handler(commands=['img'])
def generate_img(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    chat_id = message.chat.id
    data = load_chat_data(chat_id)
    
    if not data.image_generation:
        bot.reply_to(message, "❌ Генерация изображений отключена администратором!")
        return
    
    args = message.text.split(' ', 1)
    if len(args) < 2:
        bot.reply_to(message, "Используйте: /img описание_изображения")
        return
    
    prompt = args[1]
    
    if len(prompt) < 3:
        bot.reply_to(message, "❌ Описание должно содержать минимум 3 символа!")
        return
    
    processing_msg = bot.reply_to(message, "🔄 Генерирую изображение...")
    
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            image_url = loop.run_until_complete(generate_image(prompt))
            loop.close()
            
            if image_url:
                # Добавляем активный подарок к описанию
                user = load_user_data(message.from_user.id)
                caption = f"🎨 Сгенерировано по запросу: {prompt}"
                if user.active_gift:
                    caption = f"{user.active_gift} {caption}"
                
                bot.send_photo(chat_id, image_url, reply_to_message_id=message.message_id, caption=caption)
                bot.delete_message(chat_id, processing_msg.message_id)
            else:
                bot.edit_message_text("❌ Ошибка генерации изображения", 
                                    chat_id=chat_id, 
                                    message_id=processing_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Ошибка: {e}", 
                                chat_id=chat_id, 
                                message_id=processing_msg.message_id)
    
    thread = threading.Thread(target=run_async)
    thread.start()

@bot.message_handler(commands=['report'])
def handle_report(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "Используйте команду /report в ответ на сообщение, которое хотите пожаловаться!")
        return
    
    args = message.text.split(' ', 1)
    if len(args) < 2:
        bot.reply_to(message, "Используйте: /report причина_жалобы")
        return
    
    reason = args[1]
    reported_message = message.reply_to_message
    chat_id = message.chat.id
    
    try:
        admins = bot.get_chat_administrators(chat_id)
        reporter = message.from_user
        
        report_text = (
            f"🚨 **Новая жалоба**\n\n"
            f"👤 От: {reporter.first_name} (@{reporter.username or 'нет'})\n"
            f"💬 Чат: {message.chat.title}\n"
            f"📝 Причина: {reason}\n"
            f"🕒 Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"📄 Сообщение: {reported_message.text or 'медиа-сообщение'}"
        )
        
        sent_count = 0
        for admin in admins:
            if not admin.user.is_bot:
                try:
                    bot.send_message(admin.user.id, report_text, parse_mode='Markdown')
                    sent_count += 1
                except:
                    pass
        
        bot.reply_to(message, f"✅ Жалоба отправлена {sent_count} администраторам!")
        
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при отправке жалобы")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if message.chat.type == 'private':
        return
    
    chat_id = message.chat.id
    
    if message.document.mime_type == 'text/plain' or message.document.file_name.endswith('.txt'):
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            words_count = process_txt_file(downloaded_file, chat_id)
            
            bot.reply_to(message, f"✅ Файл успешно обработан! Добавлено {words_count} слов в базу данных.")
            
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка при обработке файла: {e}")
    else:
        bot.reply_to(message, "❌ Пожалуйста, отправьте txt файл.")

@bot.message_handler(content_types=['text'])
def handle_message(message):
    if message.chat.type == 'private':
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if is_muted(chat_id, user_id):
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        return
    
    load_user_data(user_id, message.from_user.username, message.from_user.first_name)
    
    data = load_chat_data(chat_id)
    words = extract_words(message.text)
    data.words.extend(words)
    data.words = list(set(data.words))
    save_chat_data(chat_id)
    
    if random.random() < 0.4:
        try:
            reaction = random.choice(REACTIONS)
            bot.set_message_reaction(chat_id, message.message_id, [telebot.types.ReactionType(reaction)])
        except:
            pass
    
    if data.talking_mode:
        if random.random() < 0.3:
            response = get_random_response(chat_id)
            try:
                # Добавляем активный подарок к ответу
                user = load_user_data(message.from_user.id)
                if user.active_gift:
                    response = f"{user.active_gift} {response}"
                bot.reply_to(message, response)
            except:
                pass
        else:
            response = get_random_response(chat_id)
            try:
                user = load_user_data(message.from_user.id)
                if user.active_gift:
                    response = f"{user.active_gift} {response}"
                bot.reply_to(message, response)
            except:
                pass

@bot.callback_query_handler(func=lambda call: call.data.startswith(('talk_mode_', 'image_mode_')))
def handle_settings_callback(call):
    if call.data.startswith('talk_mode_'):
        chat_id = int(call.data.split('_')[-1])
        
        if not is_admin(chat_id, call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Только администраторы могут изменять настройки!")
            return
        
        data = load_chat_data(chat_id)
        data.talking_mode = not data.talking_mode
        status = "включен" if data.talking_mode else "выключен"
        bot.answer_callback_query(call.id, f"Режим разговора {status}")
        save_chat_data(chat_id)
        show_menu(call.message)
    
    elif call.data.startswith('image_mode_'):
        chat_id = int(call.data.split('_')[-1])
        
        if not is_admin(chat_id, call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Только администраторы могут изменять настройки!")
            return
        
        data = load_chat_data(chat_id)
        data.image_generation = not data.image_generation
        status = "включена" if data.image_generation else "выключена"
        bot.answer_callback_query(call.id, f"Генерация изображений {status}")
        save_chat_data(chat_id)
        show_menu(call.message)

if __name__ == "__main__":
    print("Бот Лакер запущен!")
    print(f"Загружено подарков: {len(GIFTS)}")
    print("Подарки:", ", ".join(GIFTS))
    print("Создайте файл gifts.txt с подарками через запятую для кастомного списка")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(10)
