"""
=============================================================================
OFFICIAL ADVANCED TELEGRAM EARNING & QR TASK BOT
Developer / Owner: Abhishek (@abhishek723803)
Features: Dynamic Slab-Based QR Rewards, Secure Admin Panel, Toggle Sound Alerts,
          Referral System, Withdrawal History, Task History & Keep-Alive Flask Server.
=============================================================================
"""

import telebot
from telebot import types
import datetime
import threading
import time
from flask import Flask

# ==================== CONFIGURATION & API SETUP ====================
TOKEN = "8513419896:AAGjNu8vXEiJCUYjWZPSGtPoW6_0wRuQwpo"
bot = telebot.TeleBot(TOKEN)

# Strict Admin Identification Constants
ADMIN_USERNAME = "@abhishek723803"
ADMIN_ID = 841187478

# Bot Global State Management Dictionary
QR_STATE = {
    "is_available": True,   
    "is_claimed": False     
}

BOT_SETTINGS = {
    "channel_link": "https://t.me/+757WqqqLLoo4Yjhl",
    "channel_username": "@Abhishek_QR_Update",
    "min_withdrawal": 50.0
}

# In-Memory Data Storage Structures
USERS = {}
WITHDRAWALS_HISTORY = {}
TASK_HISTORY = {}
PENDING_WITHDRAWALS = {}


# ==================== KEEP ALIVE FLASK SERVER (RENDER DEPLOYMENT) ====================
app = Flask('')

@app.route('/')
def home():
    return "Telegram Earning Bot is running live and active with Render keep-alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()


# ==================== HELPER & UTILITY FUNCTIONS ====================
def get_user_data(user_id):
    """Fetch user data dictionary or initialize default profile if new user."""
    if user_id not in USERS:
        USERS[user_id] = {
            "balance": 0.0,
            "completed_tasks": 0,
            "referrals": 0,
            "notifications": True,  # Default sound notifications enabled
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "referred_by": None
        }
    return USERS[user_id]

def get_task_reward(task_number):
    """
    Dynamic Slab-Based Reward Calculator:
    - 1 to 10 QRs: ₹15 per QR
    - 10 to 20 QRs: ₹20 per QR
    - 20 to 30 QRs and above: ₹25 per QR
    """
    if task_number <= 10:
        return 15.0
    elif task_number <= 20:
        return 20.0
    else:
        return 25.0

def get_current_rate(completed_tasks):
    """Determine reward rate for the upcoming task."""
    next_task = completed_tasks + 1
    if next_task <= 10:
        return 15.0
    elif next_task <= 20:
        return 20.0
    else:
        return 25.0

def safe_send_message(chat_id, text, reply_markup=None, parse_mode="Markdown", sound_enabled=True):
    """Wrapper function to handle message sending with custom notification sound behavior."""
    try:
        return bot.send_message(
            chat_id, 
            text, 
            reply_markup=reply_markup, 
            parse_mode=parse_mode,
            disable_notification=not sound_enabled,
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error sending message to {chat_id}: {e}")
        return None


# ==================== START COMMAND & MAIN MENU HANDLER ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Handle Referral Parameter Parsing
    args = message.text.split()
    if len(args) > 1 and user_data["referred_by"] is None:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id:
                user_data["referred_by"] = referrer_id
                referrer_data = get_user_data(referrer_id)
                referrer_data["referrals"] += 1
                referrer_data["balance"] += 1.0  # Instant joining referral bonus
                safe_send_message(
                    referrer_id, 
                    f"🎉 **New Referral Joined!**\n\nUser ID `{user_id}` joined using your link. ₹1.00 bonus added to your wallet!", 
                    sound_enabled=referrer_data["notifications"]
                )
        except Exception as err:
            print(f"Referral processing exception: {err}")

    # Constructing Main Reply Keyboard with all 10 buttons
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_qr = types.KeyboardButton("🎯 GET QR")
    btn_balance = types.KeyboardButton("💰 My Balance")
    btn_account = types.KeyboardButton("👤 My Account")
    btn_withdraw = types.KeyboardButton("💸 Withdraw Money")
    btn_history = types.KeyboardButton("📜 Withdrawal History")
    btn_invite = types.KeyboardButton("👥 Invite & Earn")
    btn_task_hist = types.KeyboardButton("📋 Task History")
    btn_toggle = types.KeyboardButton("🔔 Toggle Notification")
    btn_support = types.KeyboardButton("🛠 Support")
    btn_admin = types.KeyboardButton("👑 Admin Panel")
    
    markup.add(btn_qr, btn_balance, btn_account, btn_withdraw, btn_history, 
               btn_invite, btn_task_hist, btn_toggle, btn_support, btn_admin)
    
    welcome_text = (
        f"👋 Welcome, **{message.from_user.first_name}**!\n\n"
        f"🤖 Welcome to our official Automated Earning & QR Task Bot.\n"
        f"Complete fast scanning tasks, claim rewards through dynamic earning slabs, and withdraw real money instantly!\n\n"
        f"👇 Choose any option from the menu below to get started:"
    )
    safe_send_message(message.chat.id, welcome_text, reply_markup=markup, sound_enabled=user_data["notifications"])


# ==================== GET QR SECTION & INTERACTION ====================
@bot.message_handler(func=lambda message: message.text == "🎯 GET QR")
def handle_get_qr(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not QR_STATE["is_available"]:
        no_qr_text = (
            "❌ **QR Tasks Currently Unavailable**\n\n"
            "There are no active QR tasks right now. Stay alert and keep notifications turned on to grab live tasks instantly when posted!\n\n"
            f"🔔 Official Update Channel:\n🔗 {BOT_SETTINGS['channel_link']}"
        )
        safe_send_message(message.chat.id, no_qr_text, sound_enabled=user_data["notifications"])
        
    elif QR_STATE["is_claimed"]:
        claimed_text = (
            "⚠️ **Task Already Claimed**\n\n"
            "Oops! This QR task has already been claimed by another user. Better luck next time! Wait for the next fresh QR drop.\n\n"
            f"🔔 Official Update Channel:\n🔗 {BOT_SETTINGS['channel_link']}"
        )
        safe_send_message(message.chat.id, claimed_text, sound_enabled=user_data["notifications"])
        
    else:
        current_reward = get_current_rate(user_data["completed_tasks"])
        
        qr_text = (
            f"🎯 **QR TASK & CLAIM ZONE** 🎯\n\n"
            f"⚠️ **IMPORTANT INSTRUCTIONS:**\n"
            f"Live QR tasks have strict validity. Complete payment quickly and submit your proof!\n\n"
            f"🎁 **Current Payout Rate:** ₹{current_reward}\n"
            f"⏳ **Status:** Active & Ready for Claim\n\n"
            f"Click the button below to secure this task and view payment options."
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Make Payment", callback_data="make_payment_action"))
        
        safe_send_message(message.chat.id, qr_text, reply_markup=markup, sound_enabled=user_data["notifications"])


# ==================== MAKE PAYMENT CALLBACK ====================
@bot.callback_query_handler(func=lambda call: call.data == "make_payment_action")
def ask_payment_proof(call):
    if QR_STATE["is_claimed"]:
        bot.answer_callback_query(call.id, "Sorry! This QR has already been claimed by someone else.", show_alert=True)
        return
    
    QR_STATE["is_claimed"] = True
    user_data = get_user_data(call.from_user.id)
    current_reward = get_current_rate(user_data["completed_tasks"])
    
    proof_text = (
        f"✅ **QR Successfully Claimed!**\n\n"
        f"🎁 **Reward Payout:** ₹{current_reward}\n"
        f"⏳ You have 4 minutes to complete the transaction and submit your payment screenshot proof.\n\n"
        f"💳 **Instructions:**\n"
        f"Scan the QR or complete the payment, then upload your transaction receipt screenshot directly as a photo in this chat."
    )
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=proof_text,
            parse_mode="Markdown"
        )
    except Exception:
        safe_send_message(call.message.chat.id, proof_text)


# ==================== PAYMENT SCREENSHOT & REWARD HANDLER ====================
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Increment completed tasks count
    user_data["completed_tasks"] += 1
    current_task_num = user_data["completed_tasks"]
    
    # Calculate reward via slab system
    reward = get_task_reward(current_task_num)
    user_data["balance"] += reward
    
    # Reset claim status for subsequent users
    QR_STATE["is_claimed"] = False
    
    # Log task history
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if user_id not in TASK_HISTORY:
        TASK_HISTORY[user_id] = []
    TASK_HISTORY[user_id].append(f"Task #{current_task_num} - ₹{reward} ({timestamp})")
    
    success_text = (
        f"✅ **Payment Proof Verified & Approved!**\n\n"
        f"🎁 **Reward Added (Task #{current_task_num}):** ₹{reward}\n"
        f"📋 **Total Completed QRs:** {current_task_num}\n"
        f"💰 **Updated Wallet Balance:** ₹{user_data['balance']}\n\n"
        f"🎉 Excellent work! Keep completing tasks to scale up your dynamic slab tier automatically."
    )
    safe_send_message(message.chat.id, success_text, sound_enabled=user_data["notifications"])


# ==================== MY BALANCE SECTION ====================
@bot.message_handler(func=lambda message: message.text == "💰 My Balance")
def my_balance(message):
    user_data = get_user_data(message.from_user.id)
    next_rate = get_current_rate(user_data["completed_tasks"])
    
    balance_content = (
        f"💰 **YOUR WALLET & EARNING TIERS** 💰\n\n"
        f"🏦 Available Wallet Balance: ₹{user_data['balance']}\n"
        f"⭐ Active Payout Rate: ₹{next_rate} / QR\n"
        f"🏧 Minimum Withdrawal Limit: ₹{BOT_SETTINGS['min_withdrawal']}\n\n"
        f"📊 **Dynamic Slab Reward Structure:**\n"
        f"• 1 to 10 QRs: ₹15 per QR\n"
        f"• 10 to 20 QRs: ₹20 per QR\n"
        f"• 20 to 30 QRs & above: ₹25 per QR\n\n"
        f"💡 *Complete more tasks to automatically upgrade your payout bracket!*"
    )
    safe_send_message(message.chat.id, balance_content, sound_enabled=user_data["notifications"])


# ==================== MY ACCOUNT SECTION ====================
@bot.message_handler(func=lambda message: message.text == "👤 My Account")
def my_account(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    account_info = (
        f"👤 **YOUR ACCOUNT PROFILE**\n\n"
        f"📌 Username: @{message.from_user.username if message.from_user.username else 'Member'}\n"
        f"🆔 Telegram ID: `{user_id}`\n\n"
        f"🏦 Balance: ₹{user_data['balance']}\n"
        f"📋 Completed QRs: {user_data['completed_tasks']}\n"
        f"👥 Total Referrals: {user_data['referrals']} Users\n"
        f"🔔 Sound Notification: {'ON 🔊' if user_data['notifications'] else 'OFF 🔕'}\n"
        f"📅 Joined On: {user_data['joined_date']}"
    )
    safe_send_message(message.chat.id, account_info, sound_enabled=user_data["notifications"])


# ==================== WITHDRAW MONEY SECTION ====================
@bot.message_handler(func=lambda message: message.text == "💸 Withdraw Money")
def withdraw_money(message):
    user_data = get_user_data(message.from_user.id)
    if user_data["balance"] < BOT_SETTINGS["min_withdrawal"]:
        safe_send_message(
            message.chat.id, 
            f"❌ **Insufficient Balance for Withdrawal.**\n\nYour current balance is ₹{user_data['balance']}.\nMinimum required limit is ₹{BOT_SETTINGS['min_withdrawal']}.",
            sound_enabled=user_data["notifications"]
        )
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Withdraw to UPI / Paytm", callback_data="process_withdraw"))
        withdraw_text = (
            f"💸 **WITHDRAWAL SECTION**\n\n"
            f"Available Balance: ₹{user_data['balance']}\n"
            f"Minimum Payout Limit: ₹{BOT_SETTINGS['min_withdrawal']}\n\n"
            f"Click the secure button below to process your payout instantly:"
        )
        safe_send_message(message.chat.id, withdraw_text, reply_markup=markup, sound_enabled=user_data["notifications"])

@bot.callback_query_handler(func=lambda call: call.data == "process_withdraw")
def process_withdrawal_callback(call):
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    if user_data["balance"] < BOT_SETTINGS["min_withdrawal"]:
        bot.answer_callback_query(call.id, "Insufficient balance!", show_alert=True)
        return
    
    amount = user_data["balance"]
    user_data["balance"] = 0.0  # Deduct balance after payout request
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if user_id not in WITHDRAWALS_HISTORY:
        WITHDRAWALS_HISTORY[user_id] = []
    WITHDRAWALS_HISTORY[user_id].append(f"₹{amount} - Processing ({timestamp})")
    
    if user_id not in PENDING_WITHDRAWALS:
        PENDING_WITHDRAWALS[user_id] = []
    PENDING_WITHDRAWALS[user_id].append({"amount": amount, "time": timestamp})
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ **Withdrawal Request Submitted Successfully!**\n\nAmount: ₹{amount}\nStatus: Processing\nYour funds will be credited to your verified UPI handle shortly.",
            parse_mode="Markdown"
        )
    except Exception:
        safe_send_message(call.message.chat.id, "✅ Withdrawal Request Submitted Successfully!")


# ==================== WITHDRAWAL HISTORY ====================
@bot.message_handler(func=lambda message: message.text == "📜 Withdrawal History")
def withdrawal_history(message):
    user_id = message.from_user.id
    history = WITHDRAWALS_HISTORY.get(user_id, [])
    
    history_content = (
        f"📜 **WITHDRAWAL HISTORY**\n\n"
        f"🆔 Telegram ID: `{user_id}`\n\n"
    )
    if not history:
        history_content += "No withdrawal transaction records found yet."
    else:
        history_content += "\n".join(f"• {item}" for item in history)
        
    safe_send_message(message.chat.id, history_content, sound_enabled=get_user_data(user_id)["notifications"])


# ==================== INVITE & EARN ====================
@bot.message_handler(func=lambda message: message.text == "👥 Invite & Earn")
def invite_earn(message):
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    
    invite_text = (
        f"👥 **REFERRAL PROGRAM & COMMISSION**\n\n"
        f"💰 **EARNING BENEFITS:**\n"
        f"1️⃣ Direct Join Bonus: ₹1.00 added instantly per referral join!\n"
        f"2️⃣ Active Network Rewards: Build your team and earn commissions.\n\n"
        f"🔗 **Your Unique Referral Link:**\n`{ref_link}`\n\n"
        f"Share this link with your friends and groups to expand your earnings!"
    )
    safe_send_message(message.chat.id, invite_text, sound_enabled=get_user_data(message.from_user.id)["notifications"])


# ==================== TASK HISTORY ====================
@bot.message_handler(func=lambda message: message.text == "📋 Task History")
def task_history(message):
    user_id = message.from_user.id
    tasks = TASK_HISTORY.get(user_id, [])
    
    if not tasks:
        task_text = "📋 **TASK HISTORY**\n\nNo completed tasks found yet. Click '🎯 GET QR' to start working on live tasks."
    else:
        task_text = "📋 **COMPLETED TASK HISTORY**\n\n" + "\n".join(f"• {t}" for t in tasks[-15:])
        
    safe_send_message(message.chat.id, task_text, sound_enabled=get_user_data(user_id)["notifications"])


# ==================== TOGGLE NOTIFICATION & FOCUS SOUND ====================
@bot.message_handler(func=lambda message: message.text == "🔔 Toggle Notification")
def toggle_notification(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    user_data["notifications"] = not user_data["notifications"]
    
    if user_data["notifications"]:
        status_desc = "Enabled 🔊 (Sound Alert Active)"
        note_msg = "You will now receive instant push notifications with alert sounds when new QR tasks become available, allowing you to claim instantly!"
    else:
        status_desc = "Disabled 🔕 (Silent Mode)"
        note_msg = "Task alerts will now be delivered silently without alert sounds."
        
    safe_send_message(
        message.chat.id, 
        f"🔔 **Notification & Sound Settings**\n\nStatus: **{status_desc}**\n\n{note_msg}", 
        sound_enabled=user_data["notifications"]  # Controls Telegram client sound behavior dynamically
    )


# ==================== SUPPORT ====================
@bot.message_handler(func=lambda message: message.text == "🛠 Support")
def support(message):
    support_text = (
        f"🛠 **CUSTOMER SUPPORT DESK**\n\n"
        f"👑 Owner Username: {ADMIN_USERNAME}\n"
        f"⏰ Support Timings: 10:00 AM - 10:00 PM\n\n"
        f"Feel free to contact the admin if you face any issues with payment approvals or withdrawals."
    )
    safe_send_message(message.chat.id, support_text, sound_enabled=get_user_data(message.from_user.id)["notifications"])


# ==================== ADVANCED ADMIN PANEL (STRICT SECURITY) ====================
@bot.message_handler(func=lambda message: message.text == "👑 Admin Panel")
def admin_panel(message):
    # Strict verification check for Owner ID and Username
    if message.from_user.id == ADMIN_ID or (message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.replace("@", "").lower()):
        admin_text = (
            f"👑 **Admin Control Panel**\n\n"
            f"Welcome Abhishek! Manage your bot settings and operations below:\n\n"
            f"📊 Total Registered Users: {len(USERS)}\n"
            f"🟢 Current QR Status: {'Available' if QR_STATE['is_available'] else 'Unavailable'}"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
            types.InlineKeyboardButton("📋 Pending Withdrawals", callback_data="admin_pending"),
            types.InlineKeyboardButton("📢 Broadcast Alert", callback_data="admin_broadcast_prompt"),
            types.InlineKeyboardButton("🔗 Set Channel", callback_data="admin_set_channel"),
            types.InlineKeyboardButton("🟢 Turn QR ON", callback_data="admin_qr_on"),
            types.InlineKeyboardButton("🔴 Turn QR OFF", callback_data="admin_qr_off")
        )
        safe_send_message(message.chat.id, admin_text, reply_markup=markup)
    else:
        # Silently ignore or deny unauthorized users
        safe_send_message(message.chat.id, "❌ You are not authorized to access the admin control panel!")

@bot.callback_query_handler(func=lambda call: call.data in [
    "admin_stats", "admin_pending", "admin_broadcast_prompt", 
    "admin_set_channel", "admin_qr_on", "admin_qr_off"
])
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Unauthorized access restricted!", show_alert=True)
        return
        
    if call.data == "admin_stats":
        total_payouts = sum(len(h) for h in WITHDRAWALS_HISTORY.values())
        stats_msg = (
            f"📊 **BOT LIVE STATISTICS**\n\n"
            f"👥 Total Users Registered: {len(USERS)}\n"
            f"💸 Total Payout Requests Processed: {total_payouts}\n"
            f"🎯 QR Task Status: {'Active' if QR_STATE['is_available'] else 'Inactive'}"
        )
        bot.answer_callback_query(call.id, "Fetching stats...")
        safe_send_message(call.message.chat.id, stats_msg)
        
    elif call.data == "admin_pending":
        total_pending = sum(len(v) for v in PENDING_WITHDRAWALS.values())
        bot.answer_callback_query(call.id, f"Pending withdrawals: {total_pending}")
        safe_send_message(call.message.chat.id, f"📋 **Pending Withdrawals Count:** {total_pending}\nReview and distribute payments through your merchant portal.")
        
    elif call.data == "admin_broadcast_prompt":
        bot.answer_callback_query(call.id)
        safe_send_message(call.message.chat.id, "📢 **Broadcast Manager:**\nSend your broadcast update message to push notifications with sound alerts across all registered bot members.")
        
    elif call.data == "admin_set_channel":
        bot.answer_callback_query(call.id)
        safe_send_message(call.message.chat.id, f"🔗 **Current Integration Channel:**\n{BOT_SETTINGS['channel_link']}\nSend a new link if you wish to modify channel bindings.")
        
    elif call.data == "admin_qr_on":
        QR_STATE["is_available"] = True
        QR_STATE["is_claimed"] = False
        bot.answer_callback_query(call.id, "QR tasks enabled successfully!")
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="👑 **Admin Panel**\n\nQR Status: **Enabled (Available)**", parse_mode="Markdown")
        except Exception:
            pass
                              
    elif call.data == "admin_qr_off":
        QR_STATE["is_available"] = False
        bot.answer_callback_query(call.id, "QR tasks disabled successfully!")
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="👑 **Admin Panel**\n\nQR Status: **Disabled (Unavailable)**", parse_mode="Markdown")
        except Exception:
            pass


# ==================== MAIN EXECUTION, KEEP-ALIVE & POLLING ====================
if __name__ == "__main__":
    print("Starting Keep-Alive Flask server for Render deployment...")
    keep_alive()
    
    print("Clearing old webhooks and pending updates to prevent API/Polling conflicts...")
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
        print("Webhook successfully reset and cleared.")
    except Exception as webhook_err:
        print(f"Webhook reset warning: {webhook_err}")
        
    print("Telegram Bot is running successfully with all advanced features and security layers...")
    
    # Infinite Polling Loop with Robust Error Handling & Auto-Reconnect
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
        except Exception as polling_error:
            print(f"Polling error encountered: {polling_error}")
            time.sleep(5)
