import os
import sqlite3
import threading
from flask import Flask
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ==================== CONFIGURATION ====================
API_TOKEN = '8513419896:AAFMs-OxnZE7OjWjPK8gt34cMU9Z5-w1_2E'  # Bot Token
ADMIN_ID = 8411871478  # Main Admin Telegram ID

DIRECT_JOIN_BONUS = 1.0  # Per Direct Referral Bonus (₹1.00)
TASK_COMMISSION_PERCENT = 0.10  # 10% Referral Task Commission
MIN_WITHDRAWAL = 10.0  # Minimum Withdrawal Limit
DEFAULT_CHANNEL_LINK = 'https://t.me/+757WqqqLLoo4Yjhl'  # Official Channel Link
# =======================================================

bot = telebot.TeleBot(API_TOKEN)

try:
  bot.remove_webhook()
except Exception as e:
  print(f'Webhook note: {e}')


# ==================== FLASK WEB SERVER (RENDER 24/7 FIX) ====================
app = Flask('')


@app.route('/')
def home():
  return 'Abhishek QR Bot is active and running 24/7!'


def run_web():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


# ==================== DATABASE HELPER (LOCK-PROOF) ====================
def get_db_connection():
  conn = sqlite3.connect(
      'bot_database.db', timeout=60.0, check_same_thread=False
  )
  conn.execute('PRAGMA journal_mode=WAL;')  # Prevents disk I/O lock issues
  return conn


def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        balance REAL DEFAULT 0.0,
        total_rewards REAL DEFAULT 0.0,
        total_withdrawn REAL DEFAULT 0.0,
        referred_by INTEGER,
        total_invited INTEGER DEFAULT 0,
        is_blocked INTEGER DEFAULT 0,
        notifications_enabled INTEGER DEFAULT 1
    )
    ''')

  try:
    cursor.execute(
        'ALTER TABLE users ADD COLUMN notifications_enabled INTEGER DEFAULT 1'
    )
    conn.commit()
  except Exception:
    pass

  cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_num INTEGER,
        reward REAL,
        status TEXT DEFAULT 'Approved'
    )
    ''')

  cursor.execute('''
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        upi_id TEXT,
        status TEXT DEFAULT 'Pending'
    )
    ''')

  cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

  cursor.execute(
      'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
      ('channel_link', DEFAULT_CHANNEL_LINK),
  )
  conn.commit()
  conn.close()


init_db()


# ==================== HELPER FUNCTIONS ====================
def get_setting(key, default=''):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
  row = cursor.fetchone()
  conn.close()
  return row[0] if row else default


def set_setting(key, value):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value)
  )
  conn.commit()
  conn.close()


def get_main_menu(user_id):
  markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
  markup.add(
      KeyboardButton('🎯 GET QR'),
      KeyboardButton('💰 My Balance'),
      KeyboardButton('👤 My Account'),
      KeyboardButton('💸 Withdraw Money'),
      KeyboardButton('📜 Withdrawal History'),
      KeyboardButton('🤝 Invite & Earn'),
      KeyboardButton('📋 Task History'),
      KeyboardButton('🔔 Toggle Notification'),
      KeyboardButton('🛠 Support'),
  )
  if user_id == ADMIN_ID:
    markup.add(KeyboardButton('👑 Admin Panel'))
  return markup


def get_admin_inline_keyboard():
  markup = InlineKeyboardMarkup(row_width=2)
  markup.add(
      InlineKeyboardButton(
          '📊 Bot Statistics', callback_data='admin_stats'
      ),
      InlineKeyboardButton(
          '💸 Pending Withdrawals', callback_data='admin_pending_w'
      ),
      InlineKeyboardButton('🎯 Approve Task', callback_data='admin_add_task'),
      InlineKeyboardButton(
          '🚫 Block/Unblock User', callback_data='admin_toggle_block'
      ),
      InlineKeyboardButton(
          '⚡ Broadcast QR Alert', callback_data='admin_qr_broadcast'
      ),
      InlineKeyboardButton(
          '📢 General Broadcast', callback_data='admin_broadcast'
      ),
      InlineKeyboardButton('🔗 Update Channel', callback_data='admin_set_chan'),
  )
  return markup


def get_or_create_user(user, referrer_id=None):
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute('SELECT * FROM users WHERE user_id = ?', (user.id,))
  data = cursor.fetchone()

  if not data:
    ref_by = (
        int(referrer_id)
        if referrer_id
        and str(referrer_id).isdigit()
        and int(referrer_id) != user.id
        else None
    )

    cursor.execute(
        'INSERT INTO users (user_id, first_name, username, balance,'
        ' total_rewards, total_withdrawn, referred_by, total_invited,'
        ' is_blocked, notifications_enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0,'
        ' 1)',
        (
            user.id,
            user.first_name,
            user.username or 'Not Set',
            0.0,
            0.0,
            0.0,
            ref_by,
            0,
        ),
    )
    conn.commit()

    if ref_by:
      cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (ref_by,))
      if cursor.fetchone():
        cursor.execute(
            'UPDATE users SET balance = balance + ?, total_rewards ='
            ' total_rewards + ?, total_invited = total_invited + 1 WHERE'
            ' user_id = ?',
            (DIRECT_JOIN_BONUS, DIRECT_JOIN_BONUS, ref_by),
        )
        conn.commit()
        try:
          bot.send_message(
              ref_by,
              '🎉 *NEW REFERRAL JOINED!*\n'
              '━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
              f'Aapke link se naye user (`{user.first_name}`) ne bot start kiya'
              ' hai!\n'
              f'Aapko **₹{DIRECT_JOIN_BONUS:.2f}** Direct Bonus mil gaya hai!',
              parse_mode='Markdown',
          )
        except Exception:
          pass

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user.id,))
    data = cursor.fetchone()

  conn.close()
  return data


def is_user_blocked(user_id):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_blocked FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] == 1 if row else False
  except Exception as e:
    print(f'Error checking block status: {e}')
    return False


# ==================== USER HANDLERS ====================


@bot.message_handler(commands=['start'])
def start_cmd(message):
  if is_user_blocked(message.from_user.id):
    bot.send_message(
        message.chat.id,
        '🚫 *Aapka account block kar diya gaya hai!*',
        parse_mode='Markdown',
    )
    return

  args = message.text.split()
  ref_id = args[1] if len(args) > 1 else None
  get_or_create_user(message.from_user, ref_id)

  welcome_msg = """👋 *Welcome to ABHISHEK QR BOT!* 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━
Aapka hamare official QR Earning platform par swagat hai!

👇 *Key Features:*
• 🎯 **QR Tasks:** Fast QR scans karke instant earning karein.
• 🤝 **Referral System:** Per refer **₹1.00 Direct Bonus** + **10% Task Commission**!
• 💸 **Instant Withdraw:** Direct UPI / FamPay me payout!
• 🔔 **Instant Task Alerts:** Direct QR notification pane ke liye Toggle Notification ON rakhein!"""

  bot.send_message(
      message.chat.id,
      welcome_msg,
      reply_markup=get_main_menu(message.from_user.id),
      parse_mode='Markdown',
  )


@bot.message_handler(func=lambda m: m.text == '🎯 GET QR')
def get_qr_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  channel_link = get_setting('channel_link', DEFAULT_CHANNEL_LINK)

  text = f"""🎯 *QR TASK & CLAIM ZONE* 🎯
━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *IMPORTANT NOTICE:*
Live QR tasks limited time ke liye aate hain.

📌 *Rules:*
1️⃣ Get QR par tap karein.
2️⃣ QR Active hone par hi payment claim hogi.

🔔 *LIVE QR ALERTS:*
Naye QR tasks ke alerts pane ke liye official channel join karein:
📢 **Official Channel:** {channel_link}

⚡ *Agla QR Task Jald Hi Aayega! Keep Checking!* ⚡"""

  bot.send_message(
      message.chat.id,
      text,
      parse_mode='Markdown',
      disable_web_page_preview=True,
  )


@bot.message_handler(func=lambda m: m.text == '💰 My Balance')
def balance_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  u_data = get_or_create_user(message.from_user)
  bal = u_data[3]

  text = f"""💰 *YOUR WALLET & TASK STATUS* 💰
━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 *Available Balance:* **₹{bal:.2f}**
📌 *Per Task Rate:* **₹10.00 / QR**

🏧 *Minimum Withdrawal Limit:* **₹{MIN_WITHDRAWAL:.2f}**"""
  bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '👤 My Account')
def account_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  u_data = get_or_create_user(message.from_user)
  u_id, name, uname, bal, rewards, withdrawn, _, total_invited, _, notif = (
      u_data
  )
  uname_str = f'@{uname}' if uname and uname != 'Not Set' else 'Not Set'
  notif_status = '🔔 ON' if notif == 1 else '🔕 OFF'

  text = f"""👤 *YOUR ACCOUNT PROFILE* 👤
━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 *Name:* {name}
✨ *Username:* {uname_str}
🆔 *Telegram ID:* `{u_id}`

💵 *Available Balance:* **₹{bal:.2f}**
🎁 *Total Rewards Earned:* **₹{rewards:.2f}**
🪙 *Total Withdrawn:* **₹{withdrawn:.2f}**
👥 *Total Invited:* **{total_invited} Users**
📢 *Task Notifications:* **{notif_status}**"""
  bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(
    func=lambda m: m.text in ['🔔 Toggle Notification', '🔔 Notifications']
)
def toggle_notification_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  user_id = message.from_user.id

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT notifications_enabled FROM users WHERE user_id = ?', (user_id,)
  )
  row = cursor.fetchone()

  current_status = row[0] if row else 1
  new_status = 0 if current_status == 1 else 1

  cursor.execute(
      'UPDATE users SET notifications_enabled = ? WHERE user_id = ?',
      (new_status, user_id),
  )
  conn.commit()
  conn.close()

  if new_status == 1:
    msg = (
        '🔔 *Task Notifications Turned ON!*\nAapko ab live QR tasks ke instant'
        ' alerts milenge.'
    )
  else:
    msg = (
        '🔕 *Task Notifications Turned OFF!*\nAapko instant task alerts nahi'
        ' milenge.'
    )

  bot.send_message(message.chat.id, msg, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '💸 Withdraw Money')
def withdraw_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  u_data = get_or_create_user(message.from_user)
  bal = u_data[3]

  text = f"""💸 *WITHDRAWAL SECTION* 💸
━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 *Current Balance:* **₹{bal:.2f}**
🏧 *Minimum Withdrawal:* **₹{MIN_WITHDRAWAL:.2f}**

👇 *Apna UPI ID enter karke request submit karein (Example: `name@upi`):*"""

  if bal < MIN_WITHDRAWAL:
    bot.send_message(
        message.chat.id,
        f'{text}\n\n❌ *Aapka balance ₹{MIN_WITHDRAWAL:.2f} se kam hai.*',
        parse_mode='Markdown',
    )
    return

  msg = bot.send_message(message.chat.id, text, parse_mode='Markdown')
  bot.register_next_step_handler(msg, process_withdrawal, bal)


def process_withdrawal(message, user_bal):
  upi_id = message.text.strip()
  user = message.from_user

  if '@' not in upi_id:
    bot.send_message(
        message.chat.id, '❌ Invalid UPI ID! Request cancel kar di gayi hai.'
    )
    return

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'UPDATE users SET balance = balance - ? WHERE user_id = ?',
      (user_bal, user.id),
  )
  cursor.execute(
      'INSERT INTO withdrawals (user_id, amount, upi_id) VALUES (?, ?, ?)',
      (user.id, user_bal, upi_id),
  )
  conn.commit()
  withdraw_id = cursor.lastrowid
  conn.close()

  bot.send_message(
      message.chat.id,
      f'✅ *Withdrawal Request Submitted!*\n💵 Amount: ₹{user_bal:.2f}\n💳 UPI'
      f' ID: `{upi_id}`\n📌 Status: Pending Admin Approval',
      parse_mode='Markdown',
  )

  # Admin Real-time Control
  admin_alert = f"""🔔 *NEW WITHDRAWAL REQUEST* 🔔
━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 *Req ID:* #{withdraw_id}
👤 *User:* {user.first_name} (`{user.id}`)
💵 *Amount:* **₹{user_bal:.2f}**
💳 *UPI ID:* `{upi_id}`"""

  btn_markup = InlineKeyboardMarkup(row_width=2)
  btn_markup.add(
      InlineKeyboardButton(
          '✅ Approve', callback_data=f'w_approve_{withdraw_id}'
      ),
      InlineKeyboardButton(
          '❌ Reject', callback_data=f'w_reject_{withdraw_id}'
      ),
  )
  btn_markup.add(
      InlineKeyboardButton(
          '🚫 Block User', callback_data=f'u_block_{user.id}'
      )
  )

  try:
    bot.send_message(
        ADMIN_ID, admin_alert, reply_markup=btn_markup, parse_mode='Markdown'
    )
  except Exception as e:
    print(f'Admin alert error: {e}')


@bot.message_handler(
    func=lambda m: m.text in ['📜 Withdrawal History', '📑 Withdrawal History']
)
def withdraw_history_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  user_id = message.from_user.id

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT amount, upi_id, status FROM withdrawals WHERE user_id = ? ORDER'
      ' BY id DESC LIMIT 5',
      (user_id,),
  )
  records = cursor.fetchall()
  conn.close()

  history_text = (
      f'📜 *WITHDRAWAL HISTORY* 📜\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🆔 *User ID:*'
      f' `{user_id}`\n\n'
  )
  if not records:
    history_text += 'Abhi tak koi withdrawal record nahi hai.\n'
  else:
    for r in records:
      icon = (
          '✅'
          if r[2] == 'Approved'
          else ('❌' if r[2] == 'Rejected' else '⏳')
      )
      history_text += (
          f'{icon} *Amount:* ₹{r[0]:.2f} | *UPI:* `{r[1]}` | *Status:* {r[2]}\n'
      )
  bot.send_message(message.chat.id, history_text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '🤝 Invite & Earn')
def invite_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  u_data = get_or_create_user(message.from_user)
  total_invited = u_data[7]

  try:
    bot_uname = bot.get_me().username
  except Exception:
    bot_uname = 'ABHISHEK_QR_TOP_BOT'

  ref_link = f'https://t.me/{bot_uname}?start={message.from_user.id}'

  text = f"""💸 *Invite & Earn Rules:*
━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 *EARNINGS:*
1️⃣ **Direct Join Bonus:** **₹{DIRECT_JOIN_BONUS:.2f}** per refer!
2️⃣ **Task Commission:** **10% Extra Commission** Jab aapka refer QR Task complete karega!

🔗 *Aapka Personal Referral Link:*
`{ref_link}`

👥 *Total Invited:* **{total_invited} Users**"""
  bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '📋 Task History')
def task_history_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  user_id = message.from_user.id

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT task_num, reward, status FROM task_history WHERE user_id = ?'
      ' ORDER BY id DESC LIMIT 5',
      (user_id,),
  )
  records = cursor.fetchall()
  conn.close()

  text = f'📋 *YOUR TASK HISTORY* 📋\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
  if not records:
    text += 'Abhi tak koi task complete nahi kiya hai.'
  else:
    for r in records:
      text += f'✅ *Task #{r[0]}* | Reward: ₹{r[1]:.2f} | *{r[2]}*\n'

  bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text in ['🛠 Support', '🛠️ Support'])
def support_cmd(message):
  if is_user_blocked(message.from_user.id):
    return
  text = """🛠️ *CUSTOMER SUPPORT* 🛠️
👤 *Owner Username:* @Abhishek723803
⏰ *Support Timings:* 10:00 AM - 10:00 PM"""
  bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ==================== ADMIN PANEL CONTROLS ====================


@bot.message_handler(
    commands=['admin'], func=lambda m: m.from_user.id == ADMIN_ID
)
@bot.message_handler(
    func=lambda m: m.text == '👑 Admin Panel' and m.from_user.id == ADMIN_ID
)
def admin_panel(message):
  admin_text = """👑 *ABHISHEK QR BOT - ADMIN PANEL* 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━
Aapka poora bot yahan se control hoga. Niche diye gaye option select karein:"""

  bot.send_message(
      message.chat.id,
      admin_text,
      reply_markup=get_admin_inline_keyboard(),
      parse_mode='Markdown',
  )


# Inline Buttons Action Handler for Admin
@bot.callback_query_handler(
    func=lambda call: call.from_user.id == ADMIN_ID
    and (call.data.startswith('w_') or call.data.startswith('u_'))
)
def handle_admin_actions(call):
  data = call.data
  conn = get_db_connection()
  cursor = conn.cursor()

  if data.startswith('w_'):
    action, req_id = data.split('_')[1], int(data.split('_')[2])

    cursor.execute(
        'SELECT user_id, amount, upi_id, status FROM withdrawals WHERE id = ?',
        (req_id,),
    )
    w_data = cursor.fetchone()

    if not w_data or w_data[3] != 'Pending':
      bot.answer_callback_query(
          call.id, '⚠️ Request already processed!', show_alert=True
      )
      conn.close()
      return

    u_id, amt, upi, _ = w_data

    if action == 'approve':
      cursor.execute(
          "UPDATE withdrawals SET status = 'Approved' WHERE id = ?", (req_id,)
      )
      cursor.execute(
          'UPDATE users SET total_withdrawn = total_withdrawn + ? WHERE user_id'
          ' = ?',
          (amt, u_id),
      )
      conn.commit()

      try:
        bot.send_message(
            u_id,
            f'✅ *WITHDRAWAL SUCCESSFUL!*\nAapka ₹{amt:.2f} ka payout UPI ID:'
            f' `{upi}` par transfer kar diya gaya hai!',
            parse_mode='Markdown',
        )
      except Exception:
        pass

      bot.edit_message_text(
          f'✅ *WITHDRAWAL APPROVED!*\nReq #{req_id} | User: `{u_id}` | Amt:'
          f' ₹{amt:.2f}',
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          parse_mode='Markdown',
      )
      bot.answer_callback_query(call.id, '✅ Approved!')

    elif action == 'reject':
      cursor.execute(
          "UPDATE withdrawals SET status = 'Rejected' WHERE id = ?", (req_id,)
      )
      cursor.execute(
          'UPDATE users SET balance = balance + ? WHERE user_id = ?',
          (amt, u_id),
      )
      conn.commit()

      try:
        bot.send_message(
            u_id,
            f'❌ *WITHDRAWAL REJECTED!*\nAapka ₹{amt:.2f} ka withdrawal reject'
            ' ho gaya hai aur paise wallet me refund ho gaye hain.',
            parse_mode='Markdown',
        )
      except Exception:
        pass

      bot.edit_message_text(
          f'❌ *WITHDRAWAL REJECTED!*\nReq #{req_id} | User: `{u_id}` | Amt:'
          f' ₹{amt:.2f} (Refunded)',
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          parse_mode='Markdown',
      )
      bot.answer_callback_query(call.id, '❌ Rejected & Refunded!')

  elif data.startswith('u_block_'):
    target_id = int(data.split('_')[2])
    cursor.execute(
        'UPDATE users SET is_blocked = 1 WHERE user_id = ?', (target_id,)
    )
    conn.commit()
    bot.answer_callback_query(
        call.id, f'🚫 User {target_id} Blocked!', show_alert=True
    )

  conn.close()


@bot.callback_query_handler(
    func=lambda call: call.from_user.id == ADMIN_ID
    and call.data.startswith('admin_')
)
def handle_admin_callbacks(call):
  conn = get_db_connection()
  cursor = conn.cursor()

  if call.data == 'admin_stats':
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute(
        'SELECT COUNT(*) FROM users WHERE notifications_enabled = 1'
    )
    notif_users = cursor.fetchone()[0]

    cursor.execute(
    
"SELECT COUNT(*), SUM(amount) FROM withdrawals WHERE status = 'Pending'"
    )
    p_reqs, p_amt = cursor.fetchone()
    p_amt = p_amt or 0.0

    cursor.execute(
        'SELECT SUM(total_withdrawn), SUM(total_rewards) FROM users'
    )
    tot_w, tot_r = cursor.fetchone()
    tot_w = tot_w or 0.0
    tot_r = tot_r or 0.0

    stats_msg = f"""📊 *ABHISHEK QR BOT STATISTICS* 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 *Total Registered Users:* **{total_users}**
🔔 *Notification Enabled Users:* **{notif_users}**
⏳ *Pending Withdrawals:* **{p_reqs}** (₹{p_amt:.2f})
💸 *Total Payout Delivered:* **₹{tot_w:.2f}**
🎁 *Total User Earnings:* **₹{tot_r:.2f}**"""

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, stats_msg, parse_mode='Markdown')

  elif call.data == 'admin_pending_w':
    cursor.execute(
        "SELECT id, user_id, amount, upi_id FROM withdrawals WHERE status ="
        " 'Pending' LIMIT 10"
    )
    pending = cursor.fetchall()

    if not pending:
      bot.answer_callback_query(
          call.id, '✅ Koi pending withdrawal nahi hai!', show_alert=True
      )
      conn.close()
      return

    bot.answer_callback_query(call.id)
    for req in pending:
      req_id, u_id, amt, upi = req
      btn_markup = InlineKeyboardMarkup(row_width=2)
      btn_markup.add(
          InlineKeyboardButton(
              '✅ Approve', callback_data=f'w_approve_{req_id}'
          ),
          InlineKeyboardButton(
              '❌ Reject', callback_data=f'w_reject_{req_id}'
          ),
      )
      bot.send_message(
          call.message.chat.id,
          f'🆔 *Req #{req_id}*\n👤 User: `{u_id}`\n💵 Amt: **₹{amt:.2f}**\n💳'
          f' UPI: `{upi}`',
          reply_markup=btn_markup,
          parse_mode='Markdown',
      )

  elif call.data == 'admin_toggle_block':
    msg = bot.send_message(
        call.message.chat.id,
        '🚫 Block/Unblock karne ke liye User ID bhejein:\n(Example: `8411871478`)',
        parse_mode='Markdown',
    )
    bot.register_next_step_handler(msg, process_admin_block)

  elif call.data == 'admin_add_task':
    msg = bot.send_message(
        call.message.chat.id,
        '🎯 Task Approve karne ke liye detail bhejein:\nFormat: `USER_ID'
        ' TASK_NUM AMOUNT`\nExample: `8411871478 1 10`',
        parse_mode='Markdown',
    )
    bot.register_next_step_handler(msg, process_admin_add_task)

  elif call.data == 'admin_qr_broadcast':
    msg = bot.send_message(
        call.message.chat.id,
        '⚡ *LIVE QR TASK ALERT BROADCAST*\n\nNaye QR task ki detail ya'
        ' Message likhein (Ye message sirf unhi users ko jayega jinhone'
        ' Notification ON rakha hai):',
        parse_mode='Markdown',
    )
    bot.register_next_step_handler(msg, process_admin_qr_broadcast)

  elif call.data == 'admin_broadcast':
    msg = bot.send_message(
        call.message.chat.id,
        '📢 *GENERAL BROADCAST*\n\nSabhi users ko bhejne ke liye Message'
        ' likhein:',
    )
    bot.register_next_step_handler(msg, process_admin_broadcast)

  elif call.data == 'admin_set_chan':
    msg = bot.send_message(
        call.message.chat.id,
        '🔗 Naya Official Channel Link bhejein:\nExample:'
        ' `https://t.me/YourChannel`',
        parse_mode='Markdown',
    )
    bot.register_next_step_handler(msg, process_admin_set_channel)

  conn.close()


def process_admin_block(message):
  try:
    target_id = int(message.text.strip())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT is_blocked FROM users WHERE user_id = ?', (target_id,)
    )
    row = cursor.fetchone()

    if row:
      new_status = 0 if row[0] == 1 else 1
      cursor.execute(
          'UPDATE users SET is_blocked = ? WHERE user_id = ?',
          (new_status, target_id),
      )
      conn.commit()
      st_text = '🚫 Blocked' if new_status == 1 else '🟢 Unblocked'
      bot.send_message(
          message.chat.id,
          f'✅ User `{target_id}` status updated to: **{st_text}**',
          parse_mode='Markdown',
      )
    else:
      bot.send_message(message.chat.id, '❌ User database me nahi mila.')
    conn.close()
  except Exception:
    bot.send_message(message.chat.id, '❌ Invalid User ID!')


def process_admin_add_task(message):
  try:
    args = message.text.strip().split()
    target_id = int(args[0])
    task_num = int(args[1])
    reward = float(args[2])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE users SET balance = balance + ?, total_rewards = total_rewards'
        ' + ? WHERE user_id = ?',
        (reward, reward, target_id),
    )
    cursor.execute(
        'INSERT INTO task_history (user_id, task_num, reward) VALUES (?, ?, ?)',
        (target_id, task_num, reward),
    )
    conn.commit()

    try:
      bot.send_message(
          target_id,
          f'🎉 *TASK APPROVED!*\nTask #{task_num} complete! **₹{reward:.2f}**'
          ' credited!',
          parse_mode='Markdown',
      )
    except Exception:
      pass

    cursor.execute(
        'SELECT referred_by FROM users WHERE user_id = ?', (target_id,)
    )
    ref_row = cursor.fetchone()
    if ref_row and ref_row[0]:
      referrer_id = ref_row[0]
      commission = reward * TASK_COMMISSION_PERCENT
      cursor.execute(
          'UPDATE users SET balance = balance + ?, total_rewards ='
          ' total_rewards + ? WHERE user_id = ?',
          (commission, commission, referrer_id),
      )
      conn.commit()
      try:
        bot.send_message(
            referrer_id,
            '🎁 *10% REFERRAL COMMISSION RECEIVED!*\n'
            f'Aapke refer ne Task #{task_num} complete kiya hai!\n'
            f'Aapko **10% Commission (₹{commission:.2f})** mil gaya hai!',
            parse_mode='Markdown',
        )
      except Exception:
        pass

    conn.close()
    bot.send_message(
        message.chat.id,
        f'✅ Task #{task_num} Approved! User `{target_id}` credited with'
        f' ₹{reward:.2f}',
        parse_mode='Markdown',
    )
  except Exception:
    bot.send_message(
        message.chat.id,
        '❌ Invalid Input! Example Format: `8411871478 1 10`',
        parse_mode='Markdown',
    )


def process_admin_qr_broadcast(message):
  qr_msg = (
      '🚨 *NEW LIVE QR TASK ARRIVED!* 🚨\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
      + message.text.strip()
  )

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT user_id FROM users WHERE notifications_enabled = 1 AND'
      ' is_blocked = 0'
  )
  users = cursor.fetchall()
  conn.close()

  count = 0
  for u in users:
    try:
      bot.send_message(u[0], qr_msg, parse_mode='Markdown')
      count += 1
    except Exception:
      pass

  bot.send_message(
      message.chat.id,
      f'⚡ Instant QR Task Alert sent to **{count}** active Notification Users!',
      parse_mode='Markdown',
  )


def process_admin_broadcast(message):
  broadcast_msg = message.text.strip()
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT user_id FROM users WHERE is_blocked = 0')
  users = cursor.fetchall()
  conn.close()

  count = 0
  for u in users:
    try:
      bot.send_message(u[0], broadcast_msg, parse_mode='Markdown')
      count += 1
    except Exception:
      pass

  bot.send_message(
      message.chat.id,
      f'📢 Broadcast Sent Successfully to **{count}** users!',
      parse_mode='Markdown',
  )


def process_admin_set_channel(message):
  new_link = message.text.strip()
  set_setting('channel_link', new_link)
  bot.send_message(
      message.chat.id,
      f'✅ Channel link updated successfully:\n{new_link}',
      disable_web_page_preview=True,
  )


print('Abhishek QR Bot running cleanly with full Admin controls...')
bot.infinity_polling()
