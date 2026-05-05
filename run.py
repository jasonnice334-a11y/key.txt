import telebot
from telebot import types
import json
import os
import random
import string
from datetime import datetime, timedelta

# --- Configurations ---
API_TOKEN = '8592959813:AAEDsofdrjOQvcmqYAE12nWMLOq2RziSdu0'
ADMIN_ID = 8253065182
ADMIN_NAME = "MYO MYINT AUNG"
DB_FILE = 'database.json'

bot = telebot.TeleBot(API_TOKEN)

# --- Database Functions ---
def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = {
            "resellers": {}, 
            "generated_keys": {}, # {"KEY123": "30_days"}
            "users": {} # {"USER_ID": "expiry_date"}
        }
        with open(DB_FILE, 'w') as f:
            json.dump(initial_data, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Helper Functions ---
def generate_random_key(length=10):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

# --- Handlers ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if int(user_id) == ADMIN_ID:
        btn1 = types.KeyboardButton("Generate Key 🔑")
        btn2 = types.KeyboardButton("Reseller List 📋")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"🌟 **Admin Dashboard**\nAdmin: {ADMIN_NAME}", reply_markup=markup)
        
    elif user_id in db["resellers"]:
        points = db["resellers"][user_id]["points"]
        btn1 = types.KeyboardButton("Generate Key 🔑")
        btn2 = types.KeyboardButton("Check Points 💰")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"👋 **Reseller Panel**\nPoints: {points}", reply_markup=markup)
        
    else:
        # သာမန် User အတွက် Status ပြမယ်
        expiry = db["users"].get(user_id, "No Active Plan")
        bot.send_message(message.chat.id, f"👤 **User Profile**\nExpiry: `{expiry}`\n\nKey ရှိပါက ရိုက်ထည့်၍ Activate လုပ်နိုင်ပါသည်။", parse_mode="Markdown")

# --- Reseller & Key Logic ---

@bot.message_handler(func=lambda message: message.text == "Generate Key 🔑")
def handle_gen_key(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    # Permission Check
    if int(user_id) != ADMIN_ID and user_id not in db["resellers"]:
        return

    # Reseller Point Check
    if int(user_id) != ADMIN_ID:
        if db["resellers"][user_id]["points"] <= 0:
            bot.send_message(message.chat.id, "❌ Point မလောက်တော့ပါ။")
            return
        db["resellers"][user_id]["points"] -= 1

    # Key တစ်ခုထုတ်မယ် (ဥပမာ ၃၀ ရက်စာ)
    new_key = f"VIP-{generate_random_key()}"
    db["generated_keys"][new_key] = 30 # 30 days
    save_db(db)
    
    bot.send_message(message.chat.id, f"✅ **New Key Generated!**\n\n`{new_key}`\n(Duration: 30 Days)", parse_mode="Markdown")

# --- Key Activation Logic (User ဘက်ခြမ်း) ---

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    input_text = message.text.strip()
    db = load_db()

    # Admin အတွက် Point ထည့်တဲ့ command
    if input_text.startswith("/add") and int(user_id) == ADMIN_ID:
        try:
            _, t_id, pts = input_text.split()
            db["resellers"][t_id] = {"points": int(pts)}
            save_db(db)
            bot.send_message(message.chat.id, f"✅ ID {t_id} ထံ Point {pts} ထည့်ပြီးပါပြီ။")
            return
        except: pass

    # User က Key လာရိုက်တဲ့အခါ စစ်ဆေးပေးမယ့်အပိုင်း
    if input_text in db["generated_keys"]:
        days = db["generated_keys"][input_text]
        
        # သက်တမ်းတွက်ချက်ခြင်း
        now = datetime.now()
        if user_id in db["users"]:
            # အဟောင်းရှိရင် အဟောင်းပေါ်ထပ်ပေါင်းမယ်
            try:
                current_expiry = datetime.strptime(db["users"][user_id], "%Y-%m-%d")
                new_expiry = max(now, current_expiry) + timedelta(days=days)
            except:
                new_expiry = now + timedelta(days=days)
        else:
            new_expiry = now + timedelta(days=days)

        db["users"][user_id] = new_expiry.strftime("%Y-%m-%d")
        
        # သုံးပြီးသား Key ကို ဖျက်မယ်
        del db["generated_keys"][input_text]
        save_db(db)
        
        bot.send_message(message.chat.id, f"🎉 **Success!**\nသင်၏ VIP သက်တမ်းကို {days} ရက် တိုးမြှင့်လိုက်ပါပြီ။\nExpiry Date: `{db['users'][user_id]}`", parse_mode="Markdown")
    
    elif message.text == "Check Points 💰":
        if user_id in db["resellers"]:
            bot.send_message(message.chat.id, f"💰 လက်ကျန် Point: {db['resellers'][user_id]['points']}")

# Bot Start
print("Bot is running...")
bot.infinity_polling()
