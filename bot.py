"""
=============================================================================
OFFICIAL ADVANCED TELEGRAM EARNING & QR TASK BOT
Developer / Owner: Abhishek (@abhishek723803)
Features: Dynamic Slab-Based QR Rewards, Admin Manual Screenshot Approval (Approve/Reject),
          User Ban/Unban Control, Toggle Sound Alerts, Referral System & Keep-Alive Flask.
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
    "min_withdrawal": 50.0
}

# In-Memory Data Storage Structures
USERS = {}
WITHDRAWALS_HISTORY = {}
TASK_HISTORY = {}
PENDING_WITHDRAWALS = {}
PENDING_APPROVALS = {}  # Stores admin verification mapping


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
            "notifications": True,
            "banned": False,  # User ban status flag
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "referred_by": None
        }
    return USERS[user_id]

def is_user_banned(user_id):
    """Check if a specific user is banned by admin."""
    user_data = get_user_data(user_id)
    return user_data.get("banned", False)

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
    """Wrapper function to handle message sending safely."""
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
    
    # Check if user is banned
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ **Access Denied:** Aapko admin dwara is bot se ban kar diya gaya hai.")
        return

    user_data = get_user_data(user_id)
    
    # Handle Referral Parameter Parsing
    args = message.text.split()
    if len(args) > 1 and user_data["referred_by"] is None:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id and not is_user_banned(referrer_id):
                user_data["referred_by"] = referrer_id
                referrer_data = get_user_data(referrer_id)
                referrer_data["referrals"] += 1
                referrer_data["balance"] += 1.0  # Joining bonus
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


# ==================== GET QR SECTION & HINGLISH AVAILABILITY CHECK ====================
@bot.message_handler(func=lambda message: message.text == "🎯 GET QR")
def handle_get_qr(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ Aapko ban kar diya gaya hai.")
        return

    user_data = get_user_data(user_id)
    
    # Check if QR is available in the bot system (Professional Hinglish message)
    if not QR_STATE["is_available"]:
        no_qr_text = (
            "❌ **Filhal Koi QR Available Nahi Hai!**\n\n"
            "Abhi is time par koi bhi active QR task available nahi hai. Kripya thodi der baad dobara try karein ya notification on rakhein taaki naya QR aate hi aap turant grab kar sakein!\n\n"
            f"🔔 Hamara official update channel join karein:\n🔗 {BOT_SETTINGS['channel_link']}"
        )
        safe_send_message(message.chat.id, no_qr_text, sound_enabled=user_data["notifications"])
        
    elif QR_STATE["is_claimed"]:
        claimed_text = (
            "⚠️ **Task Already Claimed**\n\n"
            "Oops! Yeh QR task pehle hi kisi aur user dwara claim kiya ja chuka hai. Kripya next fresh QR drop ke liye wait karein!\n\n"
            f"🔔 Hamara official update channel join karein:\n🔗 {BOT_SETTINGS['channel_link']}"
        )
        safe_send_message(message.chat.id, claimed_text, sound_enabled=user_data["notifications"])
        
    else:
        current_reward = get_current_rate(user_data["completed_tasks"])
        
        qr_text = (
            f"🎯 **QR TASK & CLAIM ZONE** 🎯\n\n"
            f"⚠️ **IMPORTANT INSTRUCTIONS:**\n"
            f"Live QR task available hai! Apna payment jaldi complete karke screenshot submit karein.\n\n"
            f"🎁 **Current Payout Rate:** ₹{current_reward}\n"
            f"⏳ **Status:** Active & Ready for Claim\n\n"
            f"Neeche diye gaye button par click karke payment details dekhein:"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Make Payment", callback_data="make_payment_action"))
        
        safe_send_message(message.chat.id, qr_text, reply_markup=markup, sound_enabled=user_data["notifications"])


# ==================== MAKE PAYMENT CALLBACK ====================
@bot.callback_query_handler(func=lambda call: call.data == "make_payment_action")
def ask_payment_proof(call):
    if is_user_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "You are banned!", show_alert=True)
        return

    if QR_STATE["is_claimed"]:
        bot.answer_callback_query(call.id, "Sorry! Yeh QR pehle hi claim ho chuka hai.", show_alert=True)
        return
    
    QR_STATE["is_claimed"] = True
    user_data = get_user_data(call.from_user.id)
    current_reward = get_current_rate(user_data["completed_tasks"])
    
    proof_text = (
        f"✅ **QR Successfully Claimed!**\n\n"
        f"🎁 **Reward Payout:** ₹{current_reward}\n"
        f"⏳ Aapke paas 4 minute hain transaction complete karne ke liye.\n\n"
        f"💳 **Instructions:**\n"
        f"QR scan karke payment karein aur apne payment ka screenshot (photo) direct is chat mein upload karein."
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


# ==================== SCREENSHOT SUBMISSION & ADMIN FORWARDING ====================
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        safe_send_message(message.chat.id, "❌ Aapko ban kiya gaya hai, screenshot accept nahi hoga.")
        return

    user_data = get_user_data(user_id)
    
    # Calculate expected reward
    current_task_num = user_data["completed_tasks"] + 1
    reward = get_task_reward(current_task_num)
    
    # Reset claim status so other users can grab new tasks if available
    QR_STATE["is_claimed"] = False
    
    # Forward screenshot to Admin for manual review (Approve / Reject)
    photo_file_id = message.photo[-1].file_id
    admin_caption = (
        f"📸 **New Payment Proof Submitted!**\n\n"
        f"👤 User: @{message.from_user.username if message.from_user.username else 'NoUsername'}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📋 Task Number: #{current_task_num}\n"
        f"🎁 Reward Amount: ₹{reward}\n\n"
        f"Kripya payment receipt check karke neeche se action lein:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{reward}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )
    
    try:
        sent_admin_msg = bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_caption, reply_markup=markup, parse_mode="Markdown")
        PENDING_APPROVALS[sent_admin_msg.message_id] = {"user_id": user_id, "reward": reward}
    except Exception as e:
        print(f"Failed to forward screenshot to admin: {e}")
    
    submission_text = (
        f"📥 **Screenshot Successfully Submitted!**\n\n"
        f"Aapka payment screenshot admin ke paas verification ke liye bhej diya gaya hai.\n"
        f"⏳ Jaise hi admin ise approve karenge, aapke wallet mein paise turant add kar diye jayenge."
    )
    safe_send_message(message.chat.id, submission_text, sound_enabled=user_data["notifications"])


# ==================== ADMIN APPROVAL / REJECTION HANDLER ====================
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
        user_data["balance"] += reward  # Balance is credited ONLY upon admin approval
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if user_id not in TASK_HISTORY:
            TASK_HISTORY[user_id] = []
        TASK_HISTORY[user_id].append(f"Task #{current_task_num} - ₹{reward} ({timestamp})")
        
        bot.answer_callback_query(call.id, f"Approved! ₹{reward} user ke wallet mein credit ho gaye.")
        
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + f"\n\n✅ **STATUS: APPROVED BY ADMIN** (₹{reward} Credited)",
                parse_mode="Markdown"
            )
        except Exception:
            pass
            
        # Notify User
        success_user_msg = (
            f"✅ **Payment Approved by Admin!**\n\n"
            f"🎁 **Reward Added (Task #{current_task_num}):** ₹{reward}\n"
            f"📋 **Total Completed QRs:** {current_task_num}\n"
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
            
        # Notify User (Money NOT credited)
        reject_user_msg = (
            f"❌ **Payment Proof Rejected**\n\n"
            f"Aapka submitted payment screenshot admin dwara reject kar diya gaya hai kyunki yeh invalid ya mismatch tha."
        )
        safe_send_message(user_id, reject_user_msg, sound_enabled=user_data["notifications"])


# ==================== STANDARD BOT SECTIONS ====================
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
        f"• 10 to 20 QRs: ₹20 per QR\n"
        f"• 20 to 30 QRs & above: ₹25 per QR"
    )
    safe_send_message(message.chat.id, balance_content, sound_enabled=user_data["notifications"])


@bot.message_handler(func=lambda message: message.text == "👤 My Account")
def my_account(message):
    if is_user_banned(message.from_user.id): return
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
            text=f"✅ **Withdrawal Request Submitted Successfully!**\n\nAmount: ₹{amount}\nStatus: Processing\nAapka payout jald hi aapke account mein bhej diya jayega.",
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
        f"👥 **REFERRAL PROGRAM**\n\n"
        f"💰 **BENEFITS:**\n"
        f"• Har ek naye referral par turant ₹1.00 joining bonus paayein!\n\n"
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


# ==================== ADVANCED ADMIN PANEL WITH USER CONTROL (BAN/UNBAN) ====================
@bot.message_handler(func=lambda message: message.text == "👑 Admin Panel")
def admin_panel(message):
    if message.from_user.id == ADMIN_ID or (message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.replace("@", "").lower()):
        admin_text = (
            f"👑 **Admin Control & User Management Panel**\n\n"
            f"Welcome Abhishek! Total Registered Users: {len(USERS)}\n"
            f"QR Status: {'Active (Available)' if QR_STATE['is_available'] else 'Inactive (Unavailable)'}\n\n"
            f"👇 Kisi bhi user ko Ban ya Unban karne ke liye neeche diye gaye commands use karein:\n"
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


# Admin Commands for Banning and Unbanning Users
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
        bot.answer_callback_query(call.id, "QR tasks enabled!")
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="👑 **Admin Panel**\n\nQR Status: **Enabled (Available)**", parse_mode="Markdown")
        except Exception:
            pass
                              
    elif call.data == "admin_qr_off":
        QR_STATE["is_available"] = False
        bot.answer_callback_query(call.id, "QR tasks disabled!")
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="👑 **Admin Panel**\n\nQR Status: **Disabled (Unavailable)**", parse_mode="Markdown")
        except Exception:
            pass


# ==================== MAIN EXECUTION & POLLING ====================
if __name__ == "__main__":
    print("Starting Keep-Alive Flask server for Render deployment...")
    keep_alive()
    
    print("Clearing old webhooks and pending updates...")
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as webhook_err:
        print(f"Webhook warning: {webhook_err}")
        
    print("Telegram Bot is running smoothly...")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
        except Exception as polling_error:
            print(f"Polling error: {polling_error}")
            time.sleep(5)
