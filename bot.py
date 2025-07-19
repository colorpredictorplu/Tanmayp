import telebot
import requests
import os
import json
import re
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7377723790:AAF4CeGIpdyjF2DKvhj_qLhtKOWqRboHbjc'
OWNER_ID = 8115268811
ADMIN_USERNAME = 'TANMAYPAUL211'
MANDATORY_CHANNEL_ID = -1002322862030  # Hidden mandatory channel

bot = telebot.TeleBot(API_TOKEN)

# File paths
USERS_FILE = 'users.txt'
REFERRALS_FILE = 'referrals.txt'
REFER_COUNTS_FILE = 'refer_counts.txt'
SEARCH_CREDITS_FILE = 'search_credits.txt'

# Channel links (shown to users)
CHANNEL_LINKS = [
    {'name': 'MUST JOIN', 'url': 'https://t.me/itzdhruv1060'},
    {'name': 'JOIN MUST', 'url': 'https://t.me/itzpaidmodfree'},
    {'name': 'MUST', 'url': 'https://t.me/+F3tG9JyvsONmNjhl'},
    {'name': 'MainChnl', 'url': 'https://t.me/paidmodffreee'},
    {'name': 'KRLO', 'url': 'https://t.me/+6Vm4GewYMwVhMDU1'},
    {'name': 'FRIEND', 'url': 'https://t.me/itzdhruvfreindsgroup'}
]

user_last_result = {}
user_file_sent = {}

# --- Utility Functions ---
def load_file_list(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def save_file_list(filename, items):
    with open(filename, 'w') as f:
        for item in items: f.write(str(item) + "\n")

def load_referrals():
    if not os.path.exists(REFERRALS_FILE): return {}
    with open(REFERRALS_FILE, 'r') as f:
        return {int(k): int(v) for k, v in (line.strip().split(':') for line in f)}

def save_referrals(data):
    with open(REFERRALS_FILE, 'w') as f:
        for uid, ref in data.items():
            f.write(f"{uid}:{ref}\n")

def load_refer_counts():
    if not os.path.exists(REFER_COUNTS_FILE): return {}
    with open(REFER_COUNTS_FILE, 'r') as f:
        return {int(k): int(v) for k, v in (line.strip().split(':') for line in f)}

def save_refer_counts(data):
    with open(REFER_COUNTS_FILE, 'w') as f:
        for uid, count in data.items():
            f.write(f"{uid}:{count}\n")

def load_search_credits():
    if not os.path.exists(SEARCH_CREDITS_FILE): return {}
    with open(SEARCH_CREDITS_FILE, 'r') as f:
        return {int(k): int(v) for k, v in (line.strip().split(':') for line in f)}

def save_search_credits(data):
    with open(SEARCH_CREDITS_FILE, 'w') as f:
        for uid, count in data.items():
            f.write(f"{uid}:{count}\n")

def is_admin(user_id):
    return user_id == OWNER_ID

def add_user(user_id):
    users = load_file_list(USERS_FILE)
    if str(user_id) not in users:
        users.append(str(user_id))
        save_file_list(USERS_FILE, users)

def is_user_verified(user_id):
    try:
        member = bot.get_chat_member(MANDATORY_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Channel verification error: {e}")
        return False

def align_label(label, value):
    return f"{label:<16}: {value.strip()}"

def clean_emoji(text):
    emoji_pattern = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

# --- Formatters ---
def format_phone_response(json_text):
    try:
        data = json.loads(json_text)
        if not isinstance(data, list): return "❌ Invalid response format"
        
        result_lines = []
        for entry in data:
            result_lines.append("\n".join([
                align_label("📱 Mobile", entry.get('mobile', 'N/A')),
                align_label("🧑 Name", entry.get('name', 'N/A')),
                align_label("👨 Father", entry.get('fname', 'N/A')),
                align_label("📍 Address", entry.get('address', 'N/A').replace('!!', ', ').replace('!', ', ')),
                align_label("📞 Alternate", entry.get('alt', 'N/A')),
                align_label("🌐 Circle", entry.get('circle', 'N/A')),
                align_label("🆔 Aadhar", entry.get('id', 'N/A'))
            ]))
        return "\n\n".join(result_lines).strip()
    except Exception as e:
        print(f"Formatting error: {e}")
        return f"❌ Error formatting response\nRaw API response:\n{json_text}"

# --- Menus ---
def show_main_menu(user_id):
    name = bot.get_chat(user_id).first_name
    credits = load_search_credits().get(user_id, 0)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔍 Search Phone", callback_data="search_phone"),
        InlineKeyboardButton("👤 My Account", callback_data="menu_account")
    )
    markup.add(
        InlineKeyboardButton("📤 Refer & Earn", callback_data="refer_earn"),
        InlineKeyboardButton("📢 Join Channels", callback_data="join_channels")
    )
    bot.send_message(user_id, f"👋 Welcome {name}!\n🔍 Credits: {credits}\nYOUR REFER LINK\nhttps://t.me/{bot.get_me().username}?start={user_id}", reply_markup=markup)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    args = message.text.split()
    
    # Handle referral
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id:  # Prevent self-referral
                referrals = load_referrals()
                if user_id not in referrals:  # New referral
                    referrals[user_id] = referrer_id
                    save_referrals(referrals)
                    
                    # Update referrer count
                    refer_counts = load_refer_counts()
                    refer_counts[referrer_id] = refer_counts.get(referrer_id, 0) + 1
                    save_refer_counts(refer_counts)
                    
                    # Check for credit (every 2 referrals)
                    if refer_counts[referrer_id] % 2 == 0:
                        credits = load_search_credits()
                        credits[referrer_id] = credits.get(referrer_id, 0) + 1
                        save_search_credits(credits)
                        bot.send_message(referrer_id, "🎉 You earned 1 search credit for 2 referrals!")
        except Exception as e:
            print(f"Referral error: {e}")
    
    if not is_user_verified(user_id):
        show_join_channels(user_id)
        return
    
    add_user(user_id)
    show_main_menu(user_id)

def show_join_channels(user_id):
    markup = InlineKeyboardMarkup()
    # Add channel buttons in rows of 2
    for i in range(0, len(CHANNEL_LINKS), 2):
        row_links = CHANNEL_LINKS[i:i+2]
        buttons = [InlineKeyboardButton(link['name'], url=link['url']) for link in row_links]
        markup.row(*buttons)
    markup.add(InlineKeyboardButton("✅ Verify Join", callback_data="check_join"))
    bot.send_message(user_id, "📢 Join our channels:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def recheck_join(call):
    user_id = call.message.chat.id
    if is_user_verified(user_id):
        add_user(user_id)
        show_main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Please join all channels first!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "join_channels")
def handle_join_channels(call):
    show_join_channels(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "refer_earn")
def handle_refer_earn(call):
    user_id = call.message.chat.id
    refer_counts = load_refer_counts()
    referrals_made = refer_counts.get(user_id, 0)
    credits_earned = referrals_made // 2
    pending_for_next = 2 - (referrals_made % 2)
    
    bot.send_message(
        user_id,
        f"📤 *Referral Program*\n\n"
        f"👥 Your Referrals: {referrals_made}\n"
        f"🔍 Credits Earned: {credits_earned}\n"
        f"📌 Need {pending_for_next} more for next credit\n\n"
        f"🔗 Your Referral Link:\n"
        f"`https://t.me/{bot.get_me().username}?start={user_id}`\n\n"
        f"💡 2 Referrals = 1 Search Credit",
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "menu_account")
def handle_account_btn(call): 
    handle_account(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "search_phone")
def get_phone(call):
    uid = call.message.chat.id
    credits = load_search_credits()
    if credits.get(uid, 0) <= 0:
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "⚠️ No search credits!\n\nRefer 2 friends to get 1 free search!")
        return
    msg = bot.send_message(uid, "📲 Enter phone number (with country code):")
    bot.register_next_step_handler(msg, process_phone_search)

def process_phone_search(message):
    uid = message.chat.id
    number = message.text.strip()
    
    if not number:
        return bot.send_message(uid, "❌ Please enter a valid number")
    
    bot.send_message(uid, "⏳ Searching...")
    
    try:
        url = f"https://presents-specialties-mention-simpson.trycloudflare.com/search?key=bhanu555&mobile={number}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        
        if res.status_code != 200:
            raise Exception(f"API Error: {res.status_code}")
        
        result = format_phone_response(res.text)
        send_result_with_button(uid, "📱 Phone Info", result)
        
        # Deduct credit
        credits = load_search_credits()
        credits[uid] = credits.get(uid, 0) - 1
        save_search_credits(credits)
        
    except Exception as e:
        print(f"Search error: {e}")
        bot.send_message(uid, f"❌ Search failed:\n{e}")

def send_result_with_button(user_id, label, result_text):
    user_last_result[user_id] = result_text
    user_file_sent[user_id] = False
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 Download TXT", callback_data="download_txt"))
    bot.send_message(user_id, f"<b>{label}</b>\n\n<pre>{result_text}</pre>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "download_txt")
def send_txt(call):
    uid = call.message.chat.id
    if user_file_sent.get(uid, False):
        return bot.answer_callback_query(call.id, "✅ Already sent")
    
    txt = clean_emoji(user_last_result.get(uid, ""))
    with open("result.txt", 'w') as f:
        f.write(txt)
    with open("result.txt", 'rb') as doc:
        bot.send_document(uid, doc)
    os.remove("result.txt")
    user_file_sent[uid] = True
    bot.answer_callback_query(call.id, "📤 File sent")

def handle_account(message):
    uid = message.chat.id
    credits = load_search_credits().get(uid, 0)
    refer_counts = load_refer_counts()
    referrals = refer_counts.get(uid, 0)
    
    bot.send_message(
        uid,
        f"👤 *Account Info*\n\n"
        f"🆔 ID: `{uid}`\n"
        f"🔍 Credits: {credits}\n"
        f"👥 Referrals: {referrals}\n\n"
        f"🔗 Referral Link:\n"
        f"`https://t.me/{bot.get_me().username}?start={uid}`\n\n"
        f"💡 2 Referrals = 1 Search Credit",
        parse_mode="Markdown"
    )

# --- Admin Commands ---
@bot.message_handler(commands=['total'])
def total_cmd(message):
    if not is_admin(message.chat.id): return
    users = load_file_list(USERS_FILE)
    refer_counts = load_refer_counts()
    total_refs = sum(refer_counts.values())
    active_users = len([uid for uid in users if load_search_credits().get(int(uid), 0) > 0])
    bot.send_message(
        message.chat.id,
        f"📊 *Stats*\n\n"
        f"👤 Users: {len(users)}\n"
        f"🔍 Active: {active_users}\n"
        f"👥 Referrals: {total_refs}",
        parse_mode="Markdown"
    )

print("🤖 Bot is running...")
bot.polling()
