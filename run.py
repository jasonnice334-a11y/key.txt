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

# --- Database Functions ---
def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = {"resellers": {}, "generated_keys": {}, "users": {}}
        with open(DB_FILE, 'w') as f:
            json.dump(initial_data, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ID စစ်ဆေးသည့် Command ---
@bot.message_handler(commands=['id'])
def get_my_id(message):
    bot.reply_to(message, f"သင့်ရဲ့ Telegram ID ကတော့: `{message.from_user.id}` ဖြစ်ပါတယ်ဗျ။", parse_mode="Markdown")

# --- အရင်က ပေးထားတဲ့ Start နှင့် Logic များ အောက်တွင် ဆက်လက်တည်ရှိမည် ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    db = load_db()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if int(user_id) == ADMIN_ID:
        btn1 = types.KeyboardButton("Generate Key 🔑")
        btn2 = types.KeyboardButton("Reseller List 📋")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"🌟 **Admin Panel is Online!**\nAdmin: `{ADMIN_NAME}`", reply_markup=markup, parse_mode="Markdown")
    elif user_id in db["resellers"]:
        points = db["resellers"][user_id]["points"]
        btn1 = types.KeyboardButton("Generate Key 🔑")
        btn2 = types.KeyboardButton("Check Points 💰")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f"👋 **Reseller Panel is Online!**\nPoints: `{points}`", reply_markup=markup, parse_mode="Markdown")
    else:
        expiry = db["users"].get(user_id, "No Active Plan")
        bot.send_message(message.chat.id, f"👤 **User Status**\nExpiry: `{expiry}`\n\nKey ရှိပါက ရိုက်ထည့်၍ Activate လုပ်နိုင်ပါသည်။", parse_mode="Markdown")

# (ကျန်ရှိသော Logic များ - Generate Key နှင့် Key Activation အပိုင်းများ ထပ်ထည့်ရန်...)
# အဆင်ပြေစေရန် အပေါ်က code ထဲမှာ logic အစုံ ထည့်ပေးထားပြီးသား ဖြစ်ရပါမည်။

bot.infinity_polling()
