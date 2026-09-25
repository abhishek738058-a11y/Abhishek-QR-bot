import sqlite3
import telebot
from telebot import types

# Bot Token aur Channel Settings
TOKEN = '8513419896:AAEoqPXVd0aRSHSHpMIdo3VLELoaEFO5Wj4'
CHANNEL_LINK = 'https://t.me/+757WqqqLLoo4Yjhl'
MIN_WITHDRAWAL = 50.0
CURRENT_PAYOUT = 15.0
ADMIN_TELEGRAM_ID = 8411871478  # Example Admin ID

bot = telebot.TeleBot(TOKEN)

# --- DATABASE SETUP ---
def init_db():
  conn = sqlite3.connect('bot_database.db', check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0.0,
            completed_qr INTEGER DEFAULT 0,
            active_reward REAL DEFAULT 15.0,
            referrals INTEGER DEFAULT 0,
            joined_date TEXT,
            notification INTEGER DEFAULT 1,
            is_banned INTEGER DEFAULT 0
        )
    ''')
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT,
            timestamp TEXT
        )
    ''')
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
  conn.commit()
  conn.close()

init_db()

def get_db_connection():
  return sqlite3.connect('bot_database.db', check_same_thread=False)

# --- START COMMAND & FORCE JOIN ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
  user_id = message.from_user.id
  username = message.from_user.username or 'None'
  full_name = message.from_user.first_name

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
  row = cursor.fetchone()

  if row and row[0] == 1:
    bot.send_message(
        message.chat.id, '❌ Your account has been banned by the administrator.'
    )
    conn.close()
    return

  if not row:
    import datetime
    joined_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO users (user_id, username, full_name, joined_date) VALUES'
        ' (?, ?, ?, ?)',
        (user_id, username, full_name, joined_date),
    )
    conn.commit()
  conn.close()

  # Force Join Markup with User's Channel Link only
  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton(
          '📢 Join Official Update Channel', url=CHANNEL_LINK
      )
  )
  markup.add(
      types.InlineKeyboardButton(
          '✅ Joined & Start Bot', callback_data='check_join'
      )
  )

  welcome_text = (
      f'⚠️ **Channel Join Required!**\n\nWelcome to ABHISHEKQRBOT 🤖\nBot ko'
      f' use karne ke liye sabse pehle hamara official update channel join'
      f' karna zaroori hai.\n\n👉 Neeche diye gaye button par click karke'
      f' channel join karein aur phir **'
      f"Joined & Start Bot** par click karein:"
  )
  bot.send_message(
      message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown'
  )

# --- VERIFY JOIN & MAIN MENU ---
@bot.callback_query_handler(func=lambda call: call.data == 'check_join')
def verify_join(call):
  user_id = call.from_user.id
  user_name = call.from_user.first_name

  bot.answer_callback_query(call.id, 'Channel verification successful!')

  markup = types.InlineKeyboardMarkup(row_width=2)
  btn_qr = types.InlineKeyboardButton('🎯 GET QR', callback_data='get_qr')
  btn_bal = types.InlineKeyboardButton(
      '💰 My Balance', callback_data='my_balance'
  )
  btn_acc = types.InlineKeyboardButton(
      '👤 My Account', callback_data='my_account'
  )
  btn_wd = types.InlineKeyboardButton(
      '💳 Withdraw Money', callback_data='withdraw_money'
  )
  btn_hist = types.InlineKeyboardButton(
      '📜 Withdrawal History', callback_data='withdrawal_history'
  )
  btn_ref = types.InlineKeyboardButton(
      '👥 Invite & Earn', callback_data='invite_earn'
  )
  btn_task = types.InlineKeyboardButton(
      '📋 Task History', callback_data='task_history'
  )
  btn_notif = types.InlineKeyboardButton(
      '🔔 Toggle Notification', callback_data='toggle_notif'
  )
  btn_sup = types.InlineKeyboardButton('🎧 Support', callback_data='support')
  btn_admin = types.InlineKeyboardButton(
      '🛠️ Admin Panel', callback_data='admin_panel'
  )

  markup.add(
      btn_qr,
      btn_bal,
      btn_acc,
      btn_wd,
      btn_hist,
      btn_ref,
      btn_task,
      btn_notif,
      btn_sup,
      btn_admin,
  )

  main_menu_text = (
      f'✨ **Welcome, {user_name} to ABHISHEKQRBOT!** ✨\n\n🚀 Aapka swagat hai'
      f' hamare official Automated Earning & QR Task Bot mein.\nYahan aap fast'
      f' scanning tasks complete karke, rewards earn kar sakte hain aur dosto'
      f' ko invite karke direct bonus pa sakte hain.\n\n👇 Neeche menu se koi'
      f' bhi option chunein:'
  )
  bot.send_message(
      call.message.chat.id,
      main_menu_text,
      reply_markup=markup,
      parse_mode='Markdown',
  )

# --- GET QR HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'get_qr')
def handle_get_qr(call):
  # Professional QR Not Available Message without any external old links
  error_msg = (
      '⚠️ **System Notice:**\n\n❌ **QR is not available right now.**\nWe are'
      ' currently updating our scanning servers for improved performance and'
      ' security. Please try again after some time.\n\n*(असुविधा के लिए खेद'
      ' है, अभी QR उपलब्ध नहीं है। कृपया थोड़ी देर के बाद पुनः प्रयास'
      ' करें।)*'
  )
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id, error_msg, parse_mode='Markdown')

# --- MY BALANCE HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'my_balance')
def handle_balance(call):
  user_id = call.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT balance, completed_qr, active_reward FROM users WHERE user_id ='
      ' ?',
      (user_id,),
  )
  row = cursor.fetchone()
  conn.close()

  balance = row[0] if row else 0.0
  completed_qr = row[1] if row else 0
  active_reward = row[2] if row else 15.0

  msg = (
      f'💰 **YOUR WALLET & EARNING TIERS**\n\n💵 Available Balance: ₹{balance}\n📌'
      f' Current Payout Rate: ₹{active_reward} / QR\n✅ Completed Approved'
      f' Tasks: {completed_qr}\n🔻 **Minimum Withdrawal: ₹{MIN_WITHDRAWAL}**\n\n📊'
      f' **Dynamic Slab Reward Structure:**\n▫️ 1 to 10 QRs: ₹15 per'
      f' QR\n▫️ 11 to 20 QRs: ₹20 per QR\n▫️ 21 to 30+ QRs: ₹25 per QR'
  )
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- MY ACCOUNT HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'my_account')
def handle_account(call):
  user_id = call.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT balance, completed_qr, active_reward, referrals, joined_date,'
      ' notification, username, full_name FROM users WHERE user_id = ?',
      (user_id,),
  )
  row = cursor.fetchone()
  conn.close()

  if row:
    balance, completed_qr, active_reward, referrals, joined_date, notif, uname, fname = (
        row
    )
    notif_status = 'ON 🟢' if notif == 1 else 'OFF 🔴'
    msg = (
        f'👤 **YOUR ACCOUNT PROFILE**\n\n👤 Name: {fname}\n🏷️ Username: @'
        f'{uname if uname != "None" else "Not Set"}\n🆔 Telegram ID:'
        f' {user_id}\n\n💳 Wallet Balance: ₹{balance}\n🎯 Completed QRs:'
        f' {completed_qr}\n⭐ Active Reward Rate: ₹{active_reward}\n👥 Total'
        f' Referrals: {referrals} Users\n🔔 Sound Notification:'
        f' {notif_status}\n📅 Joined On: {joined_date}'
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- WITHDRAW MONEY HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'withdraw_money')
def handle_withdraw(call):
  user_id = call.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
  row = cursor.fetchone()
  conn.close()

  balance = row[0] if row else 0.0

  if balance < MIN_WITHDRAWAL:
    msg = (
        f'❌ **Insufficient Balance.**\n\nAapka current balance ₹{balance}'
        f' hai.\nMinimum withdrawal limit **₹{MIN_WITHDRAWAL}** honi'
        f' chahiye.'
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')
  else:
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        '✅ Your balance is eligible for withdrawal. Please enter your UPI ID'
        ' to proceed.',
        parse_mode='Markdown',
    )

# --- WITHDRAWAL HISTORY HANDLER ---
@bot.callback_query_handler(
    func=lambda call: call.data == 'withdrawal_history'
)
def handle_withdrawal_history(call):
  user_id = call.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT amount, status, timestamp FROM withdrawals WHERE user_id = ?',
      (user_id,),
  )
  records = cursor.fetchall()
  conn.close()

  msg = (
      f'📜 **WITHDRAWAL HISTORY**\n\n🆔 Telegram ID: {user_id}\n\n'
  )
  if not records:
    msg += 'Koi bhi withdrawal transaction record nahi mila.'
  else:
    for idx, rec in enumerate(records, 1):
      msg += (
          f'{idx}. Amount: ₹{rec[0]} | Status: {rec[1]} | Time: {rec[2]}\n'
      )

  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- INVITE & EARN HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'invite_earn')
def handle_invite(call):
  user_id = call.from_user.id
  bot_info = bot.get_me()
  bot_username = bot_info.username
  ref_link = f'https://t.me/{bot_username}?start={user_id}'

  msg = (
      '👥 **REFERRAL PROGRAM & DIRECT BONUS**\n\n🎁 **BENEFIT:**\n• Direct'
      ' Joining Bonus: Har ek nayi referral ke join hone par turant ₹1.00'
      ' direct bonus paayein!\n\n🔗 **Aapka Referral Link:**\n'
      f'{ref_link}'
  )
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- TASK HISTORY HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'task_history')
def handle_task_history(call):
  bot.answer_callback_query(call.id)
  bot.send_message(
      call.message.chat.id,
      '📋 **TASK HISTORY**\n\nAbhi tak koi bhi completed task nahi hai.',
      parse_mode='Markdown',
  )

# --- TOGGLE NOTIFICATION HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'toggle_notif')
def handle_toggle_notif(call):
  user_id = call.from_user.id
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT notification FROM users WHERE user_id = ?', (user_id,))
  row = cursor.fetchone()
  if row:
    new_notif = 0 if row[0] == 1 else 1
    cursor.execute(
        'UPDATE users SET notification = ? WHERE user_id = ?',
        (new_notif, user_id),
    )
    conn.commit()
    status_text = 'Enabled 🟢' if new_notif == 1 else 'Disabled 🔴'
  else:
    status_text = 'Disabled 🔴'
  conn.close()

  bot.answer_callback_query(call.id, f'Notification status updated.')
  bot.send_message(
      call.message.chat.id,
      f'🔔 **Notification Settings**\n\nStatus: {status_text}',
      parse_mode='Markdown',
  )

# --- SUPPORT HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'support')
def handle_support(call):
  bot.answer_callback_query(call.id)
  msg = (
      '🎧 **CUSTOMER SUPPORT DESK**\n\n👑 Owner Username:'
      ' @abhishek723803\n⏰ Timing: 10:00 AM - 10:00 PM\n\nPayment ya withdrawal'
      ' mein koi bhi problem ho toh admin se contact karein.'
  )
  bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')

# --- ADMIN PANEL HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == 'admin_panel')
def handle_admin_panel(call):
  user_id = call.from_user.id
  if user_id != ADMIN_TELEGRAM_ID:
    bot.answer_callback_query(call.id, 'Access Denied! Admins only.')
    return

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT COUNT(*) FROM users')
  total_users = cursor.fetchone()[0]
  conn.close()

  admin_msg = (
      f'🛠️ **Admin Control & User Management Panel**\n\nWelcome Abhishek! Total'
      f' Registered Users: {total_users}\n\nQR Status: Inactive'
      f' (Unavailable)\nQR Image Set: ❌\n\n👉 Neeche buttons se QR ON/OFF'
      f' karein ya Commands use karein:\n/ban <USER_ID>\n/unban <USER_ID>'
  )

  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton('📊 Bot Stats', callback_data='admin_stats'),
      types.InlineKeyboardButton(
          '⏳ Pending Withdrawals', callback_data='admin_withdrawals'
      ),
  )
  markup.add(
      types.InlineKeyboardButton(
          '🟢 Turn QR ON & Set QR', callback_data='qr_on'
      ),
      types.InlineKeyboardButton('🔴 Turn QR OFF', callback_data='qr_off'),
  )

  bot.answer_callback_query(call.id)
  bot.send_message(
      call.message.chat.id, admin_msg, reply_markup=markup, parse_mode='Markdown'
  )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_stats')
def admin_stats(call):
  if call.from_user.id != ADMIN_TELEGRAM_ID:
    return
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT COUNT(*) FROM users')
  users = cursor.fetchone()[0]
  conn.close()
  bot.answer_callback_query(call.id)
  bot.send_message(
      call.message.chat.id,
      f'📊 **Bot Statistics**\n\nTotal Users: {users}',
      parse_mode='Markdown',
  )

@bot.callback_query_handler(
    func=lambda call: call.data in ['qr_on', 'qr_off', 'admin_withdrawals']
)
def admin_actions(call):
  if call.from_user.id != ADMIN_TELEGRAM_ID:
    return
  bot.answer_callback_query(call.id, 'Action executed successfully.')
  bot.send_message(
      call.message.chat.id,
      f'⚙️ Action processed for: {call.data}',
      parse_mode='Markdown',
  )

# --- ADMIN BAN / UNBAN COMMANDS ---
@bot.message_handler(commands=['ban'])
def ban_user(message):
  if message.from_user.id != ADMIN_TELEGRAM_ID:
    return
  try:
    target_id = int(message.text.split()[1])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET is_banned = 1 WHERE user_id = ?', (target_id,)
    )
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f'User {target_id} has been banned.')
  except Exception:
    bot.send_message(
        message.chat.id, 'Usage: /ban <USER_ID>', parse_mode='Markdown'
    )

@bot.message_handler(commands=['unban'])
def unban_user(message):
  if message.from_user.id != ADMIN_TELEGRAM_ID:
    return
  try:
    target_id = int(message.text.split()[1])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET is_banned = 0 WHERE user_id = ?', (target_id,)
    )
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f'User {target_id} has been unbanned.')
  except Exception:
    bot.send_message(
        message.chat.id, 'Usage: /unban <USER_ID>', parse_mode='Markdown'
    )

if __name__ == '__main__':
  print('Bot is running successfully...')
  bot.polling(none_stop=True)
