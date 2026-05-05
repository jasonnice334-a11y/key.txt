import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta

# --- Configurations ---
API_TOKEN = '8592959813:AAEDsofdrjOQvcmqYAE12nWMLOq2RziSdu0'
ADMIN_ID = 8253065182
ADMIN_NAME = "MYO MYINT AUNG"
DB_FILE = 'database.json'

bot = telebot.TeleBot(API_TOKEN)
user_process = {}

def load_db():
    if not os.path.exists(DB_FILE):
        initial = {"resellers": {}, "generated_keys": {}, "users": {}}
        with open(DB_FILE, 'w') as f: json.dump(initial, f)
    with open(DB_FILE, 'r') as f:
        try: return json.load(f)
        except: return {"resellers": {}, "generated_keys": {}, "users": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- ID စစ်ဆေးရန် ---
@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"🆔 သင့်ရဲ့ Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

# --- Start Handler ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    db = load_db()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if int(user_id) == ADMIN_ID:
        btn1, btn2 = types.KeyboardButton("Key ထုတ်မည် 🔑"), types.KeyboardButton("Reseller စာရင်း 📋")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"🌟 **Admin Dashboard**\nAdmin: `{ADMIN_NAME}`", reply_markup=markup, parse_mode="Markdown")
    elif user_id in db["resellers"]:
        points = db["resellers"][user_id]["points"]
        btn1, btn2 = types.KeyboardButton("Key ထုတ်မည် 🔑"), types.KeyboardButton("Point စစ်မည် 💰")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"👋 **Reseller Panel**\nလက်ရှိ Point: `{points}`", reply_markup=markup, parse_mode="Markdown")
    else:
        expiry = db["users"].get(user_id, "သက်တမ်းမရှိသေးပါ")
        bot.send_message(message.chat.id, f"👤 **User Status**\nသက်တမ်းကုန်ရက်: `{expiry}`\n\nKey ရှိပါက ရိုက်ထည့်၍ Activate လုပ်နိုင်ပါသည်။", parse_mode="Markdown")

# --- Admin: Add Reseller (/add ID Point) ---
@bot.message_handler(commands=['add'])
def add_res(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        db = load_db()
        db["resellers"][args[1]] = {"points": int(args[2])}
        save_db(db)
        bot.send_message(message.chat.id, f"✅ ID `{args[1]}` ကို Point `{args[2]}` ထည့်ပြီးပါပြီ။")
    except: bot.send_message(message.chat.id, "💡 Format: `/add [ID] [Points]`")

# --- Key Generation Flow ---
@bot.message_handler(func=lambda m: m.text == "Key ထုတ်မည် 🔑")
def ask_time(message):
    user_id = str(message.from_user.id)
    db = load_db()
    if int(user_id) != ADMIN_ID and user_id not in db["resellers"]: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    times = {"၁ နာရီ": 0.04, "၁ ရက်": 1, "၇ ရက်": 7, "၁ လ": 30, "၁ နှစ်": 365}
    btns = [types.InlineKeyboardButton(text=t, callback_data=f"t_{d}") for t, d in times.items()]
    markup.add(*btns)
    bot.send_message(message.chat.id, "သက်တမ်းရွေးချယ်ပါ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("t_"))
def ask_appid(call):
    user_process[call.from_user.id] = {"days": float(call.data.split("_")[1])}
    msg = bot.edit_message_text("Client ရဲ့ App ID ကို ရိုက်ထည့်ပါ:", chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.register_next_step_handler(msg, finalize)

def finalize(message):
    user_id = str(message.from_user.id)
    app_id = message.text.strip()
    db = load_db()
    
    if int(user_id) != ADMIN_ID:
        if db["resellers"][user_id]["points"] <= 0:
            bot.send_message(message.chat.id, "❌ Point မလောက်တော့ပါ။"); return
        db["resellers"][user_id]["points"] -= 1

    new_key = f"{app_id}@{datetime.now().strftime('%d-%m-%Y')}"
    db["generated_keys"][new_key] = user_process[message.from_user.id]["days"]
    save_db(db)
    bot.send_message(message.chat.id, f"✅ **Key ထွက်လာပါပြီ:**\n`{new_key}`", parse_mode="Markdown")

# --- Handle Keys & Points ---
@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    uid, text, db = str(message.from_user.id), message.text.strip(), load_db()
    if text in db["generated_keys"]:
        days = db["generated_keys"][text]
        now = datetime.now()
        start = max(now, datetime.strptime(db["users"].get(uid, now.strftime("%Y-%m-%d")), "%Y-%m-%d")) if uid in db["users"] else now
        expiry = start + timedelta(days=days)
        db["users"][uid] = expiry.strftime("%Y-%m-%d")
        del db["generated_keys"][text]
        save_db(db)
        bot.send_message(message.chat.id, f"🎉 **Activate အောင်မြင်သည်!**\nExpiry: `{db['users'][uid]}`", parse_mode="Markdown")
    elif text == "Point စစ်မည် 💰" and uid in db["resellers"]:
        bot.send_message(message.chat.id, f"💰 လက်ကျန် Point: `{db['resellers'][uid]['points']}`")
    elif text == "Reseller စာရင်း 📋" and int(uid) == ADMIN_ID:
        res_list = "\n".join([f"ID: `{i}` | Pts: `{d['points']}`" for i, d in db["resellers"].items()])
        bot.send_message(message.chat.id, f"👥 **Resellers:**\n{res_list or 'မရှိသေးပါ'}", parse_mode="Markdown")

bot.infinity_polling()
