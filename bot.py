"""
=============================================================================
OFFICIAL ABHISHEKQRBOT - ADVANCED EARNING & QR TASK BOT (FINAL FIXED)
Developer / Owner: Abhishek (@abhishek723803)
Description: Fully fixed bot with command menu, all 10 reply buttons, 
             strict Force Join, admin QR controls, and slab-based payouts.
=============================================================================
"""

import telebot
from telebot import types
import datetime
import threading
import time
from flask import Flask

# ============================================================================
# SECTION 1: CONFIGURATION & CORE SETUP
# ============================================================================

TOKEN = "8513419896:AAGjNu8vXEiJCUYjWZPSGtPoW6_0wRuQwpo"
bot = telebot.TeleBot(TOKEN)

# Administrative Security Constants
ADMIN_USERNAME = "@abhishek723803"
ADMIN_ID = 841187478
BOT_NAME = "ABHISHEKQRBOT"

# Global Bot State Dictionaries
QR_STATE = {
    "is_available": False,     
    "qr_image_id": None,       
    "is_claimed": False        
}

ADMIN_STATE = {}  

BOT_SETTINGS = {
    "channel_link": "https://t.me/A_ToolsX",  
    "min_withdrawal": 10.0
}

# In-Memory Database Structures
USERS = {}
WITHDRAWALS_HISTORY = {}
TASK_HISTORY = {}
PENDING_WITHDRAWALS = {}
PENDING_APPROVALS = {}
VERIFIED_USERS = set()


# ============================================================================
# SECTION 2: FLASK KEEP-ALIVE SERVER (RENDER DEPLOYMENT)
# ============================================================================

app = Flask('')

@app.route('/')
def home():
    return "ABHISHEKQRBOT is running live and operational!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()


# ============================================================================
# SECTION 3: UTILITY & HELPER FUNCTIONS
# ============================================================================

def get_user_data(user_id):
    if user_id not in USERS:
        USERS[user_id] = {
            "balance": 0.0,
            "completed_tasks": 0,
            "referrals": 0,
            "notifications": True,
            "banned": False,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "referred_by": None
        }
    return USERS[user_id]

def is_user_banned(user_id):
    return get_user_data(user_id).get("banned", False)

def get_task_reward(completed_tasks):
    next_task = completed_tasks + 1
    if next_task <= 10:
        return 15.0
    elif next_task <= 20:
        return 20.0
    else:
        return 25.0

def safe_send_message(chat_id, text, reply_markup=None, sound_enabled=True):
    try:
        return bot.send_message(
            chat_id, 
            text, 
            reply_markup=reply_markup, 
            parse_mode=None,
            disable_notification=not sound_enabled,
            disable_web_page_preview=True
        )
    except Exception as error_msg:
        print(f"Error sending message to {chat_id}: {error_msg}")
        return None


# ============================================================================
# SECTION 4: MAIN MENU KEYBOARD BUILDER (EXACT 10 BUTTONS)
# ============================================================================

def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🎯 GET QR"),
        types.KeyboardButton("💰 My Balance"),
        types.KeyboardButton("👤 My Account"),
        types.KeyboardButton("💸 Withdraw Money"),
        types.KeyboardButton("📜 Withdrawal History"),
        types.KeyboardButton("👥 Invite & Earn"),
        types.KeyboardButton("📋 Task History"),
        types.KeyboardButton("🔔 Toggle Notification"),
        types.KeyboardButton("🛠 Support"),
        types.KeyboardButton("👑 Admin Panel")
    )
    return markup


# ============================================================================
# SECTION 5: /START COMMAND & FORCE JOIN VERIFICATION SYSTEM
# ============================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ Access Denied: Aapko admin dwara is bot se ban kar diya gaya hai.")
        return

    user_data = get_user_data(user_id)
    
    args = message.text.split()
    if len(args) > 1 and user_data["referred_by"] is None:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id and not is_user_banned(referrer_id):
                user_data["referred_by"] = referrer_id
                referrer_data = get_user_data(referrer_id)
                referrer_data["referrals"] += 1
                referrer_data["balance"] += 1.0  
                
                safe_send_message(
                    referrer_id, 
                    f"New Referral Joined!\n\nUser ID {user_id} joined using your link. ₹1.00 direct joining bonus added to your wallet!", 
                    sound_enabled=referrer_data["notifications"]
                )
        except Exception as ref_err:
            print(f"Referral error: {ref_err}")

    if user_id not in VERIFIED_USERS:
        force_join_markup = types.InlineKeyboardMarkup(row_width=1)
        force_join_markup.add(
            types.InlineKeyboardButton("📢 Join Update Channel", url=BOT_SETTINGS["channel_link"]),
            types.InlineKeyboardButton("✅ Joined & Start Bot", callback_data="verify_force_join")
        )
        join_msg = (
            f"⚠️ Channel Join Required!\n\n"
            f"Welcome to {BOT_NAME} 🤖\n"
            f"Bot ko use karne ke liye sabse pehle hamara official update channel join karna zaroori hai.\n\n"
            f"👇 Neeche diye gaye button par click karke channel join karein aur phir 'Joined & Start Bot' par click karein:"
        )
        safe_send_message(message.chat.id, join_msg, reply_markup=force_join_markup)
        return

    show_main_menu_screen(message.chat.id, message.from_user.first_name, user_data["notifications"])


@bot.callback_query_handler(func=lambda call: call.data == "verify_force_join")
def verify_force_join_callback(call):
    user_id = call.from_user.id
    VERIFIED_USERS.add(user_id)
    bot.answer_callback_query(call.id, "Channel verification successful! Welcome.")
    
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        pass
        
    user_data = get_user_data(user_id)
    show_main_menu_screen(call.message.chat.id, call.from_user.first_name, user_data["notifications"])


def show_main_menu_screen(chat_id, first_name, sound_enabled):
    markup = get_main_menu_keyboard()
    welcome_text = (
        f"👋 Welcome, {first_name} to {BOT_NAME}!\n\n"
        f"🤖 Aapka swagat hai hamare official Automated Earning & QR Task Bot mein.\n"
        f"Yahan aap fast scanning tasks complete karke, rewards earn kar sakte hain aur dosto ko invite karke direct bonus pa sakte hain.\n\n"
        f"👇 Neeche menu se koi bhi option chunein:"
    )
    safe_send_message(chat_id, welcome_text, reply_markup=markup, sound_enabled=sound_enabled)


# ============================================================================
# SECTION 6: "GET QR" SECTION (STRICT ADMIN-CONTROLLED AVAILABILITY)
# ============================================================================

@bot.message_handler(func=lambda message: message.text == "🎯 GET QR")
def handle_get_qr(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ Aapko ban kar diya gaya hai.")
        return

    user_data = get_user_data(user_id)
    
    if not QR_STATE["is_available"] or not QR_STATE["qr_image_id"]:
        no_qr_text = "❌ QR is not available right now. Please try again later.\n(अभी क्यूआर उपलब्ध नहीं है। कृपया थोड़ी देर के बाद प्रयास करें।)"
        safe_send_message(message.chat.id, no_qr_text, sound_enabled=user_data["notifications"])
        return
        
    if QR_STATE["is_claimed"]:
        claimed_text = (
            "⚠️ Task Already Claimed\n\n"
            "Oops! Yeh QR task pehle hi kisi aur user dwara claim kiya ja chuka hai. Kripya next fresh QR drop ke liye wait karein!"
        )
        safe_send_message(message.chat.id, claimed_text, sound_enabled=user_data["notifications"])
        return
        
    current_reward = get_task_reward(user_data["completed_tasks"])
    qr_caption = (
        f"🎯 QR TASK & CLAIM ZONE 🎯\n\n"
        f"🎁 Current Payout Rate: ₹{current_reward}\n\n"
        f"📌 Instructions:\n"
        f"1️⃣ Neeche diye gaye QR ko scan karke payment complete karein.\n"
        f"2️⃣ Payment ke baad 'Make Payment' button par click karein ya apna screenshot direct is chat mein bhej dein."
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Make Payment & Proceed", callback_data="make_payment_action"))
    
    try:
        bot.send_photo(
            message.chat.id, 
            QR_STATE["qr_image_id"], 
            caption=qr_caption, 
            reply_markup=markup, 
            parse_mode=None
        )
    except Exception as e:
        print(f"Error sending QR image: {e}")
        safe_send_message(message.chat.id, "❌ Error loading QR. Please try again later.")


# ============================================================================
# SECTION 7: PAYMENT & SCREENSHOT SUBMISSION (MANUAL APPROVAL FLOW)
# ============================================================================

@bot.callback_query_handler(func=lambda call: call.data == "make_payment_action")
def ask_payment_proof(call):
    if is_user_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "You are banned!", show_alert=True)
        return

    if not QR_STATE["is_available"] or QR_STATE["is_claimed"]:
        bot.answer_callback_query(call.id, "Sorry! Yeh QR available nahi hai ya pehle hi claim ho chuka hai.", show_alert=True)
        return
    
    QR_STATE["is_claimed"] = True
    user_data = get_user_data(call.from_user.id)
    current_reward = get_task_reward(user_data["completed_tasks"])
    
    proof_text = (
        f"✅ Payment Session Active!\n\n"
        f"🎁 Reward Payout: ₹{current_reward}\n"
        f"⏳ Aapne QR scan karke payment kar di hai?\n\n"
        f"💳 Action: Kripya apne payment ka screenshot (photo) direct is chat mein upload karein taaki admin verification ke liye bhej sakein."
    )
    
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=proof_text,
            parse_mode=None
        )
    except Exception:
        safe_send_message(call.message.chat.id, proof_text)


@bot.message_handler(content_types=['photo'])
def handle_incoming_photos(message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID and ADMIN_STATE.get(ADMIN_ID) == "waiting_for_qr_photo":
        photo_file_id = message.photo[-1].file_id
        QR_STATE["qr_image_id"] = photo_file_id
        QR_STATE["is_available"] = True
        QR_STATE["is_claimed"] = False
        ADMIN_STATE.pop(ADMIN_ID, None)
        
        safe_send_message(
            ADMIN_ID, 
            "✅ Success! New QR Code successfully set and QR Status is now ON (Available) for users."
        )
        return

    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ Aapko ban kiya gaya hai, screenshot accept nahi hoga.")
        return

    user_data = get_user_data(user_id)
    current_task_num = user_data["completed_tasks"] + 1
    reward = get_task_reward(user_data["completed_tasks"])
    
    QR_STATE["is_claimed"] = False  
    
    photo_file_id = message.photo[-1].file_id
    admin_caption = (
        f"📸 New Payment Proof Submitted for Approval!\n\n"
        f"👤 User Name: {message.from_user.first_name}\n"
        f"🔖 Username: @{message.from_user.username if message.from_user.username else 'NoUsername'}\n"
        f"🆔 User ID: {user_id}\n"
        f"📋 Task Number: #{current_task_num}\n"
        f"🎁 Expected Reward: ₹{reward}\n\n"
        f"Kripya payment receipt check karke Approve ya Reject karein:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )
    
    try:
        sent_admin_msg = bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_caption, reply_markup=markup, parse_mode=None)
        PENDING_APPROVALS[sent_admin_msg.message_id] = {"user_id": user_id, "reward": reward}
    except Exception as img_err:
        print(f"Error forwarding screenshot to admin: {img_err}")
    
    submission_text = (
        f"📥 Screenshot Successfully Submitted!\n\n"
        f"Aapka payment screenshot admin ke paas approval ke liye bhej diya gaya hai.\n"
        f"⏳ Jaise hi admin isse Approve karenge, tabhi aapke wallet mein ₹{reward} add hoga."
    )
    safe_send_message(message.chat.id, submission_text, sound_enabled=user_data["notifications"])


# ============================================================================
# SECTION 8: ADMIN APPROVAL / REJECTION & DYNAMIC RATE UPDATE
# ============================================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_admin_verification(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Unauthorized action!", show_alert=True)
        return
        
    data_parts = call.data.split("_")
    action = data_parts[0]
    user_id = int(data_parts[1])
    user_data = get_user_data(user_id)
    
    if action == "approve":
        reward = get_task_reward(user_data["completed_tasks"])
        user_data["completed_tasks"] += 1
        current_task_num = user_data["completed_tasks"]
        user_data["balance"] += reward
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if user_id not in TASK_HISTORY:
            TASK_HISTORY[user_id] = []
        TASK_HISTORY[user_id].append(f"Task #{current_task_num} - ₹{reward} ({timestamp})")
        
        bot.answer_callback_query(call.id, f"Approved! ₹{reward} credited successfully.")
        
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + f"\n\n✅ STATUS: APPROVED BY ADMIN (₹{reward} Credited, Total Tasks: {current_task_num})",
                parse_mode=None
            )
        except Exception:
            pass
            
        next_rate = get_task_reward(user_data["completed_tasks"])
        success_user_msg = (
            f"✅ Payment Approved by Admin!\n\n"
            f"🎁 Reward Added (Task #{current_task_num}): ₹{reward}\n"
            f"💰 Updated Wallet Balance: ₹{user_data['balance']}\n"
            f"⭐ Next Task Payout Rate: ₹{next_rate}\n\n"
            f"🎉 Badhai ho! Aise hi aur tasks complete karte rahein."
        )
        safe_send_message(user_id, success_user_msg, sound_enabled=user_data["notifications"])
        
    elif action == "reject":
        bot.answer_callback_query(call.id, "Payment proof reject kar diya gaya hai.")
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + f"\n\n❌ STATUS: REJECTED BY ADMIN",
                parse_mode=None
            )
        except Exception:
            pass
            
        reject_user_msg = (
            f"❌ Payment Proof Rejected\n\n"
            f"Aapka submitted payment screenshot admin dwara reject kar diya gaya hai. Kripya sahi screenshot upload karein."
        )
        safe_send_message(user_id, reject_user_msg, sound_enabled=user_data["notifications"])


# ============================================================================
# SECTION 9: MENU BUTTON HANDLERS (ALL 10 BUTTONS RESTORED)
# ============================================================================

@bot.message_handler(func=lambda message: message.text == "💰 My Balance")
def my_balance(message):
    if is_user_banned(message.from_user.id): return
    user_data = get_user_data(message.from_user.id)
    next_rate = get_task_reward(user_data["completed_tasks"])
    
    balance_content = (
        f"💰 YOUR WALLET & EARNING TIERS 💰\n\n"
        f"🏦 Available Balance: ₹{user_data['balance']}\n"
        f"⭐ Current Payout Rate: ₹{next_rate} / QR\n"
        f"✅ Completed Approved Tasks: {user_data['completed_tasks']}\n"
        f"🏧 Minimum Withdrawal: ₹{BOT_SETTINGS['min_withdrawal']}\n\n"
        f"📊 Dynamic Slab Reward Structure:\n"
        f"• 1 to 10 QRs: ₹15 per QR\n"
        f"• 11 to 20 QRs: ₹20 per QR\n"
        f"• 21 to 30+ QRs: ₹25 per QR"
    )
    safe_send_message(message.chat.id, balance_content, sound_enabled=user_data["notifications"])


@bot.message_handler(func=lambda message: message.text == "👤 My Account")
def my_account(message):
    if is_user_banned(message.from_user.id): return
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    next_rate = get_task_reward(user_data["completed_tasks"])
    
    account_info = (
        f"👤 YOUR ACCOUNT PROFILE\n\n"
        f"📌 Name: {message.from_user.first_name}\n"
        f"🔖 Username: @{message.from_user.username if message.from_user.username else 'None'}\n"
        f"🆔 Telegram ID: {user_id}\n\n"
        f"🏦 Wallet Balance: ₹{user_data['balance']}\n"
        f"📋 Completed QRs: {user_data['completed_tasks']}\n"
        f"⭐ Active Reward Rate: ₹{next_rate}\n"
        f"👥 Total Referrals: {user_data['referrals']} Users\n"
        f"🔔 Sound Notification: {'ON 🔊' if user_data['notifications'] else 'OFF 🔕'}\n"
        f"📅 Joined On: {user_data['joined_date']}"
    )
    safe_send_message(message.chat.id, account_info, sound_enabled=user_data["notifications"])


@bot.message_handler(func=lambda message: message.text == "💸 Withdraw Money")
def withdraw_money(message):
    if is_user_banned(message.from_user.id): return
    user_data = get_user_data(message.from_user.id)
    if user_data["balance"] < BOT_SETTINGS["min_withdrawal"]:
        safe_send_message(
            message.chat.id, 
            f"❌ Insufficient Balance.\n\nAapka current balance ₹{user_data['balance']} hai.\nMinimum withdrawal limit ₹{BOT_SETTINGS['min_withdrawal']} honi chahiye.",
            sound_enabled=user_data["notifications"]
        )
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Withdraw to UPI / Paytm", callback_data="process_withdraw"))
        withdraw_text = (
            f"💸 WITHDRAWAL SECTION\n\n"
            f"Available Balance: ₹{user_data['balance']}\n"
            f"Minimum Limit: ₹{BOT_SETTINGS['min_withdrawal']}\n\n"
            f"Neeche diye gaye button par click karke payout request submit karein:"
        )
        safe_send_message(message.chat.id, withdraw_text, reply_markup=markup, sound_enabled=user_data["notifications"])

@bot.callback_query_handler(func=lambda call: call.data == "process_withdraw")
def process_withdrawal_callback(call):
    user_id = call.from_user.id
    if is_user_banned(user_id): return
    user_data = get_user_data(user_id)
    if user_data["balance"] < BOT_SETTINGS["min_withdrawal"]:
        bot.answer_callback_query(call.id, "Insufficient balance!", show_alert=True)
        return
    
    amount = user_data["balance"]
    user_data["balance"] = 0.0  
    
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
            text=f"✅ Withdrawal Request Submitted Successfully!\n\nAmount: ₹{amount}\nStatus: Processing"
        )
    except Exception:
        safe_send_message(call.message.chat.id, "✅ Withdrawal Request Submitted Successfully!")


@bot.message_handler(func=lambda message: message.text == "📜 Withdrawal History")
def withdrawal_history(message):
    if is_user_banned(message.from_user.id): return
    user_id = message.from_user.id
    history = WITHDRAWALS_HISTORY.get(user_id, [])
    
    history_content = f"📜 WITHDRAWAL HISTORY\n\n🆔 Telegram ID: {user_id}\n\n"
    if not history:
        history_content += "Koi bhi withdrawal transaction record nahi mila."
    else:
        history_content += "\n".join(f"• {item}" for item in history)
        
    safe_send_message(message.chat.id, history_content, sound_enabled=get_user_data(user_id)["notifications"])


@bot.message_handler(func=lambda message: message.text == "👥 Invite & Earn")
def invite_earn(message):
    if is_user_banned(message.from_user.id): return
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    
    invite_text = (
        f"👥 REFERRAL PROGRAM & DIRECT BONUS\n\n"
        f"💰 BENEFIT:\n"
        f"• Direct Joining Bonus: Har ek naye referral ke join hone par turant ₹1.00 direct bonus paayein!\n\n"
        f"🔗 Aapka Referral Link:\n{ref_link}"
    )
    safe_send_message(message.chat.id, invite_text, sound_enabled=get_user_data(message.from_user.id)["notifications"])


@bot.message_handler(func=lambda message: message.text == "📋 Task History")
def task_history(message):
    if is_user_banned(message.from_user.id): return
    user_id = message.from_user.id
    tasks = TASK_HISTORY.get(user_id, [])
    
    if not tasks:
        task_text = "📋 TASK HISTORY\n\nAbhi tak koi bhi completed task nahi hai."
    else:
        task_text = "📋 COMPLETED TASK HISTORY\n\n" + "\n".join(f"• {t}" for t in tasks[-15:])
        
    safe_send_message(message.chat.id, task_text, sound_enabled=get_user_data(user_id)["notifications"])


@bot.message_handler(func=lambda message: message.text == "🔔 Toggle Notification")
def toggle_notification(message):
    if is_user_banned(message.from_user.id): return
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    user_data["notifications"] = not user_data["notifications"]
    
    status_desc = "Enabled 🔊" if user_data["notifications"] else "Disabled 🔕"
    safe_send_message(message.chat.id, f"🔔 Notification Settings\n\nStatus: {status_desc}", sound_enabled=user_data["notifications"])


@bot.message_handler(func=lambda message: message.text == "🛠 Support")
def support(message):
    if is_user_banned(message.from_user.id): return
    support_text = (
        f"🛠 CUSTOMER SUPPORT DESK\n\n"
        f"👑 Owner Username: {ADMIN_USERNAME}\n"
        f"⏰ Timing: 10:00 AM - 10:00 PM\n\n"
        f"Payment ya withdrawal mein koi bhi problem ho toh admin se contact karein."
    )
    safe_send_message(message.chat.id, support_text, sound_enabled=get_user_data(message.from_user.id)["notifications"])


# ============================================================================
# SECTION 10: EXCLUSIVE ADMIN PANEL & SECURITY RESTRICTIONS
# ============================================================================

@bot.message_handler(func=lambda message: message.text == "👑 Admin Panel")
def admin_panel(message):
    if message.from_user.id == ADMIN_ID or (message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.replace("@", "").lower()):
        admin_text = (
            f"👑 Admin Control & User Management Panel\n\n"
            f"Welcome Abhishek! Total Registered Users: {len(USERS)}\n"
            f"QR Status: {'Active (Available)' if QR_STATE['is_available'] else 'Inactive (Unavailable)'}\n"
            f"QR Image Set: {'Yes ✅' if QR_STATE['qr_image_id'] else 'No ❌'}\n\n"
            f"👇 Neeche buttons se QR ON/OFF karein ya Commands use karein:\n"
            f"• /ban <USER_ID>\n"
            f"• /unban <USER_ID>"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
            types.InlineKeyboardButton("📋 Pending Withdrawals", callback_data="admin_pending"),
            types.InlineKeyboardButton("🟢 Turn QR ON & Set QR", callback_data="admin_qr_on"),
            types.InlineKeyboardButton("🔴 Turn QR OFF", callback_data="admin_qr_off")
        )
        safe_send_message(message.chat.id, admin_text, reply_markup=markup)
    else:
        safe_send_message(message.chat.id, "⚠️ You are not authorized to access Admin Panel!")


@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        safe_send_message(message.chat.id, "⚠️ Sahi format use karein:\n`/ban <USER_ID>`")
        return
    try:
        target_id = int(args[1])
        user_data = get_user_data(target_id)
        user_data["banned"] = True
        safe_send_message(message.chat.id, f"✅ User ID {target_id} ko successfully Ban kar diya gaya hai.")
        safe_send_message(target_id, "❌ Aapko admin dwara is bot se ban kar diya gaya hai.")
    except Exception as e:
        safe_send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['unban'])
def unban_user_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        safe_send_message(message.chat.id, "⚠️ Sahi format use karein:\n`/unban <USER_ID>`")
        return
    try:
        target_id = int(args[1])
        user_data = get_user_data(target_id)
        user_data["banned"] = False
        safe_send_message(message.chat.id, f"✅ User ID {target_id} ko successfully Unban kar diya gaya hai.")
        safe_send_message(target_id, "✅ Aapka ban hata diya gaya hai! Ab aap bot use kar sakte hain.")
    except Exception as e:
        safe_send_message(message.chat.id, f"❌ Error: {e}")


@bot.callback_query_handler(func=lambda call: call.data in ["admin_stats", "admin_pending", "admin_qr_on", "admin_qr_off"])
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Unauthorized!", show_alert=True)
        return
        
    if call.data == "admin_stats":
        total_payouts = sum(len(h) for h in WITHDRAWALS_HISTORY.values())
        banned_count = sum(1 for u in USERS.values() if u.get("banned", False))
        stats_msg = (
            f"📊 BOT STATISTICS\n\n"
            f"👥 Total Users: {len(USERS)}\n"
            f"🚫 Banned Users: {banned_count}\n"
            f"💸 Payouts Processed: {total_payouts}\n"
            f"🎯 QR Status: {'Active' if QR_STATE['is_available'] else 'Inactive'}"
        )
        bot.answer_callback_query(call.id, "Fetching stats...")
        safe_send_message(call.message.chat.id, stats_msg)
        
    elif call.data == "admin_pending":
        total_pending = sum(len(v) for v in PENDING_WITHDRAWALS.values())
        bot.answer_callback_query(call.id, f"Pending: {total_pending}")
        safe_send_message(call.message.chat.id, f"📋 Pending Withdrawals: {total_pending}")
        
    elif call.data == "admin_qr_on":
        ADMIN_STATE[ADMIN_ID] = "waiting_for_qr_photo"
        bot.answer_callback_query(call.id, "Please send QR image now.")
        safe_send_message(
            call.message.chat.id, 
            "📸 QR Setup: Kripya ab apne naye QR Code ki photo (image) direct is chat mein bhein. Jaise hi aap photo bhejenge, QR automatically ON ho jayega aur users ko dikhne lagega."
        )
                              
    elif call.data == "admin_qr_off":
        QR_STATE["is_available"] = False
        ADMIN_STATE.pop(ADMIN_ID, None)
        bot.answer_callback_query(call.id, "QR tasks disabled! Users will see unavailable message.")
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text="👑 Admin Panel\n\nQR Status: Disabled (Unavailable)"
            )
        except Exception:
            pass


# ============================================================================
# SECTION 11: MAIN EXECUTION & POLLING LOOP
# ============================================================================

if __name__ == "__main__":
    print("Starting Keep-Alive Flask server for Render deployment...")
    keep_alive()
    
    print("Clearing old webhooks and pending updates...")
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as webhook_err:
        print(f"Webhook warning: {webhook_err}")
        
    # Set Bot Commands Menu (Adds "Start the bot" option on left menu icon)
    try:
        bot.set_my_commands([
            types.BotCommand("start", "Start the bot")
        ])
        print("Bot commands menu successfully set.")
    except Exception as cmd_err:
        print(f"Command menu error: {cmd_err}")

    print("ABHISHEKQRBOT is running smoothly and ready for production...")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
        except Exception as polling_error:
            print(f"Polling error encountered: {polling_error}")
            time.sleep(5)
