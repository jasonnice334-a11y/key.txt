import telebot
from telebot import types
import json
import base64
import requests
import os
from datetime import datetime, timedelta

# --- GitHub Configurations ---
GITHUB_TOKEN = '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'
GITHUB_REPO = 'jasonnice334-a11y/key.txt'
DB_PATH = 'database.json'
KEY_LOG_PATH = 'key.txt'

# --- Bot Configurations ---
API_TOKEN = '8592959813:AAEDsofdrjOQvcmqYAE12nWMLOq2RziSdu0'
ADMIN_ID = 8253065182
ADMIN_NAME = "MYO MYINT AUNG"

bot = telebot.TeleBot(API_TOKEN)
user_process = {}

# --- GitHub Helper Functions ---
def get_github_file(path):
    """GitHub ပေါ်က ဖိုင်ကို ဖတ်ရန်"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return content, r.json()['sha']
    return None, None

def update_github_file(path, content, message="Update file"):
    """GitHub ပေါ်က ဖိုင်ကို အသစ်ပြန်ရေးရန်"""
    _, sha = get_github_file(path)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {
        "message": message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
    }
    if sha:
        data["sha"] = sha
    requests.put(url, json=data, headers=headers)

# --- Database Management ---
def load_db():
    content, _ = get_github_file(DB_PATH)
    if content:
        try:
            return json.loads(content)
        except:
            pass
    return {"resellers": {}, "generated_keys": {}, "users": {}}

def save_db(data):
    update_github_file(DB_PATH, json.dumps(data, indent=4), "Update Database")

# --- Start Handler ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    db = load_db()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if int(uid) == ADMIN_ID:
        markup.add("Key ထုတ်မည် 🔑", "Reseller စာရင်း 📋", "Key စာရင်း 📋")
        bot.send_message(message.chat.id, f"🌟 Admin Panel (GitHub Live)\nAdmin: {ADMIN_NAME}", reply_markup=markup)
    elif uid in db["resellers"]:
        markup.add("Key ထုတ်မည် 🔑", "Point စစ်မည် 💰")
        bot.send_message(message.chat.id, f"👋 Reseller Panel\nလက်ကျန် Point: {db['resellers'][uid]['points']}", reply_markup=markup)
    else:
        expiry = db["users"].get(uid, "သက်တမ်းမရှိသေးပါ")
        bot.send_message(message.chat.id, f"👤 User Status\nသက်တမ်းကုန်ရက်: {expiry}\n\nKey ကို ရိုက်ထည့်၍ Activate လုပ်နိုင်ပါသည်။")

# --- Generate Key Steps ---
@bot.message_handler(func=lambda m: m.text == "Key ထုတ်မည် 🔑")
def ask_time(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    times = {"၁ နာရီ": 0.04, "၁ ရက်": 1, "၇ ရက်": 7, "၁၅ ရက်": 15, "၁ လ": 30, "၁ နှစ်": 365}
    btns = [types.InlineKeyboardButton(text=t, callback_data=f"time_{d}") for t, d in times.items()]
    markup.add(*btns)
    bot.send_message(message.chat.id, "Select Expiration Time:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("time_"))
def ask_appid(call):
    user_process[call.from_user.id] = {"days": float(call.data.split("_")[1])}
    msg = bot.send_message(call.message.chat.id, "Enter the Client App ID:")
    bot.register_next_step_handler(msg, finalize_gen)

def finalize_gen(message):
    uid = str(message.from_user.id)
    appID = message.text.strip()
    db = load_db()

    # App ID ကနေ Real UID ထုတ်ယူခြင်း
    try:
        real_uid = base64.b16decode(appID[2:-3]).decode()
    except:
        bot.send_message(message.chat.id, "❌ App ID မှားယွင်းနေပါသည်။")
        return

    # Reseller ဖြစ်ပါက Point နှုတ်ခြင်း
    if int(uid) != ADMIN_ID:
        if db["resellers"].get(uid, {}).get("points", 0) <= 0:
            bot.send_message(message.chat.id, "❌ Point မလောက်တော့ပါ။")
            return
        db["resellers"][uid]["points"] -= 1

    # Key ဖန်တီးခြင်း
    expire_str = (datetime.now() + timedelta(days=user_process[message.from_user.id]["days"])).strftime("%M-%H-%d-%m-%Y")
    new_key = f"{real_uid}@{expire_str}"
    
    db["generated_keys"][new_key] = user_process[message.from_user.id]["days"]
    save_db(db)

    # --- GitHub ထဲက key.txt ကို JSON format ဖြင့် Update လုပ်ခြင်း ---
    old_content, _ = get_github_file(KEY_LOG_PATH)
    try:
        data = json.loads(old_content) if old_content else {"clients": []}
        if "clients" not in data:
            data["clients"] = []
        if new_key not in data["clients"]:
            data["clients"].append(new_key)
    except Exception as e:
        data = {"clients": [new_key]}

    updated_json = json.dumps(data, indent=4)
    update_github_file(KEY_LOG_PATH, updated_json, f"New Key Added: {new_key}")

    bot.send_message(message.chat.id, f"✅ Key Generated & Saved:\n{new_key}")

# --- Point ထည့်ရန် (Admin Only) ---
@bot.message_handler(commands=['add'])
def add_res(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()
        target_id, pts = args[1], int(args[2])
        db = load_db()
        if target_id in db["resellers"]:
            db["resellers"][target_id]["points"] += pts
        else:
            db["resellers"][target_id] = {"points": pts}
        save_db(db)
        bot.send_message(message.chat.id, f"✅ ID {target_id} ကို Point {pts} ခု ထည့်သွင်းပြီးပါပြီ။")
    except:
        bot.send_message(message.chat.id, "💡 Format: /add [ID] [Points]")

# --- Message Handling ---
@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    uid, text = str(message.from_user.id), message.text.strip()
    db = load_db()

    # Key Activate လုပ်ခြင်း
    if text in db["generated_keys"]:
        days = db["generated_keys"][text]
        expiry = datetime.now() + timedelta(days=days)
        db["users"][uid] = expiry.strftime("%Y-%m-%d")
        del db["generated_keys"][text]
        save_db(db)
        bot.send_message(message.chat.id, f"🎉 Activate အောင်မြင်သည်!\nသက်တမ်းကုန်ရက်: {db['users'][uid]}")
    
    elif text == "Point စစ်မည် 💰" and uid in db["resellers"]:
        bot.send_message(message.chat.id, f"💰 လက်ကျန် Point: {db['resellers'][uid]['points']}")
    
    elif text == "Key စာရင်း 📋" and int(uid) == ADMIN_ID:
        content, _ = get_github_file(KEY_LOG_PATH)
        bot.send_message(message.chat.id, f"🔑 Key မှတ်တမ်း (GitHub):\n\n{content or 'မရှိသေးပါ'}")

# --- Bot Run (Webhook Conflict ရှင်းရန်) ---
if __name__ == "__main__":
    print("Bot is starting...")
    try:
        bot.remove_webhook()
        print("Webhook removed successfully. Starting polling...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Error starting bot: {e}")
