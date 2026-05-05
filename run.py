import telebot
from telebot import types
import json
import os
import random
import string
from datetime import datetime

# --- Configurations ---
API_TOKEN = '8592959813:AAEDsofdrjOQvcmqYAE12nWMLOq2RziSdu0'
ADMIN_ID = 8253065182
ADMIN_NAME = "MYO MYINT AUNG"
DB_FILE = 'resellers.json'

bot = telebot.TeleBot(API_TOKEN)

# --- Database Functions ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"resellers": {}, "generated_keys": []}, f)
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {"resellers": {}, "generated_keys": []}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Helper Functions ---
def generate_random_key(length=12):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# --- Handlers ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    db = load_db()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if user_id == ADMIN_ID:
        btn1 = types.KeyboardButton("Generate Key 🔑")
        btn2 = types.KeyboardButton("Reseller List 📋")
        btn3 = types.KeyboardButton("Add Reseller ➕")
        btn4 = types.KeyboardButton("Key History 📜")
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id, f"🌟 **Admin Dashboard**\nAdmin: `{ADMIN_NAME}`\n\nReseller ခန့်ရန် သို့မဟုတ် Point ထည့်ရန် `/add [ID] [Points]` ကိုသုံးပါ။", reply_markup=markup, parse_mode="Markdown")
        
    elif str(user_id) in db["resellers"]:
        points = db["resellers"][str(user_id)]["points"]
        btn1 = types.KeyboardButton("Generate Key 🔑")
        btn2 = types.KeyboardButton("My Balance 💰")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"👋 **Reseller Panel**\nလက်ရှိ Point: `{points}`", reply_markup=markup, parse_mode="Markdown")
        
    else:
        bot.send_message(message.chat.id, f"❌ သင်သည် အသုံးပြုခွင့်မရှိပါ။\nKey ဝယ်ယူရန် Admin **{ADMIN_NAME}** ကို ဆက်သွယ်ပါ။", parse_mode="Markdown")

# --- Admin Commands ---

@bot.message_handler(commands=['add'])
def add_reseller_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        new_points = int(args[2])
        
        db = load_db()
        if target_id in db["resellers"]:
            db["resellers"][target_id]["points"] += new_points
        else:
            db["resellers"][target_id] = {"points": new_points}
        
        save_db(db)
        bot.send_message(message.chat.id, f"✅ ID: `{target_id}` ထံသို့ Point `{new_points}` ထည့်သွင်းပြီးပါပြီ။", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "💡 အသုံးပြုပုံ: `/add [ID] [Points]`")

# --- Button Logic ---

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    db = load_db()

    if message.text == "Generate Key 🔑":
        is_admin = (user_id == ADMIN_ID)
        is_res = (str(user_id) in db["resellers"])
        
        if not (is_admin or is_res): return

        if is_res and not is_admin:
            if db["resellers"][str(user_id)]["points"] <= 0:
                bot.send_message(message.chat.id, "❌ သင့်တွင် Point မလောက်တော့ပါ။")
                return
            db["resellers"][str(user_id)]["points"] -= 1
        
        key = f"PREMIUM-{generate_random_key()}"
        db["generated_keys"].append({
            "key": key,
            "by": user_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        save_db(db)
        
        bot.send_message(message.chat.id, f"✅ **Key Generated!**\n\n`{key}`", parse_mode="Markdown")
        if is_res and not is_admin:
            bot.send_message(message.chat.id, f"📉 လက်ကျန် Point: `{db['resellers'][str(user_id)]['points']}`", parse_mode="Markdown")

    elif message.text == "My Balance 💰":
        if str(user_id) in db["resellers"]:
            pts = db["resellers"][str(user_id)]["points"]
            bot.send_message(message.chat.id, f"💰 သင့်လက်ကျန် Point: `{pts}`", parse_mode="Markdown")

    elif message.text == "Reseller List 📋" and user_id == ADMIN_ID:
        if not db["resellers"]:
            bot.send_message(message.chat.id, "သတ်မှတ်ထားသော Reseller မရှိသေးပါ။")
            return
        msg = "👥 **Current Resellers:**\n\n"
        for rid, data in db["resellers"].items():
            msg += f"• ID: `{rid}` | Points: `{data['points']}`\n"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

    elif message.text == "Key History 📜" and user_id == ADMIN_ID:
        keys = db["generated_keys"][-10:]
        if not keys:
            bot.send_message(message.chat.id, "ထုတ်ထားသော Key မရှိသေးပါ။")
            return
        msg = "📜 **Recent History:**\n\n"
        for k in keys:
            msg += f"🔑 `{k['key']}`\nBY: `{k['by']}` | {k['date']}\n\n"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# Run Bot
print(f"--- Bot Active (Admin: {ADMIN_NAME}) ---")
bot.infinity_polling()
