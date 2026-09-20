import os
import sqlite3
import threading
from flask import Flask
import telebot
from telebot import types

API_TOKEN = '8513419896:AAFzIlJaBL01lMWt4rHUQXTJJGcuokFEmKg'
ADMIN_ID = 8411871478
CHANNEL_USERNAME = 'https://t.me/+757WqqqLLoo4Yjhl'

bot = telebot.TeleBot(API_TOKEN)

app = Flask('')


@app.route('/')
def home():
  return 'Bot is active and running 24/7!'


def run_flask():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def get_db_connection():
  conn = sqlite3.connect('bot_database.db')
  conn.row_factory = sqlite3.Row
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
            total_earned REAL DEFAULT 0.0,
            total_withdrawn REAL DEFAULT 0.0,
            total_invited INTEGER DEFAULT 0,
            notifications INTEGER DEFAULT 1
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
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_name TEXT,
            status TEXT DEFAULT 'Completed'
        )
    ''')
  
  # Purane test balance ko clean karne ke liye:
  cursor.execute("UPDATE users SET balance = 0.0, total_earned = 0.0 WHERE balance = 50.0")
  conn.commit()
  conn.close()


init_db()


def get_main_keyboard():
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      types.KeyboardButton('🎯 GET QR'), types.KeyboardButton('💰 My Balance')
  )
  markup.add(
      types.KeyboardButton('👤 My Account'),
      types.KeyboardButton('💸 Withdraw Money'),
  )
  markup.add(
      types.KeyboardButton('📜 Withdrawal History'),
      types.KeyboardButton('💎 Invite & Earn'),
  )
  markup.add(
      types.KeyboardButton('📋 Task History'),
      types.KeyboardButton('🔔 Toggle Notification'),
  )
  markup.add(types.KeyboardButton('🛠 Support'))
  markup.add(types.KeyboardButton('👑 Admin Panel'))
  return markup


def safe_send_message(chat_id, text, parse_mode='Markdown', reply_markup=None):
  try:
    return bot.send_message(
        chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup
    )
  except Exception as e:
    print(f'Error sending message: {e}')
    return None


@bot.message_handler(commands=['start'])
def send_welcome(message):
  try:
    user_id = message.from_user.id
    first_name = message.from_user.first_name or 'User'
    username = message.from_user.username or 'None'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, first_name, username, balance,'
        ' total_earned) VALUES (?, ?, ?, 0.0, 0.0)',
        (user_id, first_name, username),
    )
    cursor.execute(
        'UPDATE users SET first_name = ?, username = ? WHERE user_id = ?',
        (first_name, username, user_id),
    )
    conn.commit()
    conn.close()

    welcome_text = (
        f'👋 *Welcome, {first_name}* 🚀\n\nAapka hamare official QR Earning'
        ' platform par swagat hai!\n\n🔑 *Key Features:*\n• 🎯 *QR Tasks:* Fast'
        ' QR scans karke instant earning karein.\n• 🎁 *Referral System:* Per'
        ' refer ₹1.00 Direct Bonus + 10% Task Commission!\n• 🏧 *Instant'
        ' Withdraw:* Direct UPI / FamPay payout!\n• 🔔 *Task Alerts:* Direct'
        ' QR notification pane ke liye Toggle Notification ON rakhein!'
    )

    safe_send_message(
        message.chat.id,
        welcome_text,
        reply_markup=get_main_keyboard(),
    )
  except Exception as e:
    print(f'Error in start: {e}')


@bot.message_handler(
    func=lambda message: message.text
    in [
        '🎯 GET QR',
        '💰 My Balance',
        '👤 My Account',
        '💸 Withdraw Money',
        '📜 Withdrawal History',
        '💎 Invite & Earn',
        '📋 Task History',
        '🔔 Toggle Notification',
        '🛠 Support',
        '👑 Admin Panel',
    ]
)
def handle_reply_buttons(message):
  try:
    text = message.text
    user_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()

    # User existence check to prevent errors
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
      first_name = message.from_user.first_name or 'User'
      username = message.from_user.username or 'None'
      cursor.execute(
          'INSERT INTO users (user_id, first_name, username, balance, total_earned) VALUES (?, ?, ?, 0.0, 0.0)',
          (user_id, first_name, username),
      )
      conn.commit()
      cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
      user = cursor.fetchone()

    if text == '🎯 GET QR':
      qr_msg = (
          '🎯 *QR TASK & CLAIM ZONE* 🎯\n\n⚠️ *IMPORTANT NOTICE:*\nLive QR tasks'
          ' limited time ke liye aate hain.\n\n📌 *Rules:*\n1️⃣ Get QR par tap'
          ' karein.\n2️⃣ QR active hone par hi payment claim hogi.\n\n🔔 *LIVE'
          ' QR ALERTS:*\nNaye QR tasks ke alerts pane ke liye official channel'
          ' join karein:\n🔗 *Official Channel:*'
          f' {CHANNEL_USERNAME}\n\n⚡ *Agla QR Task Jald Hi Aayega! Keep'
          ' Checking!* ⚡'
      )
      safe_send_message(message.chat.id, qr_msg, reply_markup=get_main_keyboard())

    elif text == '💰 My Balance':
      bal = user['balance'] if user else 0.0
      bal_msg = (
          f'💰 *YOUR WALLET & TASK STATUS* 💰\n\n🏦 Available Balance:'
          f' ₹{bal:.2f}\n📌 Per Task Rate: ₹10.00 / QR\n🏧 Minimum Withdrawal'
          ' Limit: ₹10.00'
      )
      safe_send_message(
          message.chat.id, bal_msg, reply_markup=get_main_keyboard()
      )

    elif text == '👤 My Account':
      bal = user['balance'] if user else 0.0
      earned = user['total_earned'] if user else 0.0
      withdrawn = user['total_withdrawn'] if user else 0.0
      invited = user['total_invited'] if user else 0
      notif_val = user['notifications'] if user and 'notifications' in user.keys() else 1
      notif_status = 'ON' if notif_val == 1 else 'OFF'
      uname = f'@{user["username"]}' if user and user['username'] and user['username'] != 'None' else 'No Username'
      fname = user['first_name'] if user and user['first_name'] else message.from_user.first_name

      acc_msg = (
          f'👤 *YOUR ACCOUNT PROFILE* 👤\n\n👤 Name: {fname}\n🔗 Username:'
          f' {uname}\n🆔 Telegram ID: `{user_id}`\n\n🏦 Available Balance:'
          f' ₹{bal:.2f}\n🎁 Total Rewards Earned: ₹{earned:.2f}\n💸 Total'
          f' Withdrawn: ₹{withdrawn:.2f}\n👥 Total Invited: {invited}'
          f' Users\n🔔 Task Notifications: {notif_status}'
      )
      safe_send_message(
          message.chat.id, acc_msg, reply_markup=get_main_keyboard()
      )

    elif text == '💸 Withdraw Money':
      bal = user['balance'] if user else 0.0
      wd_msg = (
          f'💳 *WITHDRAWAL SECTION* 💳\n\n🏦 Current Balance:'
          f' ₹{bal:.2f}\n🏧 Minimum Withdrawal: ₹10.00\n\n💡 *Apna UPI ID enter'
          ' karke request submit karein (Example: `name@upi`):*'
      )
      msg = safe_send_message(
          message.chat.id, wd_msg, reply_markup=get_main_keyboard()
      )
      bot.register_next_step_handler(msg, process_withdrawal_upi)

    elif text == '📜 Withdrawal History':
      cursor.execute('SELECT * FROM withdrawals WHERE user_id = ?', (user_id,))
      history = cursor.fetchall()
      if not history:
        hist_text = (
            f'📜 *WITHDRAWAL HISTORY* 📜\n\n🆔 Telegram ID: `{user_id}`\n\nAbhi'
            ' tak koi withdrawal record nahi hai.'
        )
        safe_send_message(
            message.chat.id, hist_text, reply_markup=get_main_keyboard()
        )
      else:
        hist_text = f'📜 *WITHDRAWAL HISTORY* 📜\n\n🆔 Telegram ID: `{user_id}`\n\n'
        for h in history:
          hist_text += (
              f'🆔 ID: `#{h["id"]}` | Amount: ₹{h["amount"]:.2f} | UPI:'
              f' `{h["upi_id"]}` | Status: *{h["status"]}*\n'
          )
        safe_send_message(
            message.chat.id, hist_text, reply_markup=get_main_keyboard()
        )

    elif text == '💎 Invite & Earn':
      bot_info = bot.get_me()
      ref_link = f'https://t.me/{bot_info.username}?start={user_id}'
      invited = user['total_invited'] if user else 0
      invite_msg = (
          f'💎 *Invite & Earn Rules:* 💎\n\n💰 *EARNINGS:*\n1️⃣ *Direct Join'
          ' Bonus:* ₹1.00 per refer!\n2️⃣ *Task Commission:* 10% Extra'
          ' Commission Jab aapka refer QR Task complete karega!\n\n🔗 *Aapka'
          f' Personal Referral Link:*\n`{ref_link}`\n\n👥 *Total Invited:*'
          f' {invited} Users'
      )
      safe_send_message(
          message.chat.id, invite_msg, reply_markup=get_main_keyboard()
      )

    elif text == '📋 Task History':
      cursor.execute(
          'SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC LIMIT 10',
          (user_id,),
      )
      tasks = cursor.fetchall()
      if not tasks:
        t_text = (
            '📋 *YOUR TASK HISTORY* 📋\n\nAbhi tak koi task complete nahi kiya'
            ' hai.'
        )
        safe_send_message(
            message.chat.id, t_text, reply_markup=get_main_keyboard()
        )
      else:
        t_text = '📋 *YOUR TASK HISTORY* 📋\n\n'
        for t in tasks:
          t_text += f'✔️ {t["task_name"]} - *{t["status"]}*\n'
        safe_send_message(
            message.chat.id, t_text, reply_markup=get_main_keyboard()
        )

    elif text == '🔔 Toggle Notification':
      current_notif = user['notifications'] if user and 'notifications' in user.keys() else 1
      new_val = 0 if current_notif == 1 else 1
      cursor.execute(
          'UPDATE users SET notifications = ? WHERE user_id = ?',
          (new_val, user_id),
      )
      conn.commit()
      if new_val == 1:
        notif_msg = (
            '🔔 *Task Notifications TURNED ON!*\nAapko ab live QR tasks ke'
            ' instant alerts milenge.'
        )
      else:
        notif_msg = (
            '🔕 *Task Notifications TURNED OFF!*\nAapko instant task alerts'
            ' nahi milenge.'
        )
      safe_send_message(
          message.chat.id, notif_msg, reply_markup=get_main_keyboard()
      )

    elif text == '🛠 Support':
      supp_msg = (
          '🛠 *CUSTOMER SUPPORT* 🛠\n\n👨‍💻 *Owner Username:* `@Abhishek723803`\n⏰'
          ' *Support Timings:* 10:00 AM - 10:00 PM'
      )
      safe_send_message(
          message.chat.id, supp_msg, reply_markup=get_main_keyboard()
      )

    elif text == '👑 Admin Panel':
      if user_id != ADMIN_ID:
        safe_send_message(
            message.chat.id,
            '⚠️ You are not authorized to access Admin Panel!',
            reply_markup=get_main_keyboard(),
        )
        return

      markup = types.InlineKeyboardMarkup(row_width=2)
      markup.add(
          types.InlineKeyboardButton('📊 Bot Stats', callback_data='admin_stats'),
          types.InlineKeyboardButton(
              '⏳ Pending Withdrawals', callback_data='admin_pending_w'
          ),
          types.InlineKeyboardButton(
              '📢 Broadcast', callback_data='admin_broadcast'
          ),
          types.InlineKeyboardButton(
              '🔗 Set Channel', callback_data='admin_set_chan'
          ),
      )
      safe_send_message(
          message.chat.id,
          '🔐 *Admin Control Panel*\n\nNiche se koi option chunein:',
          reply_markup=markup,
      )

    conn.close()
  except Exception as e:
    print(f'Error in reply button handler: {e}')


def process_withdrawal_upi(message):
  try:
    user_id = message.from_user.id
    upi_id = message.text.strip()
    withdrawal_amount = 10.0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user and user['balance'] >= withdrawal_amount:
      cursor.execute(
          'INSERT INTO withdrawals (user_id, amount, upi_id, status) VALUES (?,'
          ' ?, ?, "Pending")',
          (user_id, withdrawal_amount, upi_id),
      )
      conn.commit()
      conn.close()
      safe_send_message(
          message.chat.id,
          f'✅ *Withdrawal Request Submitted!*\n\n🏦 UPI ID:'
          f' `{upi_id}`\n💰 Amount: ₹{withdrawal_amount:.2f}\n⏳ Status:'
          ' *Pending*',
          reply_markup=get_main_keyboard(),
      )
    else:
      conn.close()
      safe_send_message(
          message.chat.id,
          f'❌ *Aapka balance ₹{withdrawal_amount:.2f} se kam hai.*',
          reply_markup=get_main_keyboard(),
      )
  except Exception as e:
    print(f'Error in withdrawal: {e}')


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    data = call.data
    user_id = call.from_user.id

    if data.startswith('admin_'):
      if user_id != ADMIN_ID:
        bot.answer_callback_query(
            call.id, '⚠️ You are not authorized!', show_alert=True
        )
        return

      if data == 'admin_stats':
        cursor.execute('SELECT COUNT(*) FROM users')
        tot_users = cursor.fetchone()[0]
        cursor.execute(
            'SELECT COUNT(*), SUM(amount) FROM withdrawals WHERE status ='
            ' "Pending"'
        )
        p_row = cursor.fetchone()
        p_reqs, p_amt = p_row[0] or 0, p_row[1] or 0.0

        cursor.execute('SELECT SUM(total_withdrawn) FROM users')
        tot_w = cursor.fetchone()[0] or 0.0

        stats_msg = (
            f'📊 *ADMIN STATS*\n\n👥 Total Users: *{tot_users}*\n⏳ Pending'
            f' Requests: *{p_reqs}* (₹{p_amt:.2f})\n💰 Total Payout Done:'
            f' *₹{tot_w:.2f}*'
        )
        bot.answer_callback_query(call.id)
        safe_send_message(call.message.chat.id, stats_msg)

      elif data == 'admin_pending_w':
        cursor.execute('SELECT * FROM withdrawals WHERE status = "Pending"')
        pending = cursor.fetchall()
        if not pending:
          bot.answer_callback_query(call.id, '📭 No pending withdrawals found!')
          return

        bot.answer_callback_query(call.id)
        for req in pending:
          r_id, u_id, amt, upi = (
              req['id'],
              req['user_id'],
              req['amount'],
              req['upi_id'],
          )
          markup = types.InlineKeyboardMarkup(row_width=2)
          markup.add(
              types.InlineKeyboardButton(
                  '✅ Approve', callback_data=f'w_approve_{r_id}'
              ),
              types.InlineKeyboardButton(
                  '❌ Reject', callback_data=f'w_reject_{r_id}'
              ),
          )
          safe_send_message(
              call.message.chat.id,
              f'⏳ *Withdrawal Request*\n\n🆔 Req ID: `#{r_id}`\n👤 User ID:'
              f' `{u_id}`\n💰 Amount: ₹{amt:.2f}\n🏦 UPI ID: `{upi}`',
              reply_markup=markup,
          )

      elif data == 'admin_broadcast':
        bot.answer_callback_query(call.id)
        msg = safe_send_message(
            call.message.chat.id, '📢 *Please send the broadcast message:*'
        )
        bot.register_next_step_handler(msg, process_broadcast)

      elif data == 'admin_set_chan':
        bot.answer_callback_query(call.id)
        msg = safe_send_message(
            call.message.chat.id,
            '🔗 *Naya Official Channel Link ya Username bhejo:*',
        )
        bot.register_next_step_handler(msg, process_set_chan)

    elif data.startswith('w_approve_'):
      if user_id != ADMIN_ID:
        return
      r_id = int(data.split('_')[2])
      cursor.execute(
          'SELECT * FROM withdrawals WHERE id = ? AND status = "Pending"',
          (r_id,),
      )
      req = cursor.fetchone()
      if req:
        u_id, amt = req['user_id'], req['amount']
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (u_id,))
        u_data = cursor.fetchone()
        if u_data and u_data['balance'] >= amt:
          cursor.execute(
              'UPDATE users SET balance = balance - ?, total_withdrawn ='
              ' total_withdrawn + ? WHERE user_id = ?',
              (amt, amt, u_id),
          )
          cursor.execute(
              'UPDATE withdrawals SET status = "Approved" WHERE id = ?', (r_id,)
          )
          conn.commit()
          bot.answer_callback_query(call.id, f'✅ Request #{r_id} Approved!')
          safe_send_message(
              call.message.chat.id,
              f'✅ Withdrawal Request `#{r_id}` of ₹{amt:.2f} has been'
              ' *Approved*.',
          )
          safe_send_message(
              u_id,
              f'🎉 *Aapka Withdrawal Approve ho gaya hai!*\n\n💰 Amount:'
              f' ₹{amt:.2f}\n🏦 Aapke UPI mein bhej diya gaya hai.',
          )
        else:
          bot.answer_callback_query(
              call.id, '❌ User has insufficient balance!', show_alert=True
          )
      else:
        bot.answer_callback_query(
            call.id, '⚠️ Request already processed!', show_alert=True
        )

    elif data.startswith('w_reject_'):
      if user_id != ADMIN_ID:
        return
      r_id = int(data.split('_')[2])
      cursor.execute(
          'UPDATE withdrawals SET status = "Rejected" WHERE id = ?', (r_id,)
      )
      conn.commit()
      bot.answer_callback_query(call.id, f'❌ Request #{r_id} Rejected!')
      safe_send_message(
          call.message.chat.id,
          f'❌ Withdrawal Request `#{r_id}` has been *Rejected*.',
      )

    conn.close()
  except Exception as e:
    print(f'Error in callback: {e}')


def process_broadcast(message):
  try:
    broadcast_text = message.text
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()

    count = 0
    for u in users:
      try:
        bot.send_message(u['user_id'], broadcast_text, parse_mode='Markdown')
        count += 1
      except Exception:
        pass

    safe_send_message(
        message.chat.id,
        f'📢 *Broadcast Completed!*\n\nSuccessfully sent to `{count}` users.',
        reply_markup=get_main_keyboard(),
    )
  except Exception as e:
    print(f'Error in broadcast: {e}')


def process_set_chan(message):
  try:
    global CHANNEL_USERNAME
    new_chan = message.text.strip()
    CHANNEL_USERNAME = new_chan
    safe_send_message(
        message.chat.id,
        f'✅ *Official Channel updated successfully to:* `{CHANNEL_USERNAME}`',
        reply_markup=get_main_keyboard(),
    )
  except Exception as e:
    print(f'Error in set channel: {e}')


if __name__ == '__main__':
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()
  print('Flask server started...')

  try:
    bot.remove_webhook()
    bot.delete_webhook(drop_pending_updates=True)
    print('Webhook successfully removed/cleared.')
  except Exception as e:
    print(f'Webhook reset error: {e}')

  print('Telegram Bot is running successfully...')
  bot.infinity_polling(skip_pending=True)
