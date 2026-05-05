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

# --- Key Generation Data (Temporary storage for process) ---
user_process = {}

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

# --- Generate Key Process (Steps like screenshot) ---

@bot.message_handler(func=lambda message: message.text == "Generate Key 🔑")
def step1_select_time(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    # Permission Check
    if int(user_id) != ADMIN_ID and user_id not in db["resellers"]: return

    markup = types.InlineKeyboardMarkup(row_width=2)
    times = {
        "1 Hour": 0.04, "1 Day": 1, "7 Days": 7, "15 Days": 15,
        "1 Month": 30, "2 Months": 60, "3 Months": 90, "1 Year": 365
    }
    btns = [types.InlineKeyboardButton(text=t, callback_data=f"time_{d}") for t, d in times.items()]
    markup.add(*btns)
    
    bot.send_message(message.chat.id, "Select Expiration Time:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def step2_get_time(call):
    days = float(call.data.split("_")[1])
    user_process[call.from_user.id] = {"days": days}
    
    msg = bot.edit_message_text("Enter the Client App ID:", chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.register_next_step_handler(msg, step3_final_generate)

def step3_final_generate(message):
    user_id = str(message.from_user.id)
    client_app_id = message.text.strip()
    db = load_db()
    
    if message.from_user.id not in user_process:
        bot.send_message(message.chat.id, "❌ Session expired. Please try again.")
        return

    days = user_process[message.from_user.id]["days"]

    # Point Check for Reseller
    if int(user_id) != ADMIN_ID:
        if db["resellers"][user_id]["points"] <= 0:
            bot.send_message(message.chat.id, "❌ Point မလောက်တော့ပါ။")
            return
        db["resellers"][user_id]["points"] -= 1

    # Create Key like Screenshot: u0_a30610306@...
    date_str = datetime.now().strftime("%d-%m-%Y")
    new_key = f"{client_app_id}@{date_str}"
    
    db["generated_keys"][new_key] = days
    save_db(db)
    
    bot.send_message(message.chat.id, f"✅ **Key Generated & Saved:**\n`{new_key}`", parse_mode="Markdown")
    del user_process[message.from_user.id]

# --- Key Activation & Admin Commands ---

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    db = load_db()

    # Admin: Add Reseller (/add ID Points)
    if text.startswith("/add") and int(user_id) == ADMIN_ID:
        try:
            _, t_id, pts = text.split()
            db["resellers"][t_id] = {"points": int(pts)}
            save_db(db)
            bot.send_message(message.chat.id, f"✅ Added Reseller {t_id} with {pts} points.")
        except: pass
        return

    # User: Activate Key
    if text in db["generated_keys"]:
        days = db["generated_keys"][text]
        now = datetime.now()
        
        # Calculate Expiry
        if user_id in db["users"]:
            try:
                current = datetime.strptime(db["users"][user_id], "%Y-%m-%d")
                start_date = max(now, current)
            except: start_date = now
        else:
            start_date = now
            
        expiry_date = start_date + timedelta(days=days)
        db["users"][user_id] = expiry_date.strftime("%Y-%m-%d")
        
        del db["generated_keys"][text] # Delete used key
        save_db(db)
        
        bot.send_message(message.chat.id, f"✅ **Activation Success!**\nNew Expiry: `{db['users'][user_id]}`", parse_mode="Markdown")
    
    elif text == "Check Points 💰" and user_id in db["resellers"]:
        bot.send_message(message.chat.id, f"💰 My Points: `{db['resellers'][user_id]['points']}`", parse_mode="Markdown")

# Run
print("Bot Started...")
bot.infinity_polling()
