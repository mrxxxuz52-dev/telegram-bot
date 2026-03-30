import telebot
from telethon import TelegramClient
from telethon.errors import FloodWaitError
import asyncio
import random
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ====== SOZLAMALAR ======
BOT_TOKEN = "8643375837:AAEfyRbRGpNoS7Pe9VO5wzIiG7TYA5dHZ00"
api_id = 30330798
api_hash = "972404e0bbe1d7f5f92ff7b6cb70bb43"
ADMIN_ID = 8005527610

# ====== GLOBAL LOOP ======
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ====== INIT ======
bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient("session", api_id, api_hash, loop=loop)

client.start()

# ====== GLOBAL ======
message_text = "Salom 🚀"
interval = 60
running = False
sending_task = None
selected_groups = []
all_groups_cache = []

# ====== MENU ======
def menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📨 Xabar sozlash")
    markup.add("⏱ Interval sozlash")
    markup.add("📌 Guruh tanlash")
    markup.add("▶️ Boshlash", "⏹ To‘xtatish")
    bot.send_message(chat_id, "Menu:", reply_markup=markup)

# ====== START ======
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != ADMIN_ID:
        return
    menu(message.chat.id)

# ====== XABAR ======
@bot.message_handler(func=lambda m: m.text == "📨 Xabar sozlash")
def set_msg(message):
    bot.send_message(message.chat.id, "Yangi xabar yoz:")
    bot.register_next_step_handler(message, save_msg)

def save_msg(message):
    global message_text
    message_text = message.text
    bot.send_message(message.chat.id, "Saqlandi ✅")

# ====== INTERVAL ======
@bot.message_handler(func=lambda m: m.text == "⏱ Interval sozlash")
def set_interval(message):
    bot.send_message(message.chat.id, "Sekund yoz (masalan 60):")
    bot.register_next_step_handler(message, save_interval)

def save_interval(message):
    global interval
    try:
        interval = int(message.text)
        bot.send_message(message.chat.id, f"Interval: {interval} sek ✅")
    except:
        bot.send_message(message.chat.id, "Xato! Raqam yoz ❗")

# ====== GURUH TANLASH ======
@bot.message_handler(func=lambda m: m.text == "📌 Guruh tanlash")
def show_groups(message):
    if message.chat.id != ADMIN_ID:
        return

    async def get_groups():
        dialogs = await client.get_dialogs()
        return [d for d in dialogs if d.is_group]

    global all_groups_cache

    future = asyncio.run_coroutine_threadsafe(get_groups(), loop)
    all_groups_cache = future.result()

    send_group_menu(message.chat.id)

def send_group_menu(chat_id):
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton("✅ Hammasini tanlash", callback_data="select_all"),
        InlineKeyboardButton("❌ Hammasini o‘chirish", callback_data="clear_all")
    )

    for g in all_groups_cache:
        gid = g.id
        name = g.name

        if gid in selected_groups:
            text = f"✅ {name}"
        else:
            text = f"❌ {name}"

        markup.add(InlineKeyboardButton(text, callback_data=f"group_{gid}"))

    bot.send_message(chat_id, "Guruhlarni tanla:", reply_markup=markup)

# ====== CALLBACK ======
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    global selected_groups

    if call.data == "select_all":
        selected_groups = [g.id for g in all_groups_cache]
        bot.answer_callback_query(call.id, "Hammasi tanlandi ✅")

    elif call.data == "clear_all":
        selected_groups = []
        bot.answer_callback_query(call.id, "Hammasi o‘chirildi ❌")

    elif call.data.startswith("group_"):
        gid = int(call.data.split("_")[1])

        if gid in selected_groups:
            selected_groups.remove(gid)
            bot.answer_callback_query(call.id, "O‘chirildi ❌")
        else:
            selected_groups.append(gid)
            bot.answer_callback_query(call.id, "Qo‘shildi ✅")

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None
    )

    send_group_menu(call.message.chat.id)

# ====== YUBORISH ======
async def send_messages():
    global selected_groups

    dialogs = await client.get_dialogs()
    working = []

    for dialog in dialogs:
        if dialog.is_group and dialog.id in selected_groups:
            try:
                await client.send_message(dialog.entity, message_text)
                print(f"Yuborildi: {dialog.name}")
                working.append(dialog.id)

                await asyncio.sleep(random.randint(5, 10))

            except FloodWaitError as e:
                print(f"Flood: {e.seconds}")
                await asyncio.sleep(e.seconds)

            except Exception as e:
                print(f"Xato: {dialog.name} | {e}")

    selected_groups = working

# ====== LOOP ======
async def sender_loop():
    global running
    while running:
        await send_messages()
        await asyncio.sleep(interval)

# ====== BOSHLASH ======
@bot.message_handler(func=lambda m: m.text == "▶️ Boshlash")
def start_send(message):
    global running, sending_task

    if message.chat.id != ADMIN_ID:
        return

    if not running:
        running = True
        sending_task = loop.create_task(sender_loop())
        bot.send_message(message.chat.id, "Boshladi 🚀")
    else:
        bot.send_message(message.chat.id, "Allaqachon ishlayapti ⚠️")

# ====== STOP ======
@bot.message_handler(func=lambda m: m.text == "⏹ To‘xtatish")
def stop_send(message):
    global running, sending_task

    running = False

    if sending_task:
        sending_task.cancel()

    bot.send_message(message.chat.id, "To‘xtadi ⛔")

# ====== RUN ======
def start_bot():
    bot.infinity_polling()

threading.Thread(target=start_bot).start()

print("Bot ishga tushdi 🚀")
loop.run_forever()