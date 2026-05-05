import telebot
import requests
import json
import base64

# --- CONFIGURATION (FIXED) ---
BOT_TOKEN = '8592959813:AAFRnywo_zeAAT0P2jcY8QEmdCoKll41kE0'
GITHUB_TOKEN = 'Ghp_rL8AbijSC79CARv997LeKIkj76XpXS2UY1AP'
REPO_OWNER = 'jasonnice334-a11y'
REPO_NAME = 'key.txt'
FILE_PATH = 'database.json'
# ----------------------------

bot = telebot.TeleBot(BOT_TOKEN)

def get_github_data():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            content_data = r.json()
            decoded_content = base64.b64decode(content_data['content']).decode('utf-8')
            return json.loads(decoded_content)
        else:
            print(f"GitHub Error: {r.status_code} (Check if file path is correct)")
            return None
    except Exception as e:
        print(f"Network Error: {e}")
        return None

@bot.message_handler(commands=['status'])
def show_status(message):
    uid = str(message.from_user.id)
    print(f"Checking data for Telegram ID: {uid}")
    db = get_github_data()
    
    if db and "users" in db and uid in db['users']:
        u = db['users'][uid]
        text = (f"📊 **သင်၏ လက်ကျန်များ**\n\n"
                f"🕒 Hour Bank: {u.get('hour_bank', 0)} နာရီ\n"
                f"⚡ 2H Keys: {u.get('2h_keys', 0)} ကြိမ်\n"
                f"📅 1 Month: {u.get('1month', 0)} ကြိမ်")
    else:
        text = (f"❌ သင့် ID: `{uid}` ကို Register အရင်လုပ်ပါ။\n\n"
                f"Admin ထံသို့ ဤ ID ကို ပို့ပေးပါရန်။")
    
    bot.reply_to(message, text, parse_mode="Markdown")

print("--- Bot is starting on Termux ---")
bot.infinity_polling()

