"""
=============================================================================
OFFICIAL ABHISHEKQRBOT - ADVANCED EARNING & QR TASK BOT (FINAL FIXED EDITION)
Developer / Owner: Abhishek (@abhishek723803)
Description: Telegram bot with Force Join verification, dynamic QR availability,
             direct referral bonus (₹1.00), dynamic slabs, and admin approvals.
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
    "is_available": False,  # Default False: QR tabhi dikhega jab aap Admin Panel se ON karoge
    "is_claimed": False     # Tracks if current active QR is claimed
}

BOT_SETTINGS = {
    "channel_link": "https://t.me/+757WqqqLLoo4Yjhl",
    "min_withdrawal": 50.0
}

# In-Memory Database Structures
USERS = {}
WITHDRAWALS_HISTORY = {}
TASK_HISTORY = {}
PENDING_WITHDRAWALS = {}
PENDING_APPROVALS = {}
VERIFIED_USERS = set()  # Tracks users who completed Force Join


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

def get_task_reward(task_number):
    """
    Dynamic Slab-Based Reward Calculator:
    - Task 1 to 10: ₹15 per QR
    - Task 11 to 20: ₹20 per QR
    - Task 21 to 30 and above: ₹25 per QR
    """
    if task_number <= 10:
        return 15.0
    elif task_number <= 20:
        return 20.0
    else:
        return 25.0

def get_current_rate(completed_tasks):
    next_task = completed_tasks + 1
    if next_task <= 10:
        return 15.0
    elif next_task <= 20:
        return 20.0
    else:
        return 25.0

def safe_send_message(chat_id, text, reply_markup=None, parse_mode="Markdown", sound_enabled=True):
    try:
        return bot.send_message(
            chat_id, 
            text, 
            reply_markup=reply_markup, 
            parse_mode=parse_mode,
            disable_notification=not sound_enabled,
            disable_web_page_preview=True
        )
    except Exception as error_msg:
        print(f"Error sending message to {chat_id}: {error_msg}")
        return None


# ============================================================================
# SECTION 4: /START COMMAND & FORCE JOIN VERIFICATION SYSTEM
# ============================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ **Access Denied:** Aapko admin dwara is bot se ban kar diya gaya hai.")
        return

    user_data = get_user_data(user_id)
    
    # Process Direct Referral & ₹1.00 Joining Bonus
    args = message.text.split()
    if len(args) > 1 and user_data["referred_by"] is None:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id and not is_user_banned(referrer_id):
                user_data["referred_by"] = referrer_id
                referrer_data = get_user_data(referrer_id)
                referrer_data["referrals"] += 1
                referrer_data["balance"] += 1.0  # ₹1.00 Direct Joining Bonus
                
                safe_send_message(
                    referrer_id, 
                    f"🎉 **New Referral Joined!**\n\nUser ID `{user_id}` joined using your link. ₹1.00 direct joining bonus added to your wallet!", 
                    sound_enabled=referrer_data["notifications"]
                )
        except Exception as ref_err:
            print(f"Referral error: {ref_err}")

    # Check Force Join Status
    if user_id not in VERIFIED_USERS:
        force_join_markup = types.InlineKeyboardMarkup(row_width=1)
        force_join_markup.add(
            types.InlineKeyboardButton("📢 Join Update Channel", url=BOT_SETTINGS["channel_link"]),
            types.InlineKeyboardButton("✅ Joined & Start Bot", callback_data="verify_force_join")
        )
        join_msg = (
            f"⚠️ **Channel Join Required!**\n\n"
            f"Welcome to **{BOT_NAME}** 🤖\n"
            f"Bot ko use karne ke liye sabse pehle hamara official update channel join karna zaroori hai.\n\n"
            f"👇 Neeche diye gaye button par click karke channel join karein aur phir 'Joined & Start Bot' par click karein:"
        )
        safe_send_message(message.chat.id, join_msg, reply_markup=force_join_markup)
        return

    # If already verified, show main menu
    show_main_menu(message.chat.id, message.from_user.first_name, user_data["notifications"])


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
    show_main_menu(call.message.chat.id, call.from_user.first_name, user_data["notifications"])


def show_main_menu(chat_id, first_name, sound_enabled):
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
    
    welcome_text = (
        f"👋 Welcome, **{first_name}** to **{BOT_NAME}**!\n\n"
        f"🤖 Aapka swagat hai hamare official Automated Earning & QR Task Bot mein.\n"
        f"Yahan aap fast scanning tasks complete karke, dynamic slabs ke through rewards earn kar sakte hain aur dosto ko invite karke direct bonus pa sakte hain.\n\n"
        f"👇 Neeche menu se koi bhi option chunein:"
    )
    safe_send_message(chat_id, welcome_text, reply_markup=markup, sound_enabled=sound_enabled)


# ============================================================================
# SECTION 5: "GET QR" SECTION (STRICT AVAILABILITY CONTROL)
# ============================================================================

@bot.message_handler(func=lambda message: message.text == "🎯 GET QR")
def handle_get_qr(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ Aapko ban kar diya gaya hai.")
        return

    user_data = get_user_data(user_id)
    
    # Strict Check: If Admin has NOT added/enabled QR, show unavailable message
    if not QR_STATE["is_available"]:
        no_qr_text = (
            "❌ **QR abhi available nahi hai!**\n\n"
            "Keep trying for next time! 🚀 Naya QR task aate hi aapko update mil jayega."
        )
        safe_send_message(message.chat.id, no_qr_text, sound_enabled=user_data["notifications"])
        
    elif QR_STATE["is_claimed"]:
        claimed_text = (
            "⚠️ **Task Already Claimed**\n\n"
            "Oops! Yeh QR task pehle hi kisi aur user dwara claim kiya ja chuka hai. Kripya next fresh QR drop ke liye wait karein!"
        )
        safe_send_message(message.chat.id, claimed_text, sound_enabled=user_data["notifications"])
        
    else:
        current_reward = get_current_rate(user_data["completed_tasks"])
        qr_text = (
            f"🎯 **QR TASK & CLAIM ZONE** 🎯\n\n"
            f"🎁 **Reward:** ₹{current_reward}\n\n"
            f"📌 **Instructions:**\n"
            f"1️⃣ Neeche 'Make Payment' button par click karein.\n"
            f"2️⃣ QR scan karke payment complete karein.\n"
            f"3️⃣ Payment ka screenshot (photo) direct is chat mein bhej dein.\n\n"
            f"Tap the button below to proceed:"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Make Payment", callback_data="make_payment_action"))
        
        safe_send_message(message.chat.id, qr_text, reply_markup=markup, sound_enabled=user_data["notifications"])


# ============================================================================
# SECTION 6: PAYMENT & SCREENSHOT SUBMISSION
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
    current_reward = get_current_rate(user_data["completed_tasks"])
    
    proof_text = (
        f"✅ **QR Successfully Claimed!**\n\n"
        f"🎁 **Reward Payout:** ₹{current_reward}\n"
        f"⏳ Aapke paas time hai payment complete karne ke liye.\n\n"
        f"💳 **Action:** QR scan karke payment karein aur screenshot direct is chat mein upload karein."
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


@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ Aapko ban kiya gaya hai, screenshot accept nahi hoga.")
        return

    user_data = get_user_data(user_id)
    current_task_num = user_data["completed_tasks"] + 1
    reward = get_task_reward(current_task_num)
    
    QR_STATE["is_claimed"] = False
    
    photo_file_id = message.photo[-1].file_id
    admin_caption = (
        f"📸 **New Payment Proof Submitted!**\n\n"
        f"👤 User Name: {message.from_user.first_name}\n"
        f"🔖 Username: @{message.from_user.username if message.from_user.username else 'NoUsername'}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📋 Task Number: #{current_task_num}\n"
        f"🎁 Reward Amount: ₹{reward}\n\n"
        f"Kripya receipt check karke approve ya reject karein:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{reward}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )
    
    try:
        sent_admin_msg = bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_caption, reply_markup=markup, parse_mode="Markdown")
        PENDING_APPROVALS[sent_admin_msg.message_id] = {"user_id": user_id, "reward": reward}
    except Exception as img_err:
        print(f"Error forwarding screenshot to admin: {img_err}")
    
    submission_text = (
        f"📥 **Screenshot Successfully Submitted!**\n\n"
        f"Aapka payment screenshot admin ke paas verification ke liye bhej diya gaya hai.\n"
        f"⏳ Jaise hi admin approval denge, tabhi aapke wallet mein paise add honge."
    )
    safe_send_message(message.chat.id, submission_text, sound_enabled=user_data["notifications"])


# ============================================================================
# SECTION 7: ADMIN APPROVAL / REJECTION
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
        reward = float(data_parts[2])
        user_data["completed_tasks"] += 1
        current_task_num = user_data["completed_tasks"]
        user_data["balance"] += reward  # Wallet balance credited only upon admin approval
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if user_id not in TASK_HISTORY:
            TASK_HISTORY[user_id] = []
        TASK_HISTORY[user_id].append(f"Task #{current_task_num} - ₹{reward} ({timestamp})")
        
        bot.answer_callback_query(call.id, f"Approved! ₹{reward} credited successfully.")
        
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + f"\n\n✅ **STATUS: APPROVED BY ADMIN** (₹{reward} Credited)",
                parse_mode="Markdown"
            )
        except Exception:
            pass
            
        success_user_msg = (
            f"✅ **Payment Approved by Admin!**\n\n"
            f"🎁 **Reward Added (Task #{current_task_num}):** ₹{reward}\n"
            f"💰 **Updated Wallet Balance:** ₹{user_data['balance']}\n\n"
            f"🎉 Badhai ho! Aise hi aur tasks complete karte rahein."
        )
        safe_send_message(user_id, success_user_msg, sound_enabled=user_data["notifications"])
        
    elif action == "reject":
        bot.answer_callback_query(call.id, "Payment proof reject kar diya gaya hai.")
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + f"\n\n❌ **STATUS: REJECTED BY ADMIN**",
                parse_mode="Markdown"
            )
        except Exception:
            pass
            
        reject_user_msg = (
            f"❌ **Payment Proof Rejected**\n\n"
            f"Aapka submitted payment screenshot admin dwara reject kar diya gaya hai."
        )
        safe_send_message(user_id, reject_user_msg, sound_enabled=user_data["notifications"])


# ============================================================================
# SECTION 8: REMAINING MENU BUTTON HANDLERS
# ============================================================================

@bot.message_handler(func=lambda message: message.text == "💰 My Balance")
def my_balance(message):
    if is_user_banned(message.from_user.id): return
    user_data = get_user_data(message.from_user.id)
    next_rate = get_current_rate(user_data["completed_tasks"])
    
    balance_content = (
        f"💰 **YOUR WALLET & EARNING TIERS** 💰\n\n"
        f"🏦 Available Balance: ₹{user_data['balance']}\n"
        f"⭐ Active Payout Rate: ₹{next_rate} / QR\n"
        f"🏧 Minimum Withdrawal: ₹{BOT_SETTINGS['min_withdrawal']}\n\n"
        f"📊 **Dynamic Slab Reward Structure:**\n"
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
    
    account_info = (
        f"👤 **YOUR ACCOUNT PROFILE**\n\n"
        f"📌 **Name:** {message.from_user.first_name}\n"
        f"🔖 **Username:** @{message.from_user.username if message.from_user.username else 'None'}\n"
        f"🆔 **Telegram ID:** `{user_id}`\n\n"
        f"🏦 Wallet Balance: ₹{user_data['balance']}\n"
        f"📋 Completed QRs: {user_data['completed_tasks']}\n"
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
            f"❌ **Insufficient Balance.**\n\nAapka current balance ₹{user_data['balance']} hai.\nMinimum withdrawal limit ₹{BOT_SETTINGS['min_withdrawal']} honi chahiye.",
            sound_enabled=user_data["notifications"]
        )
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Withdraw to UPI / Paytm", callback_data="process_withdraw"))
        withdraw_text = (
            f"💸 **WITHDRAWAL SECTION**\n\n"
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
            text=f"✅ **Withdrawal Request Submitted Successfully!**\n\nAmount: ₹{amount}\nStatus: Processing",
            parse_mode="Markdown"
        )
    except Exception:
        safe_send_message(call.message.chat.id, "✅ Withdrawal Request Submitted Successfully!")


@bot.message_handler(func=lambda message: message.text == "📜 Withdrawal History")
def withdrawal_history(message):
    if is_user_banned(message.from_user.id): return
    user_id = message.from_user.id
    history = WITHDRAWALS_HISTORY.get(user_id, [])
    
    history_content = f"📜 **WITHDRAWAL HISTORY**\n\n🆔 Telegram ID: `{user_id}`\n\n"
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
        f"👥 **REFERRAL PROGRAM & DIRECT BONUS**\n\n"
        f"💰 **BENEFIT:**\n"
        f"• **Direct Joining Bonus:** Har ek naye referral ke join hone par turant ₹1.00 direct bonus paayein!\n\n"
        f"🔗 **Aapka Referral Link:**\n`{ref_link}`"
    )
    safe_send_message(message.chat.id, invite_text, sound_enabled=get_user_data(message.from_user.id)["notifications"])


@bot.message_handler(func=lambda message: message.text == "📋 Task History")
def task_history(message):
    if is_user_banned(message.from_user.id): return
    user_id = message.from_user.id
    tasks = TASK_HISTORY.get(user_id, [])
    
    if not tasks:
        task_text = "📋 **TASK HISTORY**\n\nAbhi tak koi bhi completed task nahi hai."
    else:
        task_text = "📋 **COMPLETED TASK HISTORY**\n\n" + "\n".join(f"• {t}" for t in tasks[-15:])
        
    safe_send_message(message.chat.id, task_text, sound_enabled=get_user_data(user_id)["notifications"])


@bot.message_handler(func=lambda message: message.text == "🔔 Toggle Notification")
def toggle_notification(message):
    if is_user_banned(message.from_user.id): return
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    user_data["notifications"] = not user_data["notifications"]
    
    status_desc = "Enabled 🔊" if user_data["notifications"] else "Disabled 🔕"
    safe_send_message(message.chat.id, f"🔔 **Notification Settings**\n\nStatus: **{status_desc}**", sound_enabled=user_data["notifications"])


@bot.message_handler(func=lambda message: message.text == "🛠 Support")
def support(message):
    if is_user_banned(message.from_user.id): return
    support_text = (
        f"🛠 **CUSTOMER SUPPORT DESK**\n\n"
        f"👑 Owner Username: {ADMIN_USERNAME}\n"
        f"⏰ Timing: 10:00 AM - 10:00 PM\n\n"
        f"Payment ya withdrawal mein koi bhi problem ho toh admin se contact karein."
    )
    safe_send_message(message.chat.id, support_text, sound_enabled=get_user_data(message.from_user.id)["notifications"])


# ============================================================================
# SECTION 9: EXCLUSIVE ADMIN PANEL & BAN/UNBAN COMMANDS
# ============================================================================

@bot.message_handler(func=lambda message: message.text == "👑 Admin Panel")
def admin_panel(message):
    if message.from_user.id == ADMIN_ID or (message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.replace("@", "").lower()):
        admin_text = (
            f"👑 **Admin Control & User Management Panel**\n\n"
            f"Welcome Abhishek! Total Registered Users: {len(USERS)}\n"
            f"QR Status: {'Active (Available)' if QR_STATE['is_available'] else 'Inactive (Unavailable)'}\n\n"
            f"👇 Kisi bhi user ko Ban ya Unban karne ke liye commands use karein:\n"
            f"• `/ban <USER_ID>`\n"
            f"• `/unban <USER_ID>`"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
            types.InlineKeyboardButton("📋 Pending Withdrawals", callback_data="admin_pending"),
            types.InlineKeyboardButton("🟢 Turn QR ON", callback_data="admin_qr_on"),
            types.InlineKeyboardButton("🔴 Turn QR OFF", callback_data="admin_qr_off")
        )
        safe_send_message(message.chat.id, admin_text, reply_markup=markup)
    else:
        safe_send_message(message.chat.id, "❌ Aap admin nahi hain!")


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
        safe_send_message(message.chat.id, f"✅ User ID `{target_id}` ko successfully **Ban** kar diya gaya hai.")
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
        safe_send_message(message.chat.id, f"✅ User ID `{target_id}` ko successfully **Unban** kar diya gaya hai.")
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
            f"📊 **BOT STATISTICS**\n\n"
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
        safe_send_message(call.message.chat.id, f"📋 **Pending Withdrawals:** {total_pending}")
        
    elif call.data == "admin_qr_on":
        QR_STATE["is_available"] = True
        QR_STATE["is_claimed"] = False
        bot.answer_callback_query(call.id, "QR tasks enabled! Users can now claim.")
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="👑 **Admin Panel**\n\nQR Status: **Enabled (Available)**", parse_mode="Markdown")
        except Exception:
            pass
                              
    elif call.data == "admin_qr_off":
        QR_STATE["is_available"] = False
        bot.answer_callback_query(call.id, "QR tasks disabled! Users will see unavailable message.")
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="👑 **Admin Panel**\n\nQR Status: **Disabled (Unavailable)**", parse_mode="Markdown")
        except Exception:
            pass


# ============================================================================
# SECTION 10: MAIN EXECUTION & POLLING LOOP
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
        
    print("ABHISHEKQRBOT is running smoothly and ready for production...")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
        except Exception as polling_error:
            print(f"Polling error encountered: {polling_error}")
            time.sleep(5)
