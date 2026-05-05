import telebot
from telebot import types
import json
import os
import base64
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
        return {"resellers": {}, "generated_keys": {}, "users": {}}
    with open(DB_FILE, 'r') as f:
        try: return json.load(f)
        except: return {"resellers": {}, "generated_keys": {}, "users": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Key Generation Logic (Your Specific Format) ---
def create_expiration_string(days):
    now = datetime.now()
    expire = now + timedelta(days=days)
    # မိနစ်-နာရီ-ရက်-လ-ခုနှစ် ပုံစံအတိုင်း ပြန်ပေးခြင်း
    return expire.strftime("%M-%H-%d-%m-%Y")

# --- Commands ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    db = load_db()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if int(uid) == ADMIN_ID:
        markup.add("Key ထုတ်မည် 🔑", "Reseller စာရင်း 📋", "Key စာရင်း 🔑")
        bot.send_message(message.chat.id, f"🌟 **Admin Panel**\nAdmin: `{ADMIN_NAME}`", reply_markup=markup)
    elif uid in db["resellers"]:
        markup.add("Key ထုတ်မည် 🔑", "Point စစ်မည် 💰")
        bot.send_message(message.chat.id, f"👋 **Reseller Panel**\nPoints: `{db['resellers'][uid]['points']}`", reply_markup=markup)
    else:
        expiry = db["users"].get(uid, "သက်တမ်းမရှိသေးပါ")
        bot.send_message(message.chat.id, f"👤 **User Status**\nExpiry: `{expiry}`\n\nKey ကို ရိုက်ထည့်၍ Activate လုပ်နိုင်ပါသည်။")

# --- Generate Key Steps ---
@bot.message_handler(func=lambda m: m.text == "Key ထုတ်မည် 🔑")
def handle_gen_key(message):
    uid = str(message.from_user.id)
    db = load_db()
    if int(uid) != ADMIN_ID and uid not in db["resellers"]: return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    times = {"၁ နာရီ": 0.04, "၁ ရက်": 1, "၇ ရက်": 7, "၁၅ ရက်": 15, "၁ လ": 30, "၁ နှစ်": 365}
    btns = [types.InlineKeyboardButton(text=t, callback_data=f"time_{d}") for t, d in times.items()]
    markup.add(*btns)
    bot.send_message(message.chat.id, "သက်တမ်းရွေးချယ်ပါ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("time_"))
def get_app_id(call):
    user_process[call.from_user.id] = {"days": float(call.data.split("_")[1])}
    msg = bot.edit_message_text("Client ၏ App ID ကို ရိုက်ထည့်ပါ:", chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.register_next_step_handler(msg, finalize_generation)

def finalize_generation(message):
    uid = str(message.from_user.id)
    appID = message.text.strip()
    db = load_db()

    # Base64 Decoding logic from your file
    try:
        real_uid = base64.b16decode(appID[2:-3]).decode()
        if len(real_uid) <= 8: raise Exception()
    except:
        bot.send_message(message.chat.id, "❌ Invalid App ID! ကျေးဇူးပြု၍ ပြန်စစ်ပါ။")
        return

    if int(uid) != ADMIN_ID:
        if db["resellers"][uid]["points"] <= 0:
            bot.send_message(message.chat.id, "❌ Point မလောက်တော့ပါ။")
            return
        db["resellers"][uid]["points"] -= 1

    # သင့်ရဲ့ Format အတိုင်း Key ထုတ်ခြင်း: uid@မိနစ်-နာရီ-ရက်-လ-ခုနှစ်
    expire_str = create_expiration_string(user_process[message.from_user.id]["days"])
    new_key = f"{real_uid}@{expire_str}"
    
    db["generated_keys"][new_key] = user_process[message.from_user.id]["days"]
    save_db(db)
    bot.send_message(message.chat.id, f"✅ **Key ထွက်လာပါပြီ:**\n`{new_key}`", parse_mode="Markdown")

# --- Key Activation Logic ---
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = str(message.from_user.id)
    text = message.text.strip()
    db = load_db()

    if text in db["generated_keys"]:
        days = db["generated_keys"][text]
        # သက်တမ်းတိုးပေးခြင်း
        now = datetime.now()
        start_date = max(now, datetime.strptime(db["users"].get(uid, now.strftime("%Y-%m-%d")), "%Y-%m-%d")) if uid in db["users"] else now
        expiry = start_date + timedelta(days=days)
        db["users"][uid] = expiry.strftime("%Y-%m-%d")
        del db["generated_keys"][text]
        save_db(db)
        bot.send_message(message.chat.id, f"🎉 **Activate အောင်မြင်သည်!**\nသက်တမ်းကုန်ရက်: `{db['users'][uid]}`")
    
    elif text == "Key စာရင်း 🔑" and int(uid) == ADMIN_ID:
        keys = db.get("generated_keys", {})
        msg = "🔑 **အသုံးမပြုရသေးသော Key များ:**\n\n" + "\n".join([f"`{k}`" for k in keys.keys()])
        bot.send_message(message.chat.id, msg if keys else "Key စာရင်းမရှိပါ။", parse_mode="Markdown")

bot.infinity_polling()@bot.message_handler(func=lambda m: m.text == "Key စာရင်း 🔑")
def view_keys(message):
    if message.from_user.id != ADMIN_ID: return
    
    if os.path.exists("key.txt"):
        with open("key.txt", "r") as f:
            all_keys = f.read()
        if all_keys.strip():
            bot.send_message(message.chat.id, f"🔑 **လက်ရှိ Key စာရင်း:**\n\n`{all_keys}`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "လက်ရှိတွင် Key စာရင်း အလွတ်ဖြစ်နေပါသည်။")
    else:
        bot.send_message(message.chat.id, "Key မှတ်တမ်းဖိုင် မရှိသေးပါ။")
        
def finalize_generation(message):
    # ... (ယခင် code များ) ...
    
    # Key ကို key.txt ဖိုင်ထဲသို့ ထည့်သွင်းခြင်း
    with open("key.txt", "a") as f:
        f.write(f"{new_key}\n")
    
    bot.send_message(message.chat.id, f"✅ **Key ထွက်လာပါပြီ:**\n`{new_key}`\n\n(Key ကို key.txt ထဲသို့ သိမ်းဆည်းပြီးပါပြီ)", parse_mode="Markdown")
    
