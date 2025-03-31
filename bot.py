import logging
import sqlite3
from telethon import TelegramClient, events
from datetime import datetime, timedelta
from telethon.tl.custom import Button
from telethon.errors import QueryIdInvalidError
import os
import pytz
import asyncio

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
api_id = 29584645
api_hash = '7ca25762b3e7e6b3110701394d5a291b'
bot_token = '7278713024:AAE5EZNLeGK7pfv4CS3YHdyvGk96JyBCO9Q'

# Admin configuration
ADMIN_ID = 6251161332  # Your Telegram ID

# Create the client
client = TelegramClient('bot', api_id, api_hash)

# Channel configuration
CHANNEL_USERNAME = '@airdropbymoon'
PAYMENT_LINK = "https://t.me/successcrypto2"

# Database setup
DB_FILE = "channel_messages.db"
MEDIA_DIR = "media"

# Timezone configuration
LOCAL_TIMEZONE = pytz.timezone('Asia/Kolkata')

# Create media directory if it doesn't exist
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  content TEXT,
                  media_path TEXT)''')
    
    c.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in c.fetchall()]
    if 'media_type' not in columns:
        c.execute("ALTER TABLE messages ADD COLUMN media_type TEXT")
        logger.info("Added media_type column to messages table")
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  phone_number TEXT,
                  booking_date TEXT,
                  booking_time TEXT,
                  mentorship_type TEXT,
                  payment_status TEXT DEFAULT 'pending')''')
    
    conn.commit()
    conn.close()

async def fetch_recent_posts():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT timestamp, content, media_path, media_type FROM messages ORDER BY timestamp DESC LIMIT 5")
        recent_messages = [f"[{row[0]}] {row[1]}{' [' + row[3].capitalize() + ']' if row[3] else ''}" for row in c.fetchall()]
        conn.close()
        return recent_messages or ["No recent posts detected in database"]
    except Exception as e:
        logger.error(f"Error fetching recent posts: {str(e)}")
        return ["Error fetching recent posts"]

def build_ca_calendar(year, month):
    if year < 1970 or year > 2100 or month < 1 or month > 12:
        year, month = datetime.today().year, datetime.today().month
    
    first_day = datetime(year, month, 1)
    last_day = (first_day.replace(month=month % 12 + 1) - timedelta(days=1)) if month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)
    days_in_month = last_day.day
    first_weekday = first_day.weekday()
    
    keyboard = [[Button.inline(day, data=b"ignore") for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]]
    current_row = [Button.inline(" ", data=b"ignore") for _ in range(first_weekday)]
    
    for day in range(1, days_in_month + 1):
        date_str = f"{day:02d}/{month:02d}/{year}"
        current_row.append(Button.inline(str(day), data=f"date_{date_str}".encode()))
        if len(current_row) == 7:
            keyboard.append(current_row)
            current_row = []
    
    if current_row:
        keyboard.append(current_row + [Button.inline(" ", data=b"ignore") for _ in range(7 - len(current_row))])
    
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    keyboard.append([
        Button.inline("◄", data=f"cal_{prev_year}_{prev_month}".encode()),
        Button.inline(f"{month_names[month-1]} {year}", data=b"ignore"),
        Button.inline("►", data=f"cal_{next_year}_{next_month}".encode())
    ])
    keyboard.append([Button.inline("Today", data=b"today"), Button.inline("Back", data=b"back")])
    
    return keyboard

def build_mentorship_calendar(year, month, prefix="super40"):
    if year < 1970 or year > 2100 or month < 1 or month > 12:
        year, month = datetime.today().year, datetime.today().month
    
    first_day = datetime(year, month, 1)
    last_day = (first_day.replace(month=month % 12 + 1) - timedelta(days=1)) if month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)
    days_in_month = last_day.day
    first_weekday = first_day.weekday()
    
    keyboard = [[Button.inline(day, data=b"ignore") for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]]
    current_row = [Button.inline(" ", data=b"ignore") for _ in range(first_weekday)]
    
    for day in range(1, days_in_month + 1):
        date_str = f"{day:02d}/{month:02d}/{year}"
        current_row.append(Button.inline(str(day), data=f"{prefix}_date_{date_str}".encode()))
        if len(current_row) == 7:
            keyboard.append(current_row)
            current_row = []
    
    if current_row:
        keyboard.append(current_row + [Button.inline(" ", data=b"ignore") for _ in range(7 - len(current_row))])
    
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    keyboard.append([
        Button.inline("◄", data=f"{prefix}_cal_{prev_year}_{prev_month}".encode()),
        Button.inline(f"{month_names[month-1]} {year}", data=b"ignore"),
        Button.inline("►", data=f"{prefix}_cal_{next_year}_{next_month}".encode())
    ])
    keyboard.append([Button.inline("◶ Back", data=f"{prefix}_back")])
    
    return keyboard

def build_time_menu(selected_date, prefix="super40"):
    time_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    keyboard = [[]]
    for time in time_slots:
        if len(keyboard[-1]) == 3:
            keyboard.append([])
        keyboard[-1].append(Button.inline(time, data=f"{prefix}_time_{selected_date}_{time}".encode()))
    keyboard.append([Button.inline("◶ Back", data=f"{prefix}_date_back")])
    return keyboard

def check_time_availability(date, time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE booking_date = ? AND booking_time = ?", (date, time))
    count = c.fetchone()[0]
    conn.close()
    return count < 2

async def get_current_affairs_by_date(date_str, event):
    try:
        target_date = datetime.strptime(date_str, "%d/%m/%Y")
        date_pattern = target_date.strftime("%d/%m/%Y") + "%"
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT timestamp, content, media_path, media_type FROM messages WHERE timestamp LIKE ? ORDER BY timestamp DESC", (date_pattern,))
        posts = c.fetchall()
        conn.close()
        
        if not posts:
            await event.reply(
                f"📅 *Current Affairs for {date_str}*\n\n❌ No posts found.\nCheck {CHANNEL_USERNAME} manually.",
                buttons=[[Button.inline("📅 Another Date", data=b"ca")], [Button.inline("◶ Back to Menu", data=b"back")]],
                parse_mode='Markdown'
            )
            return
        
        await event.reply(
            f"📅 *Current Affairs: {date_str}*\n📋 *Total Posts*: {len(posts)}\n═══════════════════════",
            parse_mode='Markdown'
        )
        
        for i, (timestamp, content, media_path, media_type) in enumerate(posts, 1):
            media_label = {
                "image": "📸 *Image Post*",
                "video": "🎥 *Video Post*",
                "document": "📜 *Document Post*"
            }.get(media_type, "")
            post_text = f"📌 *Post {i}*\n🕒 *Time*: {timestamp}\n📝 *Content*: {content}\n{media_label}\n───────────────────"
            await event.reply(post_text, file=media_path if media_path else None, parse_mode='Markdown')
            await asyncio.sleep(0.5)
        
        await event.edit(
            "✅ *End of Current Affairs for this date*",
            buttons=[[Button.inline("📅 Another Date", data=b"ca")], [Button.inline("◶ Back to Menu", data=b"back")]],
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error fetching CA posts: {e}")
        await event.reply(
            f"⚠️ *Error fetching Current Affairs for {date_str}*\nPlease try again later.",
            buttons=[[Button.inline("📅 Another Date", data=b"ca")], [Button.inline("◶ Back to Menu", data=b"back")]],
            parse_mode='Markdown'
        )

@client.on(events.NewMessage)
async def message_handler(event):
    chat = await event.get_chat()
    if hasattr(chat, 'username') and chat.username == CHANNEL_USERNAME[1:]:
        utc_time = event.message.date
        local_time = utc_time.replace(tzinfo=pytz.UTC).astimezone(LOCAL_TIMEZONE)
        timestamp = local_time.strftime("%d/%m/%Y %H:%M")
        
        content = event.message.message or ""
        media_path = None
        media_type = None
        
        if event.message.photo:
            file_name = f"{timestamp.replace('/', '_').replace(':', '_')}_{event.message.id}.jpg"
            media_path = os.path.join(MEDIA_DIR, file_name)
            media_type = "image"
            await event.message.download_media(file=media_path)
            logger.info(f"Downloaded image to {media_path}")
        
        elif event.message.video:
            file_name = f"{timestamp.replace('/', '_').replace(':', '_')}_{event.message.id}.mp4"
            media_path = os.path.join(MEDIA_DIR, file_name)
            media_type = "video"
            await event.message.download_media(file=media_path)
            logger.info(f"Downloaded video to {media_path}")
        
        elif event.message.document:
            file_ext = event.message.document.attributes[0].file_name.split('.')[-1] if event.message.document.attributes else "unknown"
            file_name = f"{timestamp.replace('/', '_').replace(':', '_')}_{event.message.id}.{file_ext}"
            media_path = os.path.join(MEDIA_DIR, file_name)
            media_type = "document"
            await event.message.download_media(file=media_path)
            logger.info(f"Downloaded document to {media_path}")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO messages (timestamp, content, media_path, media_type) VALUES (?, ?, ?, ?)",
                  (timestamp, content[:100], media_path, media_type))
        conn.commit()
        conn.close()
        logger.info(f"Stored message: [{timestamp}] {content[:50]}... {'[' + media_type + ']' if media_type else ''}")

    elif event.message.text:
        user_id = event.sender_id
        text = event.message.text
        
        if text.startswith("/phone_") or text.startswith("/phone_mains_"):
            parts = text.split("_", 2)
            if len(parts) < 2 or not parts[1].isdigit() or len(parts[1]) < 10:
                await event.reply(f"⚠️ Invalid phone number. Use /phone_<number> for Super 40 or /phone_mains_<number> for Mains Answer (e.g., /phone_9876543210 or /phone_mains_9876543210)", parse_mode='Markdown')
                return
            
            phone_number = parts[1]
            prefix = parts[0]
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            if prefix == "/phone":
                mentorship_type = "Super 40"
                c.execute("INSERT OR REPLACE INTO users (user_id, phone_number, mentorship_type) VALUES (?, ?, ?)", 
                          (user_id, phone_number, mentorship_type))
                conn.commit()
                conn.close()
                today = datetime.today().astimezone(LOCAL_TIMEZONE)
                keyboard = build_mentorship_calendar(today.year, today.month, "super40")
                await event.reply(
                    f"✅ *Super 40 Registration*\n📱 Phone number {phone_number} saved!\nSelect your Super 40 session date:",
                    buttons=keyboard,
                    parse_mode='Markdown'
                )

            elif prefix == "/phone_mains":
                mentorship_type = "Mains Answer"
                c.execute("SELECT booking_date, booking_time FROM users WHERE user_id = ?", (user_id,))
                booking = c.fetchone()
                if not booking or not booking[0] or not booking[1]:
                    conn.close()
                    await event.reply(
                        "⚠️ Please select a date and time for your Mains Answer evaluation first.\nUse the 'Get Your Mains Answer Evaluated' option from the menu.",
                        parse_mode='Markdown'
                    )
                    return
                
                c.execute("UPDATE users SET phone_number = ?, mentorship_type = ? WHERE user_id = ?", 
                          (phone_number, mentorship_type, user_id))
                conn.commit()
                conn.close()
                await event.reply(
                    f"✅ *Mains Answer Evaluation Booking*\n📅 *Date*: {booking[0]}\n🕒 *Time*: {booking[1]}\n📱 *Phone*: {phone_number}\n\n💳 Please complete payment to confirm your slot:",
                    buttons=[[Button.url("💳 Make Payment", PAYMENT_LINK)], [Button.inline("◶ Back", data=b"mains_date_back")]],
                    parse_mode='Markdown'
                )
                await client.send_message(
                    ADMIN_ID,
                    f"🔔 *New Mains Answer Booking*\n👤 *User ID*: {user_id}\n📱 *Phone*: {phone_number}\n📅 *Date*: {booking[0]}\n🕒 *Time*: {booking[1]}",
                    parse_mode='Markdown'
                )
            else:
                conn.close()
                await event.reply(
                    "⚠️ Invalid command. Use /phone_<number> for Super 40 or /phone_mains_<number> for Mains Answer.",
                    parse_mode='Markdown'
                )

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(
        "🤖 *Welcome to the Bot!*",
        buttons=[[Button.inline("📚 Current Affairs", data=b"ca")], [Button.inline("👥 Mentorship", data=b"appointments")], [Button.inline("◶ Back", data=b"back")]],
        parse_mode='Markdown'
    )

@client.on(events.NewMessage(pattern='/admin'))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("⚠️ You are not authorized to access admin features.", parse_mode='Markdown')
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, phone_number, booking_date, booking_time, mentorship_type, payment_status FROM users WHERE phone_number IS NOT NULL")
    users = c.fetchall()
    conn.close()
    
    if not users:
        await event.reply("📋 *Admin Panel*\n\nNo registered mentees found.", parse_mode='Markdown')
        return
    
    admin_text = "📋 *Admin Panel - Mentee List*\n\n"
    for user_id, phone, date, time, m_type, payment_status in users[:20]:
        status_emoji = "✅" if payment_status == "completed" else "⏳"
        admin_text += f"👤 *User ID*: {user_id}\n📞 *Phone*: {phone}\n📅 *Date*: {date or 'Not Booked'}\n🕒 *Time*: {time or 'Not Booked'}\n🎓 *Type*: {m_type}\n💳 *Payment*: {status_emoji} {payment_status.title()}\n───────────────────\n"
    
    total_users = len(users)
    paid_users = sum(1 for u in users if u[5] == "completed")
    admin_text += f"\n📊 *Summary*:\n• Total Mentees: {total_users}\n• Payment Completed: {paid_users}\n• Payment Pending: {total_users - paid_users}"
    await event.reply(admin_text, parse_mode='Markdown')

@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    user_id = event.sender_id
    
    try:
        if data == 'ca':
            today = datetime.today().astimezone(LOCAL_TIMEZONE)
            keyboard = build_ca_calendar(today.year, today.month)
            await event.edit("📅 *Select a date for Current Affairs:*", buttons=keyboard, parse_mode='Markdown')
        
        elif data.startswith("today_ca_"):
            await get_current_affairs_by_date(data.split("_")[2], event)
        
        elif data.startswith("date_"):
            selected_date = data.split("_")[1]
            await event.edit(
                f"📅 *Selected Date: {selected_date}*\n\nClick 'Today's Current Affairs' to view posts.",
                buttons=[[Button.inline("📚 Today's Current Affairs", data=f"today_ca_{selected_date}".encode())], [Button.inline("◶ Back", data=b"ca")]],
                parse_mode='Markdown'
            )
        
        elif data.startswith("cal_"):
            _, year, month = data.split("_")
            keyboard = build_ca_calendar(int(year), int(month))
            await event.edit("📅 *Select a date for Current Affairs:*", buttons=keyboard, parse_mode='Markdown')
        
        elif data == "today":
            today_str = datetime.today().astimezone(LOCAL_TIMEZONE).strftime("%d/%m/%Y")
            await event.edit(
                f"📅 *Today: {today_str}*\n\nClick 'Today's Current Affairs' to view posts.",
                buttons=[[Button.inline("📚 Today's Current Affairs", data=f"today_ca_{today_str}".encode())], [Button.inline("◶ Back", data=b"ca")]],
                parse_mode='Markdown'
            )
        
        elif data == 'appointments':
            await event.edit(
                "*Choose a Mentorship Option:*\n\n1️⃣ *Super 40*: Special mentorship program\n2️⃣ *Open Mentorship*: General mentorship options\n3️⃣ *Get Your Mains Answer Evaluated*: Answer evaluation",
                buttons=[
                    [Button.inline("🎯 1. Super 40", data=b"super40")],
                    [Button.inline("👥 2. Open Mentorship", data=b"open_mentorship")],
                    [Button.inline("📝 3. Get Your Mains Answer Evaluated", data=b"main_answer")],
                    [Button.inline("◶ 4. Back", data=b"back")]
                ],
                parse_mode='Markdown'
            )
        
        elif data == 'main_answer':
            today = datetime.today().astimezone(LOCAL_TIMEZONE)
            keyboard = build_mentorship_calendar(today.year, today.month, "mains")
            await event.edit("*Get Your Mains Answer Evaluated*\n\n📅 Select your preferred date:", buttons=keyboard, parse_mode='Markdown')
        
        elif data.startswith("mains_date_"):
            selected_date = data.split("_")[2]
            keyboard = build_time_menu(selected_date, "mains")
            await event.edit(f"📅 *Selected Date: {selected_date}*\n🕒 Select your preferred time slot:", buttons=keyboard, parse_mode='Markdown')
        
        elif data.startswith("mains_cal_"):
            _, year, month = data.split("_")[2:]
            keyboard = build_mentorship_calendar(int(year), int(month), "mains")
            await event.edit("📅 *Select your evaluation date:*", buttons=keyboard, parse_mode='Markdown')
        
        elif data.startswith("mains_time_"):
            parts = data.split("_")
            selected_date, selected_time = parts[2], parts[3]
            if check_time_availability(selected_date, selected_time):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO users (user_id, booking_date, booking_time, mentorship_type) VALUES (?, ?, ?, ?)",
                          (user_id, selected_date, selected_time, "Mains Answer"))
                conn.commit()
                conn.close()
                await event.edit(
                    f"✅ *Time Slot Selected*\n📅 *Date*: {selected_date}\n🕒 *Time*: {selected_time}\n\n📱 Provide your phone number:\nType: /phone_mains_<number>\nExample: /phone_mains_9876543210",
                    parse_mode='Markdown'
                )
            else:
                keyboard = build_time_menu(selected_date, "mains")
                await event.edit(f"⚠️ *Time slot {selected_time} on {selected_date} is unavailable.*\nSelect another time:", buttons=keyboard, parse_mode='Markdown')
        
        elif data == "mains_date_back":
            today = datetime.today().astimezone(LOCAL_TIMEZONE)
            keyboard = build_mentorship_calendar(today.year, today.month, "mains")
            await event.edit("📅 *Select your evaluation date:*", buttons=keyboard, parse_mode='Markdown')
        
        elif data == "super40":
            await event.edit(
                "🎯 *Super 40 Mentorship*\nAre you a Super 40 mentee?",
                buttons=[
                    [Button.inline("✅ Yes", data=b"super40_yes")],
                    [Button.inline("❌ No", data=b"super40_no")]
                ],
                parse_mode='Markdown'
            )
        
        elif data == "super40_yes":
            today = datetime.today().astimezone(LOCAL_TIMEZONE)
            keyboard = build_mentorship_calendar(today.year, today.month, "super40")
            await event.edit(
                "🎯 *Super 40 Mentorship*\nGreat! Please select your session date:",
                buttons=keyboard,
                parse_mode='Markdown'
            )
        
        elif data == "super40_no":
            await event.edit(
                "🎯 *Super 40 Mentorship*\nAre you a Super 40 mentee?",
                buttons=[
                    [Button.inline("✅ Yes", data=b"super40_yes")],
                    [Button.inline("❌ No", data=b"super40_no")]
                ],
                parse_mode='Markdown'
            )
        
        elif data.startswith("super40_date_"):
            selected_date = data.split("_")[2]
            keyboard = build_time_menu(selected_date, "super40")
            await event.edit(
                f"📅 *Selected Date: {selected_date}*\n🕒 Please select your Super 40 time slot:",
                buttons=keyboard,
                parse_mode='Markdown'
            )
        
        elif data.startswith("super40_cal_"):
            _, year, month = data.split("_")[2:]
            keyboard = build_mentorship_calendar(int(year), int(month), "super40")
            await event.edit(
                "🎯 *Super 40 Mentorship*\nGreat! Please select your session date:",
                buttons=keyboard,
                parse_mode='Markdown'
            )
        
        elif data == "super40_back":
            await event.edit(
                "🎯 *Super 40 Mentorship*\nAre you a Super 40 mentee?",
                buttons=[
                    [Button.inline("✅ Yes", data=b"super40_yes")],
                    [Button.inline("❌ No", data=b"super40_no")]
                ],
                parse_mode='Markdown'
            )
        
        elif data.startswith("super40_time_"):
            parts = data.split("_")
            selected_date, selected_time = parts[2], parts[3]
            if check_time_availability(selected_date, selected_time):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO users (user_id, booking_date, booking_time, mentorship_type) VALUES (?, ?, ?, ?)",
                          (user_id, selected_date, selected_time, "Super 40"))
                conn.commit()
                conn.close()
                await event.edit(
                    f"✅ *Booking Confirmed!*\n📅 *Date*: {selected_date}\n🕒 *Time*: {selected_time}\nThank you for booking your Super 40 session!",
                    buttons=[[Button.inline("◶ Back to Main Menu", data=b"main_menu")]],
                    parse_mode='Markdown'
                )
                await client.send_message(
                    ADMIN_ID,
                    f"🔔 *New Super 40 Booking*\n👤 *User ID*: {user_id}\n📅 *Date*: {selected_date}\n🕒 *Time*: {selected_time}",
                    parse_mode='Markdown'
                )
            else:
                keyboard = build_time_menu(selected_date, "super40")
                await event.edit(
                    f"⚠️ *Time slot {selected_time} on {selected_date} is unavailable.*\nSelect another time:",
                    buttons=keyboard,
                    parse_mode='Markdown'
                )
        
        elif data == "super40_date_back":
            today = datetime.today().astimezone(LOCAL_TIMEZONE)
            keyboard = build_mentorship_calendar(today.year, today.month, "super40")
            await event.edit(
                "🎯 *Super 40 Mentorship*\nGreat! Please select your session date:",
                buttons=keyboard,
                parse_mode='Markdown'
            )
        
        elif data == 'open_mentorship':
            await event.edit("*Open Mentorship Registration*\n\nPlease provide your phone number using /phone_open_<number>\nExample: /phone_open_9876543210", parse_mode='Markdown')
        
        elif data.startswith("open_date_"):
            selected_date = data.split("_")[2]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT phone_number FROM users WHERE user_id = ?", (user_id,))
            phone = c.fetchone()
            conn.close()
            if not phone or not phone[0]:
                await event.edit("⚠️ Please provide your phone number first using /phone_open_<number>", parse_mode='Markdown')
                return
            keyboard = build_time_menu(selected_date, "open")
            await event.edit(f"📅 *Selected Date: {selected_date}*\nPlease select your Open Mentorship time slot:", buttons=keyboard, parse_mode='Markdown')
        
        elif data.startswith("open_cal_"):
            _, year, month = data.split("_")[2:]
            keyboard = build_mentorship_calendar(int(year), int(month), "open")
            await event.edit("📅 *Select your Open Mentorship session date:*", buttons=keyboard, parse_mode='Markdown')
        
        elif data == "open_back":
            await event.edit("*Open Mentorship Registration*\n\nPlease provide your phone number using /phone_open_<number>\nExample: /phone_open_9876543210", parse_mode='Markdown')
        
        elif data.startswith("open_time_"):
            parts = data.split("_")
            selected_date, selected_time = parts[2], parts[3]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT phone_number FROM users WHERE user_id = ?", (user_id,))
            phone = c.fetchone()[0]
            if check_time_availability(selected_date, selected_time):
                c.execute("UPDATE users SET booking_date = ?, booking_time = ? WHERE user_id = ?", (selected_date, selected_time, user_id))
                conn.commit()
                conn.close()
                await event.edit(
                    f"✅ *Open Mentorship Slot Reserved!*\n📅 *Date*: {selected_date}\n🕒 *Time*: {selected_time}\n📱 *Phone*: {phone}\n\nPlease complete payment to confirm:",
                    buttons=[[Button.url("💳 Make Payment", PAYMENT_LINK)], [Button.inline("◶ Back", data=b"open_date_back")]],
                    parse_mode='Markdown'
                )
                await client.send_message(ADMIN_ID, f"🔔 *New Open Mentorship Booking*\n👤 *User ID*: {user_id}\n📱 *Phone*: {phone}\n📅 *Date*: {selected_date}\n🕒 *Time*: {selected_time}", parse_mode='Markdown')
            else:
                conn.close()
                keyboard = build_time_menu(selected_date, "open")
                await event.edit(f"⚠️ *Time slot {selected_time} on {selected_date} is unavailable.*\nSelect another time:", buttons=keyboard, parse_mode='Markdown')
        
        elif data == "open_date_back":
            today = datetime.today().astimezone(LOCAL_TIMEZONE)
            keyboard = build_mentorship_calendar(today.year, today.month, "open")
            await event.edit("📅 *Select your Open Mentorship session date:*", buttons=keyboard, parse_mode='Markdown')
        
        elif data == 'back':
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT mentorship_type FROM users WHERE user_id = ?", (user_id,))
            mentorship_type = c.fetchone()
            conn.close()
            if mentorship_type and mentorship_type[0] == "Mains Answer":
                await event.edit(
                    "*Get Your Mains Answer Evaluated*\n\nContinue with your evaluation booking?",
                    buttons=[[Button.inline("📝 Continue", data=b"main_answer")], [Button.inline("◶ Main Menu", data=b"main_menu")]],
                    parse_mode='Markdown'
                )
            else:
                await event.edit(
                    "🤖 *Welcome to the Bot!*",
                    buttons=[[Button.inline("📚 Current Affairs", data=b"ca")], [Button.inline("👥 Mentorship", data=b"appointments")], [Button.inline("◶ Back", data=b"back")]],
                    parse_mode='Markdown'
                )
        
        elif data == "main_menu":
            await event.edit(
                "🤖 *Welcome to the Bot!*",
                buttons=[[Button.inline("📚 Current Affairs", data=b"ca")], [Button.inline("👥 Mentorship", data=b"appointments")], [Button.inline("◶ Back", data=b"back")]],
                parse_mode='Markdown'
            )
    
    except QueryIdInvalidError as e:
        logger.error(f"QueryIdInvalidError: {str(e)}")
        await event.reply("⚠️ This button is no longer valid. Please use the latest message.")
    except Exception as e:
        logger.error(f"Unexpected error in callback_handler: {str(e)}")
        await event.reply("⚠️ An error occurred. Please try again later.")

async def main():
    init_db()
    await client.start(bot_token=bot_token)
    try:
        chat = await client.get_entity(CHANNEL_USERNAME)
        logger.info(f"Bot accessed {CHANNEL_USERNAME} (ID: {chat.id})")
    except Exception as e:
        logger.error(f"Failed to access {CHANNEL_USERNAME}: {str(e)}")
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())