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

TOKEN = '8513419896:AAFMs-OxnZE7OjWjPK8gt34cMU9Z5-w1_2E'
ADMIN_ID = 8411871478
TASK_COMMISSION_PERCENT = 0.10

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


@app.route('/')
def home():
  return 'Abhishek QR Bot is active and running 24/7!'


def get_db_connection():
  conn = sqlite3.connect('bot_database.db', check_same_thread=False)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            total_withdrawn REAL DEFAULT 0.0,
            total_rewards REAL DEFAULT 0.0,
            notifications_enabled INTEGER DEFAULT 1,
            is_blocked INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            upi_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_num INTEGER,
            reward REAL
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)
    """)
  conn.commit()
  conn.close()


init_db()


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


def safe_send_message(chat_id, text, **kwargs):
  try:
    return bot.send_message(chat_id, text, **kwargs)
  except Exception as e:
    print(f'Ignored error: {e}')
    return None


def get_main_keyboard(user_id):
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(KeyboardButton('🎯 GET QR'), KeyboardButton('💰 My Balance'))
  markup.add(KeyboardButton('👤 My Account'), KeyboardButton('💸 Withdraw Money'))
  markup.add(
      KeyboardButton('📜 Withdrawal History'),
      KeyboardButton('🪙 Invite & Earn'),
  )
  markup.add(
      KeyboardButton('📋 Task History'),
      KeyboardButton('🔔 Toggle Notification'),
  )
  markup.add(KeyboardButton('🛠️ Support'))
  if user_id == ADMIN_ID:
    markup.add(KeyboardButton('👑 Admin Panel'))
  return markup


@bot.message_handler(commands=['start'])
def send_welcome(message):
  u_id = message.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM users WHERE user_id = ?', (u_id,))
  user = cursor.fetchone()

  if not user:
    args = message.text.split()
    ref_id = None
    if len(args) > 1 and args[1].isdigit():
      possible_ref = int(args[1])
      if possible_ref != u_id:
        cursor.execute(
            'SELECT user_id FROM users WHERE user_id = ?', (possible_ref,)
        )
        if cursor.fetchone():
          ref_id = possible_ref
    cursor.execute(
        'INSERT INTO users (user_id, referred_by) VALUES (?, ?)', (u_id, ref_id)
    )
    conn.commit()

  cursor.execute('SELECT is_blocked FROM users WHERE user_id = ?', (u_id,))
  blocked_row = cursor.fetchone()
  if blocked_row and blocked_row['is_blocked'] == 1:
    conn.close()
    return
  conn.close()

  keyboard = get_main_keyboard(u_id)
  welcome_text = (
      '👋 *Welcome to ABHISHEK QR BOT!* 🚀\n\n'
      'Aapka hamare official QR Earning platform par swagat hai!\n\n'
      '👇 *Key Features:*\n'
      '• 🎯 *QR Tasks:* Fast QR scans karke instant earning karein.\n'
      '• 💰 *Referral System:* Per refer ₹1.00 Direct Bonus + 10% Task'
      ' Commission!\n'
      '• 💸 *Instant Withdraw:* Direct UPI / FamPay me payout!\n'
      '• 🔔 *Instant Task Alerts:* Direct QR notification pane ke liye Toggle'
      ' Notification ON rakhein!'
  )
  safe_send_message(
      message.chat.id,
      welcome_text,
      reply_markup=keyboard,
      parse_mode='Markdown',
  )


@bot.message_handler(func=lambda m: m.text == '🎯 GET QR')
def handle_get_qr(message):
  ch_link = (
      get_setting('channel_link', 'https://t.me/+757WqqqLLoo4Yjhl')
      or 'https://t.me/+757WqqqLLoo4Yjhl'
  )
  text = (
      '🎯 *QR TASK & CLAIM ZONE* 🎯\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n⚠️'
      ' *IMPORTANT NOTICE:*\nLive QR tasks limited time ke liye aate'
      ' hain.\n\n📌 *Rules:*\n1️⃣ Get QR par tap karein.\n2️⃣ QR Active hone'
      ' par hi payment claim hogi.\n\n🔔 *LIVE QR ALERTS:*\nNaye QR tasks ke'
      ' alerts pane ke liye official channel join karein:\n📢 Official'
      f' Channel: [{ch_link}]({ch_link})\n\n⚡ *Agla QR Task Jald Hi'
      ' Aayega! Keep Checking!* ⚡'
  )
  markup = InlineKeyboardMarkup()
  markup.add(
      InlineKeyboardButton(
          '🎯 GET QR (Check Status)', callback_data='user_get_qr'
      )
  )
  safe_send_message(
      message.chat.id,
      text,
      reply_markup=markup,
      parse_mode='Markdown',
      disable_web_page_preview=True,
  )


@bot.callback_query_handler(func=lambda call: call.data == 'user_get_qr')
def callback_user_get_qr(call):
  bot.answer_callback_query(
      call.id,
      '⚠️ Filhaal koi naya QR live nahi hai! Channel join rakhein alert ke'
      ' liye.',
      show_alert=True,
  )


@bot.message_handler(func=lambda m: m.text == '💰 My Balance')
def handle_my_balance(message):
  u_id = message.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT balance FROM users WHERE user_id = ?', (u_id,))
  row = cursor.fetchone()
  conn.close()
  bal = row['balance'] if row and row['balance'] is not None else 0.0
  text = (
      '💰 *YOUR WALLET & TASK STATUS* 💰\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
      f'💵 *Available Balance:* ₹{bal:.2f}\n'
      '📌 *Per Task Rate:* ₹10.00 / QR\n\n'
      '🏧 *Minimum Withdrawal Limit:* ₹10.00'
  )
  safe_send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '👤 My Account')
def handle_my_account(message):
  u_id = message.from_user.id
  first_name = message.from_user.first_name
  username = (
      f'@{message.from_user.username}'
      if message.from_user.username
      else 'None'
  )
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT balance, total_rewards, total_withdrawn, notifications_enabled'
      ' FROM users WHERE user_id = ?',
      (u_id,),
  )
  row = cursor.fetchone()
  cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (u_id,))
  ref_count = cursor.fetchone()[0]
  conn.close()

  bal = row['balance'] if row and row['balance'] is not None else 0.0
  tot_rew = (
      row['total_rewards'] if row and row['total_rewards'] is not None else 0.0
  )
  tot_wit = (
      row['total_withdrawn']
      if row and row['total_withdrawn'] is not None
      else 0.0
  )
  notif_status = (
      '🟢 ON' if row and row['notifications_enabled'] == 1 else '🔴 OFF'
  )

  text = (
      '👤 *YOUR ACCOUNT PROFILE* 👤\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
      f'👤 *Name:* {first_name}\n'
      f'✨ *Username:* {username}\n'
      f'🆔 *Telegram ID:* `{u_id}`\n\n'
      f'💵 *Available Balance:* ₹{bal:.2f}\n'
      f'🎁 *Total Rewards Earned:* ₹{tot_rew:.2f}\n'
      f'💸 *Total Withdrawn:* ₹{tot_wit:.2f}\n'
      f'👥 *Total Invited:* {ref_count} Users\n'
      f'🔔 *Task Notifications:* {notif_status}'
  )
  safe_send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '💸 Withdraw Money')
def handle_withdraw_money(message):
  u_id = message.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT balance FROM users WHERE user_id = ?', (u_id,))
  row = cursor.fetchone()
  conn.close()
  bal = row['balance'] if row else 0.0
  text = (
      '💸 *WITHDRAWAL SECTION* 💸\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
      f'💳 *Current Balance:* ₹{bal:.2f}\n'
      '🏧 *Minimum Withdrawal:* ₹10.00\n\n'
      '👇 *Apna UPI ID enter karke request submit karein (Example:*'
      ' `name@upi`*):*'
  )
  if bal < 10.0:
    text += '\n\n❌ *Aapka balance ₹10.00 se kam hai.*'
    safe_send_message(message.chat.id, text, parse_mode='Markdown')
    return
  msg = safe_send_message(message.chat.id, text, parse_mode='Markdown')
  bot.register_next_step_handler(msg, process_withdrawal_request)


def process_withdrawal_request(message):
  try:
    args = message.text.strip().split()
    if len(args) < 2:
      safe_send_message(
          message.chat.id,
          '❌ Invalid format! Please send in format: `UPI_ID AMOUNT`',
          parse_mode='Markdown',
      )
      return
    upi_id = args[0]
    amount = float(args[1])
    u_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (u_id,))
    row = cursor.fetchone()
    if not row or row['balance'] < amount:
      safe_send_message(
          message.chat.id,
          '❌ Aapke wallet mein itna balance nahi hai!',
          parse_mode='Markdown',
      )
      conn.close()
      return
    if amount < 10.0:
      safe_send_message(
          message.chat.id,
          '❌ Minimum withdrawal amount ₹10.00 hai!',
          parse_mode='Markdown',
      )
      conn.close()
      return
    cursor.execute(
        'UPDATE users SET balance = balance - ? WHERE user_id = ?',
        (amount, u_id),
    )
    cursor.execute(
        'INSERT INTO withdrawals (user_id, amount, upi_id, status) VALUES (?, ?,'
        " ?, 'Pending')",
        (u_id, amount, upi_id),
    )
    conn.commit()
    req_id = cursor.lastrowid
    conn.close()
    safe_send_message(
        message.chat.id,
        '✅ *Withdrawal Request Submitted Successfully!*\n\n🆔 Req ID:'
        f' `#{req_id}`\n💵 Amount: **₹{amount:.2f}**\n💳 UPI:'
        f' `{upi_id}`\nStatus: **Pending (Admin review)**',
        parse_mode='Markdown',
    )
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton('✅ Approve', callback_data=f'w_approve_{req_id}'),
        InlineKeyboardButton('❌ Reject', callback_data=f'w_reject_{req_id}'),
    )
    safe_send_message(
        ADMIN_ID,
        f'🔔 *NEW WITHDRAWAL REQUEST!*\n\n🆔 Req ID: `#{req_id}`\n👤 User:'
        f' `{u_id}`\n💵 Amount: **₹{amount:.2f}**\n💳 UPI: `{upi_id}`',
        reply_markup=admin_markup,
        parse_mode='Markdown',
    )
  except Exception:
    safe_send_message(
        message.chat.id,
        '❌ Invalid input! Format: `UPI_ID AMOUNT` (e.g. `upi@okaxis 50`)',
        parse_mode='Markdown',
    )


@bot.message_handler(func=lambda m: m.text == '📜 Withdrawal History')
def handle_withdrawal_history(message):
  u_id = message.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT id, amount, upi_id, status FROM withdrawals WHERE user_id = ?'
      ' ORDER BY id DESC LIMIT 10',
      (u_id,),
  )
  rows = cursor.fetchall()
  conn.close()
  text = (
      '📜 *WITHDRAWAL HISTORY* 📜\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🆔 *User ID:*'
      f' `{u_id}`\n\n'
  )
  if not rows:
    text += 'Abhi tak koi withdrawal record nahi hai.'
  else:
    for r in rows:
      st_emoji = (
          '✅'
          if r['status'] == 'Approved'
          else ('❌' if r['status'] == 'Rejected' else '⏳')
      )
      text += (
          f"🆔 Req #{r['id']} | ₹{r['amount']:.2f}\n💳 UPI: `{r['upi_id']}`\nStatus:"
          f' {st_emoji} **{r["status"]}**\n\n'
      )
  safe_send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '🪙 Invite & Earn')
def handle_invite_earn(message):
  u_id = message.from_user.id
  bot_username = bot.get_me().username
  ref_link = f'https://t.me/{bot_username}?start={u_id}'
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (u_id,))
  ref_count = cursor.fetchone()[0]
  conn.close()
  text = (
      '🪙 *Invite & Earn Rules:* 🪙\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💰'
      ' *EARNINGS:*\n1️⃣ *Direct Join Bonus:* ₹1.00 per refer!\n2️⃣ *Task'
      ' Commission:* 10% Extra Commission Jab aapka refer QR Task complete'
      f' karega!\n\n🔗 *Aapka Personal Referral Link:*\n`{ref_link}`\n\n👥 *Total'
      f' Invited:* **{ref_count} Users**'
  )
  safe_send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '📋 Task History')
def handle_task_history(message):
  u_id = message.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT task_num, reward FROM task_history WHERE user_id = ? ORDER BY id'
      ' DESC LIMIT 10',
      (u_id,),
  )
  rows = cursor.fetchall()
  conn.close()
  text = (
      '📋 *YOUR TASK HISTORY* 📋\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🆔 *User ID:*'
      f' `{u_id}`\n\n'
  )
  if not rows:
    text += 'Abhi tak koi task complete nahi kiya hai.'
  else:
    for r in rows:
      text += (
          f"🎯 Task #{r['task_num']} — Reward: **₹{r['reward']:.2f}**\n\n"
      )
  safe_send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '🔔 Toggle Notification')
def handle_toggle_notification(message):
  u_id = message.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT notifications_enabled FROM users WHERE user_id = ?', (u_id,)
  )
  row = cursor.fetchone()
  if row:
    new_status = 0 if row['notifications_enabled'] == 1 else 1
    cursor.execute(
        'UPDATE users SET notifications_enabled = ? WHERE user_id = ?',
        (new_status, u_id),
    )
    conn.commit()
    if new_status == 1:
      status_text = (
          '🔔 *Task Notifications Turned ON!*\nAapko ab live QR tasks ke'
          ' instant alerts milenge.'
      )
    else:
      status_text = (
          '🔕 *Task Notifications Turned OFF!*\nAapko instant task alerts nahi'
          ' milenge.'
      )
  else:
    status_text = '⚠️ User not found.'
  conn.close()
  safe_send_message(message.chat.id, status_text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '🛠️ Support')
def handle_support(message):
  text = (
      '🛠️ *CUSTOMER SUPPORT* 🛠️\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n👤 *Owner'
      ' Username:* @Abhishek723803\n⏰ *Support Timings:* 10:00 AM - 10:00 PM'
  )
  safe_send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.text == '👑 Admin Panel')
def handle_admin_panel(message):
  if message.from_user.id != ADMIN_ID:
    safe_send_message(
        message.chat.id,
        '⚠️ Aap unauthorized hain! Yeh panel sirf admin ke liye hai.',
    )
    return
  markup = InlineKeyboardMarkup()
  markup.add(
      InlineKeyboardButton('📊 Statistics', callback_data='admin_stats'),
      InlineKeyboardButton(
          '⏳ Pending Withdrawals', callback_data='admin_pending_w'
      ),
  )
  markup.add(
      InlineKeyboardButton(
          '🚫 Block/Unblock User', callback_data='admin_toggle_block'
      ),
      InlineKeyboardButton('🎯 Add Task Reward', callback_data='admin_add_task'),
  )
  markup.add(
      InlineKeyboardButton('⚡ QR Broadcast', callback_data='admin_qr_broadcast'),
      InlineKeyboardButton('📢 General Broadcast', callback_data='admin_broadcast'),
  )
  markup.add(
      InlineKeyboardButton('🔗 Set Channel Link', callback_data='admin_set_chan')
  )
  safe_send_message(
      message.chat.id,
      '👑 *WELCOME ADMIN PANEL*\nChoose an action below:',
      reply_markup=markup,
      parse_mode='Markdown',
  )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith(('w_', 'admin_'))
)
def handle_all_callbacks(call):
  data = call.data
  conn = get_db_connection()
  cursor = conn.cursor()
  try:
    if data.startswith('w_approve_'):
      req_id = int(data.split('_')[2])
      cursor.execute(
          'SELECT user_id, amount FROM withdrawals WHERE id = ?', (req_id,)
      )
      row = cursor.fetchone()
      if row:
        u_id, amt = row['user_id'], row['amount']
        cursor.execute(
            "UPDATE withdrawals SET status = 'Approved' WHERE id = ?", (req_id,)
        )
        cursor.execute(
            'UPDATE users SET total_withdrawn = total_withdrawn + ? WHERE'
            ' user_id = ?',
            (amt, u_id),
        )
        conn.commit()
        try:
          bot.edit_message_text(
              f'✅ *WITHDRAWAL APPROVED!*\nReq #{req_id}\n ₹{amt:.2f} Paid!',
              chat_id=call.message.chat.id,
              message_id=call.message.message_id,
              parse_mode='Markdown',
          )
        except Exception:
          pass
        bot.answer_callback_query(call.id, '✅ Approved!')
        safe_send_message(
            u_id,
            f'🎉 *Withdrawal Approved!*\nYour request #{req_id} of ₹{amt:.2f}'
            ' has been successfully paid to your UPI!',
            parse_mode='Markdown',
        )
    elif data.startswith('w_reject_'):
      req_id = int(data.split('_')[2])
      cursor.execute(
          'SELECT user_id, amount FROM withdrawals WHERE id = ?', (req_id,)
      )
      row = cursor.fetchone()
      if row:
        u_id, amt = row['user_id'], row['amount']
        cursor.execute(
            "UPDATE withdrawals SET status = 'Rejected' WHERE id = ?", (req_id,)
        )
        cursor.execute(
            'UPDATE users SET balance = balance + ? WHERE user_id = ?',
            (amt, u_id),
        )
        conn.commit()
        try:
          bot.edit_message_text(
              f'❌ *WITHDRAWAL REJECTED!*\nReq #{req_id}\n ₹{amt:.2f} (Refunded)',
              chat_id=call.message.chat.id,
              message_id=call.message.message_id,
              parse_mode='Markdown',
          )
        except Exception:
          pass
        bot.answer_callback_query(call.id, '❌ Rejected & Refunded!')
        safe_send_message(
            u_id,
            f'❌ *Withdrawal Rejected!*\nYour request #{req_id} of ₹{amt:.2f}'
            ' was rejected and refunded back to your balance.',
            parse_mode='Markdown',
        )
    elif data.startswith('admin_'):
      if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(
            call.id, '⚠️ You are not authorized!', show_alert=True
        )
        conn.close()
        return
      if data == 'admin_stats':
        cursor.execute('SELECT COUNT(*) FROM users')
        tot_users = cursor.fetchone()[0]
        cursor.execute(
            'SELECT COUNT(*) FROM users WHERE notifications_enabled = 1'
        )
        notif_users = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*), SUM(amount) FROM withdrawals WHERE status ="
            " 'Pending'"
        )
        p_row = cursor.fetchone()
        p_reqs, p_amt = p_row[0], p_row[1] or 0.0
        cursor.execute(
            'SELECT SUM(total_withdrawn), SUM(total_rewards) FROM users'
        )
        tot_row = cursor.fetchone()
        tot_w, tot_r = tot_row[0] or 0.0, tot_row[1] or 0.0
        stats_msg = f"""📊 *ABHISHEK QR BOT STATISTICS* 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 *Total Registered Users:* **{tot_users}**
🔔 *Notification Enabled:* **{notif_users}**
⏳ *Pending Withdrawals:* **{p_reqs}** (₹{p_amt:.2f})
💸 *Total Payout Delivered:* **₹{tot_w:.2f}**
🎁 *Total User Earnings:* **₹{tot_r:.2f}**"""
        bot.answer_callback_query(call.id)
           safe_send_message(
            call.message.chat.id, stats_msg, parse_mode='Markdown'
        )
      elif data == 'admin_pending_w':
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
          btn_markup = InlineKeyboardMarkup()
          btn_markup.add(
              InlineKeyboardButton(
                  '✅ Approve', callback_data=f'w_approve_{req_id}'
              ),
              InlineKeyboardButton(
                  '❌ Reject', callback_data=f'w_reject_{req_id}'
              ),
          )
          safe_send_message(
              call.message.chat.id,
              f'🆔 *Req #{req_id}*\n👤 User: `{u_id}`\n💵 Amt:'
              f' **₹{amt:.2f}**\n💳 UPI: `{upi}`',
              reply_markup=btn_markup,
              parse_mode='Markdown',
          )
      elif data == 'admin_toggle_block':
        msg = bot.send_message(
            call.message.chat.id,
            '🚫 Block/Unblock karne ke liye User ID bhejein:\n(Example:'
            ' `8411871478`)',
            parse_mode='Markdown',
        )
        bot.register_next_step_handler(msg, process_admin_block)
      elif data == 'admin_add_task':
        msg = bot.send_message(
            call.message.chat.id,
            '🎯 Task Approve karne ke liye detail bhejein:\nFormat: `USER_ID'
            ' TASK_NUM AMOUNT`\nExample: `8411871478 1 10`',
            parse_mode='Markdown',
        )
        bot.register_next_step_handler(msg, process_admin_add_task)
      elif data == 'admin_qr_broadcast':
        msg = bot.send_message(
            call.message.chat.id,
            '⚡ *LIVE QR TASK ALERT BROADCAST*\n\nNaye QR task ki detail ya'
            ' Message likhein:',
            parse_mode='Markdown',
        )
        bot.register_next_step_handler(msg, process_admin_qr_broadcast)
      elif data == 'admin_broadcast':
        msg = bot.send_message(
            call.message.chat.id,
            '📢 *GENERAL BROADCAST*\n\nSabhi users ko bhejne ke liye Message'
            ' likhein:',
        )
        bot.register_next_step_handler(msg, process_admin_broadcast)
      elif data == 'admin_set_chan':
        msg = bot.send_message(
            call.message.chat.id,
            '🔗 Naya Official Channel Link bhejein:\nExample:'
            ' `https://t.me/YourChannel`',
            parse_mode='Markdown',
        )
        bot.register_next_step_handler(msg, process_admin_set_channel)
  except Exception as e:
    print(f'Error in callback: {e}')
  finally:
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
      new_status = 0 if row['is_blocked'] == 1 else 1
      cursor.execute(
          'UPDATE users SET is_blocked = ? WHERE user_id = ?',
          (new_status, target_id),
      )
      conn.commit()
      st_text = '🚫 Blocked' if new_status == 1 else '🟢 Unblocked'
      safe_send_message(
          message.chat.id,
          f'✅ User `{target_id}` status updated to: **{st_text}**',
          parse_mode='Markdown',
      )
    else:
      safe_send_message(message.chat.id, '❌ User database me nahi mila.')
    conn.close()
  except Exception:
    safe_send_message(message.chat.id, '❌ Invalid User ID!')


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
    safe_send_message(
        target_id,
        f'🎉 *TASK APPROVED!*\nTask #{task_num} complete! **₹{reward:.2f}**'
        ' credited!',
        parse_mode='Markdown',
    )
    cursor.execute(
        'SELECT referred_by FROM users WHERE user_id = ?', (target_id,)
    )
    ref_row = cursor.fetchone()
    if ref_row and ref_row['referred_by']:
      referrer_id = ref_row['referred_by']
      commission = reward * TASK_COMMISSION_PERCENT
      cursor.execute(
          'UPDATE users SET balance = balance + ?, total_rewards ='
          ' total_rewards + ? WHERE user_id = ?',
          (commission, commission, referrer_id),
      )
      conn.commit()
      safe_send_message(
          referrer_id,
          '🎁 *10% REFERRAL COMMISSION RECEIVED!*\n'
          f'Aapke refer ne Task #{task_num} complete kiya hai!\n'
          f'Aapko **10% Commission (₹{commission:.2f})** mil gaya hai!',
          parse_mode='Markdown',
      )
    conn.close()
    safe_send_message(
        message.chat.id,
        f'✅ Task #{task_num} Approved! User `{target_id}` credited with'
        f' ₹{reward:.2f}',
        parse_mode='Markdown',
    )
  except Exception:
    safe_send_message(
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
      'SELECT user_id FROM users WHERE notifications_enabled = 1 AND is_blocked'
      ' = 0'
  )
  users = cursor.fetchall()
  conn.close()
  count = 0
  for u in users:
    if safe_send_message(u['user_id'], qr_msg, parse_mode='Markdown'):
      count += 1
  safe_send_message(
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
    if safe_send_message(u['user_id'], broadcast_msg, parse_mode='Markdown'):
      count += 1
  safe_send_message(
      message.chat.id,
      f'📢 Broadcast Sent Successfully to **{count}** users!',
      parse_mode='Markdown',
  )


def process_admin_set_channel(message):
  new_link = message.text.strip()
  set_setting('channel_link', new_link)
  safe_send_message(
      message.chat.id,
      f'✅ Channel link updated successfully:\n{new_link}',
      disable_web_page_preview=True,
  )


def run_bot():
  print('Telegram bot started...')
  bot.infinity_polling(none_stop=True, interval=0, timeout=20)


if __name__ == '__main__':
  bot_thread = threading.Thread(target=run_bot)
  bot_thread.daemon = True
  bot_thread.start()

  port = int(os.environ.get('PORT', 10000))
  print(f'Starting Flask on port {port}...')
  app.run(host='0.0.0.0', port=port)
        
