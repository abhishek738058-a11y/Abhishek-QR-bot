import os
import sqlite3
import threading
from flask import Flask
import telebot
from telebot import types

API_TOKEN = '8513419896:AAFMs-OxnZE7OjWjPK8gt34cMU9Z5-w1_2E'
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
            total_withdrawn REAL DEFAULT 0.0
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
  conn.commit()
  conn.close()


init_db()


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
        'INSERT OR IGNORE INTO users (user_id, first_name, username, balance)'
        ' VALUES (?, ?, ?, 50.0)',
        (user_id, first_name, username),
    )
    cursor.execute(
        'UPDATE users SET first_name = ?, username = ? WHERE user_id = ?',
        (first_name, username, user_id),
    )
    conn.commit()
    conn.close()

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            '💰 My Balance & Stats', callback_data='my_balance'
        ),
        types.InlineKeyboardButton(
            '💸 Request Withdrawal', callback_data='request_withdrawal'
        ),
    )

    if CHANNEL_USERNAME.startswith('http'):
      markup.add(
          types.InlineKeyboardButton('📢 Official Channel', url=CHANNEL_USERNAME)
      )
    else:
      clean_chan = CHANNEL_USERNAME.replace('@', '')
      markup.add(
          types.InlineKeyboardButton(
              '📢 Official Channel', url=f'https://t.me/{clean_chan}'
          )
      )

    if user_id == ADMIN_ID:
      markup.add(
          types.InlineKeyboardButton(
              '🔐 Admin Panel', callback_data='admin_panel'
          )
      )

    safe_send_message(
        message.chat.id,
        f'👋 *Welcome, {first_name}!*\n\nAap niche diye gaye options se apni'
        ' earnings aur withdrawals manage kar sakte hain.',
        reply_markup=markup,
    )
  except Exception as e:
    print(f'Error in start: {e}')


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    data = call.data
    user_id = call.from_user.id

    if data == 'my_balance':
      cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
      user = cursor.fetchone()
      if user:
        balance = user['balance']
        earned = user['total_earned']
        withdrawn = user['total_withdrawn']
        fname = user['first_name']
        uname = user['username']

        text = (
            f'📊 *YOUR ACCOUNT STATS*\n\n👤 Name: {fname}\n🔗 Username:'
            f' @{uname}\n🆔 User ID: `{user_id}`\n💰 Current Balance:'
            f' ₹{balance:.2f}\n🎁 Total Earned: ₹{earned:.2f}\n💸 Total'
            f' Withdrawn: ₹{withdrawn:.2f}'
        )
        bot.answer_callback_query(call.id)
        safe_send_message(call.message.chat.id, text)
      else:
        bot.answer_callback_query(
            call.id, 'User not found! Please /start again.'
        )

    elif data == 'request_withdrawal':
      bot.answer_callback_query(call.id)
      msg = safe_send_message(
          call.message.chat.id,
          '💳 *Kripya apni sahi UPI ID bhejein (jaise: `yourname@paytm`):*',
      )
      bot.register_next_step_handler(msg, process_withdrawal_upi)

    elif data == 'admin_panel':
      if user_id != ADMIN_ID:
        bot.answer_callback_query(
            call.id, '⚠️ You are not authorized!', show_alert=True
        )
        return

      bot.answer_callback_query(call.id)
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
          call.message.chat.id,
          '🔐 *Admin Control Panel*\n\nNiche se koi option chunein:',
          reply_markup=markup,
      )

    elif data.startswith('admin_'):
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


def process_withdrawal_upi(message):
  try:
    user_id = message.from_user.id
    upi_id = message.text.strip()
    withdrawal_amount = 50.0

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
      )
    else:
      conn.close()
      safe_send_message(
          message.chat.id,
          f'❌ *Aapka balance kam hai!* Minimum withdrawal ₹'
          f'{withdrawal_amount:.2f} hona chahiye.',
      )
  except Exception as e:
    print(f'Error in withdrawal: {e}')


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
    )
  except Exception as e:
    print(f'Error in set channel: {e}')


if __name__ == '__main__':
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()
  print('Flask server started...')

  print('Telegram Bot is running successfully...')
  bot.infinity_polling()
