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

# --- Database Functions ---
def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = {"resellers": {}, "generated_keys": {}, "users": {}}
        with open(DB_FILE, 'w') as f:
            json.dump(initial_data, f)
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {"resellers": {}, "generated_keys": {}, "users": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ID စစ်ဆေးသည့် Command ---
@bot.message_handler(commands=['id'])
def get_my_id(message):
    bot.reply_to(message, f"🆔 သင့်ရဲ့ Telegram ID ကတော့: `{message.from_user.id}` ဖြစ်ပါတယ်ဗျ။", parse_mode="Markdown")

# --- Start Handler ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    db = load_db()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if int(user_id) == ADMIN_ID:
        btn1 = types.KeyboardButton("Key ထုတ်မည် 🔑")
        btn2 = types.KeyboardButton("Reseller စာရင်း 📋")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"🌟 **Admin Dashboard**\nစီမံခန့်ခွဲသူ: `{ADMIN_NAME}`", reply_markup=markup, parse_mode="Markdown")
    elif user_id in db["resellers"]:
        points = db["resellers"][user_id]["points"]
        btn1 = types.KeyboardButton("Key ထုတ်မည် 🔑")
        btn2 = types.KeyboardButton("Point စစ်မည် 💰")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"👋 **Reseller Panel**\nလက်ရှိ Point: `{points}` ခု", reply_markup=markup, parse_mode="Markdown")
    else:
        expiry = db["users"].get(user_id, "သက်တမ်းမရှိသေးပါ")
        bot.send_message(message.chat.id, f"👤 **User Status**\nသက်တမ်းကုန်ဆုံးရက်: `{expiry}`\n\nKey ရှိပါက ရိုက်ထည့်ပြီး Activate ပြုလုပ်နိုင်ပါသည်။", parse_mode="Markdown")

# --- Admin Command: Add Reseller ---
@bot.message_handler(commands=['add'])
def add_reseller(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        pts = int(args[2])
        db = load_db()
        if target_id in db["resellers"]:
            db["resellers"][target_id]["points"] += pts
        else:
            db["resellers"][target_id] = {"points": pts}
        save_db(db)
        bot.send_message(message.chat.id, f"✅ ID `{target_id}` ကို Point `{pts}` ခု ထည့်သွင်းပြီးပါပြီ။")
    except:
        bot.send_message(message.chat.id, "💡 အသုံးပြုပုံ: `/add [ID] [Points]`")

# --- Generate Key Steps ---
@bot.message_handler(func=lambda m: m.text == "Key ထုတ်မည် 🔑")
def ask_time(message):
    user_id = str(message.from_user.id)
    db = load_db()
    if int(user_id) != ADMIN_ID and user_id not in db["resellers"]: return

    markup = types.InlineKeyboardMarkup(row_width=2)
    times = {"၁ နာရီ": 0.04, "၁ ရက်": 1, "၇ ရက်": 7, "၁၅ ရက်": 15, "၁ လ": 30, "၁ နှစ်": 365}
    btns = [types.InlineKeyboardButton(text=t, callback_data=f"time_{d}") for t, d in times.items()]
    markup.add(*btns)
    bot.send_message(message.chat.id, "သက်တမ်းရွေးချယ်ပါ (Expiration Time):", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("time_"))
def ask_id(call):
    days = float(call.data.split("_")[1])
    user_process[call.from_user.id] = {"days": days}
    msg = bot.edit_message_text("Client ၏ App ID ကို ရိုက်ထည့်ပါ:", chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.register_next_step_handler(msg, final_gen)

def final_gen(message):
    user_id = str(message.from_user.id)
    app_id = message.text.strip()
    db = load_db()
    
    if int(user_id) != ADMIN_ID:
        if db["resellers"][user_id]["points"] <= 0:
            bot.send_message(message.chat.id, "❌ သင့်တွင် Point မလောက်တော့ပါ။ Admin ဆီတွင် ဖြည့်သွင်းပါ။")
            return
        db["resellers"][user_id]["points"] -= 1

    # Format: AppID@Date
    new_key = f"{app_id}@{datetime.now().strftime('%d-%m-%Y')}"
    db["generated_keys"][new_key] = user_process[message.from_user.id]["days"]
    save_db(db)
    
    bot.send_message(message.chat.id, f"✅ **Key ထုတ်ပြီးပါပြီ:**\n`{new_key}`", parse_mode="Markdown")
    if int(user_id) != ADMIN_ID:
        bot.send_message(message.chat.id, f"📉 လက်ကျန် Point: `{db['resellers'][user_id]['points']}` ခု")

# --- Activation & Logic ---
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    db = load_db()

    # Key Activate လုပ်ခြင်း
    if text in db["generated_keys"]:
        days = db["generated_keys"][text]
        now = datetime.now()
        
        # သက်တမ်းတွက်ချက်ခြင်း
        if user_id in db["users"]:
            try:
                current_expiry = datetime.strptime(db["users"][user_id], "%Y-%m-%d")
                start_date = max(now, current_expiry)
            except: start_date = now
        else:
            start_date = now
            
        expiry_date = start_date + timedelta(days=days)
        db["users"][user_id] = expiry_date.strftime("%Y-%m-%d")
        
        del db["generated_keys"][text] # Key ကို ဖျက်မည်
        save_db(db)
        
        bot.send_message(message.chat.id, f"🎉 **အောင်မြင်ပါသည်!**\nသက်တမ်းတိုးပြီးရက်: `{db['users'][user_id]}` ထိဖြစ်ပါတယ်ဗျ။", parse_mode="Markdown")
    
    elif text == "Point စစ်မည် 💰" and user_id in db["resellers"]:
        bot.send_message(message.chat.id, f"💰 သင့်လက်ကျန် Point: `{db['resellers'][user_id]['points']}` ခု")
    
    elif text == "Reseller စာရင်း 📋" and int(user_id) == ADMIN_ID:
        msg = "👥 **Reseller စာရင်းနှင့် Point များ:**\n\n"
        for rid, data in db["resellers"].items():
            msg += f"ID: `{rid}` | Points: `{data['points']}`\n"
        bot.send_message(message.chat.id, msg if len(db["resellers"]) > 0 else "Reseller မရှိသေးပါ။", parse_mode="Markdown")

bot.infinity_polling()
