import telebot
from telebot import types
import json
from github import Github
import os
from datetime import datetime, timedelta
from flask import Flask
import threading

# Flask app for Render port binding
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Bot Logic
API_TOKEN = os.getenv('BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = 'jasonnice334-a11y/key.txt'
FILE_PATH = 'key.txt'

bot = telebot.TeleBot(API_TOKEN)
g = Github(GITHUB_TOKEN)

def get_db():
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(FILE_PATH)
    return json.loads(contents.decoded_content.decode()), contents

def save_db(data, sha):
    repo = g.get_repo(REPO_NAME)
    repo.update_file(FILE_PATH, "Update Database", json.dumps(data, indent=4), sha)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_list = types.KeyboardButton('/list')
    btn_gen = types.KeyboardButton('Generate Key 🔑')
    markup.add(btn_list, btn_gen)
    bot.send_message(message.chat.id, "🌟 Admin Panel is Online!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Generate Key 🔑')
def choose_time(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    times = {"1 Hour": 3600, "1 Day": 86400, "7 Days": 604800, "1 Month": 2592000}
    buttons = [types.InlineKeyboardButton(text=k, callback_data=f"gen_{v}") for k, v in times.items()]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Select duration:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('gen_'))
def handle_gen(call):
    seconds = int(call.data.split('_')[1])
    expire_date = (datetime.now() + timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")
    new_key = f"u0_a{call.from_user.id}@{datetime.now().strftime('%H-%M-%S')}"
    try:
        db, contents = get_db()
        if "clients" not in db: db["clients"] = []
        db["clients"].append(new_key)
        save_db(db, contents.sha)
        bot.edit_message_text(f"✅ Key: `{new_key}`\n📅 Expire: {expire_date}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['list'])
def list_clients(message):
    try:
        db, _ = get_db()
        clients = db.get("clients", [])
        if not clients:
            bot.send_message(message.chat.id, "No clients found.")
            return
        text = "📋 Client List:\n\n"
        markup = types.InlineKeyboardMarkup()
        for c in clients:
            text += f"👤 {c}\n"
            markup.add(types.InlineKeyboardButton(text=f"❌ Delete: {c}", callback_data=f"del_{c}"))
        bot.send_message(message.chat.id, text, reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
