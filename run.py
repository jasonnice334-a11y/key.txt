import telebot
from telebot import types
import json
from github import Github
import os
from datetime import datetime, timedelta
from flask import Flask
import threading
import base64

# Flask app for Render port binding
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Bot Logic
API_TOKEN = os.getenv('BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = 'jasonnice334-a11y/key.txt' # သင့် Repo နာမည် အမှန်ကို ပြန်စစ်ပါ
FILE_PATH = 'key.txt'

bot = telebot.TeleBot(API_TOKEN)
g = Github(GITHUB_TOKEN)

# --- Key Generation Functions (Logic from create_key.py) ---

def add_months(date, months):
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(date.day, days_in_month[month - 1])
    return date.replace(year=year, month=month, day=day)

def create_expiration(option):
    now = datetime.now()
    options = {"1": timedelta(hours=1), "2": timedelta(days=1), "3": timedelta(days=7), "4": timedelta(days=15)}
    month_options = {"5": 1, "6": 2, "7": 3, "8": 12}
    if option in options:
        expire = now + options[option]
    elif option in month_options:
        expire = add_months(now, month_options[option])
    else: return None
    return expire.strftime("%M-%H-%d-%m-%Y")

def save_key_to_github(new_key):
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(FILE_PATH)
    data = json.loads(contents.decoded_content.decode())
    if new_key not in data['clients']:
        data['clients'].append(new_key)
        repo.update_file(contents.path, f"Add key: {new_key}", json.dumps(data, indent=4), contents.sha)
        return True
    return False

# --- Bot Handlers ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Generate Key 🔑", callback_data="gen_key")
    btn2 = types.InlineKeyboardButton("List Keys 📋", callback_data="list_keys")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "🌟 Admin Panel is Online!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "gen_key")
def ask_option(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    options = [
        ("1 Hour", "1"), ("1 Day", "2"), ("7 Days", "3"), ("15 Days", "4"),
        ("1 Month", "5"), ("2 Months", "6"), ("3 Months", "7"), ("1 Year", "8")
    ]
    btns = [types.InlineKeyboardButton(text, callback_data=f"opt_{val}") for text, val in options]
    markup.add(*btns)
    bot.edit_message_text("Select Expiration Time:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("opt_"))
def ask_app_id(call):
    option = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, "Enter the Client App ID:")
    bot.register_next_step_handler(msg, process_generation, option)

def process_generation(message, option):
    app_id = message.text.strip()
    try:
        # App ID မှ UID ကို decode လုပ်ခြင်း
        uid = base64.b16decode(app_id[2:-3]).decode()
        if len(uid) <= 8: raise Exception()
        
        expire_date = create_expiration(option) # သက်တမ်းသတ်မှတ်ခြင်း
        generated_key = f"{uid}@{expire_date}"
        
        if save_key_to_github(generated_key):
            bot.send_message(message.chat.id, f"✅ Key Generated & Saved:\n`{generated_key}`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ Key already exists in database.")
            
    except:
        bot.send_message(message.chat.id, "❌ Invalid App ID. Please try again.")

@bot.callback_query_handler(func=lambda call: call.data == "list_keys")
def list_keys(call):
    try:
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(FILE_PATH)
        data = json.loads(contents.decoded_content.decode())
        clients = data.get('clients', [])
        if not clients:
            bot.send_message(call.message.chat.id, "No registered clients.")
        else:
            bot.send_message(call.message.chat.id, "📋 Registered Keys:\n" + "\n".join(clients))
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
