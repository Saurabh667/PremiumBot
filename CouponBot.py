# 8076768259:AAGLtBpn3wfUYVODgIorhKJiS8UyXTUIchQ
import telebot
from telebot import types
import random
import sqlite3 

TOKEN = "8076768259:AAGLtBpn3wfUYVODgIorhKJiS8UyXTUIchQ"
bot = telebot.TeleBot(TOKEN)
BOT_USERNAME = "SamSheinCouponBot"
ADMIN_ID = 7948227251
# saurabh
# ADMIN_ID = 5806668735

CHANNELS = [
    {"id": -1003864881307, "link": "https://t.me/+xs-ZbSI664xjNGU1"},
    {"id": -1003529660366, "link": "https://t.me/+LjK0YcaNjQ1hMmZl"},
    {"id": -1003696139523, "link": "https://t.me/+afwejn5k5adlMzE1"},
    {"id": -1003769555002, "link": "https://t.me/+_3yIBuDIn4A2MTM1"},
]


conn = sqlite3.connect("couponBot_database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    referred_by INTEGER,
    joined INTEGER DEFAULT 0
)
""")
conn.commit()

def generate_code():
    return str(random.randint(100000, 999999))
# for admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):

    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not authorized.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("📊 Total Users")
    # markup.add("➕ Add Coupon")
    # markup.add("📦 Remaining Coupons")
    # markup.add("🗑 Delete All Coupons")
    markup.add("📢 Broadcast")
    markup.add("🎯 Add Points To User")
    markup.add("⬅️ Back")

    bot.send_message(
        message.chat.id,
        "⚙️ Admin Panel",
        reply_markup=markup
    )
def add_points_to_user(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        uid, points = message.text.split()
        uid = int(uid)
        points = int(points)

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
        user = cursor.fetchone()

        if not user:
            bot.send_message(message.chat.id, "❌ User not found.")
            conn.close()
            return

        cursor.execute(
            "UPDATE users SET points = points + ? WHERE user_id = ?",
            (points, uid)
        )

        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            f"✅ Added {points} points to user {uid}"
        )

    except:
        bot.send_message(
            message.chat.id,
            "❌ Invalid format.\nUse:\nUID POINTS\nExample:\n123456789 5"
        )
def save_coupon(message):

    if message.from_user.id != ADMIN_ID:
        return

    coupon = message.text.strip()

    with open("coupon.txt", "a") as file:
        file.write(coupon + "\n")

    bot.send_message(message.chat.id, f"✅ Coupon added:\n{coupon}")
def confirm_delete_all(message):

    if message.from_user.id != ADMIN_ID:
        return

    if message.text.upper() == "YES":

        with open("coupon.txt", "w", encoding="utf-8") as file:
            file.write("")

        bot.send_message(
            message.chat.id,
            "🗑 All coupons deleted successfully."
        )

    else:
        bot.send_message(
            message.chat.id,
            "❌ Operation cancelled."
        )
def broadcast_message(message):

    text = message.text

    conn = sqlite3.connect("couponBot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    conn.close()

    count = 0

    for user in users:
        try:
            bot.send_message(user[0], text)
            count += 1
        except:
            pass

    bot.send_message(message.chat.id, f"✅ Message sent to {count} users.")
# ---------------- CHECK MEMBERSHIP ----------------
def check_membership(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel['id'], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ---------------- ADD USER ----------------

def add_user(user_id, referrer_id=None):

    conn = sqlite3.connect("couponBot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, referred_by) VALUES (?, ?)",
            (user_id, referrer_id)
        )
        conn.commit()

    conn.close()

def reward_referrer(user_id):
    conn = sqlite3.connect("couponBot_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT referred_by, joined FROM users WHERE user_id = ?", 
        (user_id,)
    )
    result = cursor.fetchone()

    if result:
        referrer_id, joined = result

        # Only reward once
        if referrer_id and joined == 0:
            cursor.execute(
                "UPDATE users SET points = points + 1 WHERE user_id = ?",
                (referrer_id,)
            )

            cursor.execute(
                "UPDATE users SET joined = 1 WHERE user_id = ?",
                (user_id,)
            )

            conn.commit()
            # Send notification to referrer
            try:
                bot.send_message(
                    referrer_id,
                    "🎉 New Referral Successful!\n\n"
                    "Someone joined using your link.\n"
                    "➕ You earned 1 point!"
                )
            except:
                pass

    conn.close()

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == user_id:
                referrer_id = None
        except:
            referrer_id = None

    add_user(user_id, referrer_id)

    if check_membership(user_id):
        reward_referrer(user_id)
        show_main_menu(message.chat.id)
    else:
        send_force_join(message.chat.id)

# ---------------- FORCE JOIN ----------------
def send_force_join(chat_id):
    markup = types.InlineKeyboardMarkup()

    for channel in CHANNELS:
        markup.add(types.InlineKeyboardButton("Join Channel", url=channel["link"]))

    markup.add(types.InlineKeyboardButton("✅ I Joined", callback_data="check_join"))
    
    bot.send_message(chat_id,"""
To get premium stock alert faster than other channels.
If u didn't beleive then try alredy more than 1k+ order has been placed""")
    bot.send_message(chat_id, "🚨 Please join all channels first:", reply_markup=markup)

# ---------------- CALLBACK ----------------
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def callback_check(call):
    user_id = call.from_user.id

    if check_membership(user_id):
        reward_referrer(user_id)
        bot.answer_callback_query(call.id, "Verified ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!")

# ---------------- MENU ----------------
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⭐️ My Points")
    markup.add("🔗 My Referral Link")
    markup.add("Redeem Points")
    # markup.add("📦 Remaining Coupons")
    markup.add("Paid Point(Purchase)")


    bot.send_message(chat_id, "🎉 Good Job!\nChoose an option:", reply_markup=markup)

# ---------------- BUTTON HANDLER ----------------
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id

    if message.text == "⭐️ My Points":
        # cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        # result = cursor.fetchone()
        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        conn.close()
        points = result[0] if result else 0
        bot.send_message(message.chat.id, f"💰 Your Points: {points}")

    elif message.text == "🔗 My Referral Link":
        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(message.chat.id, f"👥 Your Referral Link:\n{link}")
    elif message.text == "Paid Point(Purchase)":
        adminUser="@samarpit07"
        bot.send_message(message.chat.id,f"""
Contact the admin {adminUser}""")
    elif message.text == "Redeem Points":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎁 Redeem 2 Point- 1hrs")
        markup.add("🎁 Redeem 5 Point- 6hrs")
        markup.add("🎁 Redeem 12 Point- 1days")
        markup.add("🎁 Redeem 20 Point- 2days")
        markup.add("🎁 Redeem 60 Point- 7days")
        markup.add("🎁 Redeem 230 Point- 30days")
        markup.add("⬅️ Back")

        bot.send_message(
            message.chat.id,
            "Choose a redeem option:",
            reply_markup=markup
        )
    elif message.text == "⬅️ Back":
        show_main_menu(message.chat.id)
    
    # 2 points 
    elif message.text == "🎁 Redeem 2 Point- 1hrs":

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        points = result[0] if result else 0

        if points < 2:
            bot.send_message(
                message.chat.id,
                "❌ Insufficient Points!\nRefer friends to earn points."
            )
            conn.close()
            return
        
        # Read coupons
        # try:
        #     with open("coupon.txt", "r") as file:
        #         coupons = file.readlines()
        # except:
        #     bot.send_message(message.chat.id, "⚠️ Coupon file not found.")
        #     conn.close()
        #     return

        # if len(coupons) == 0:
        #     bot.send_message(message.chat.id, "❌ No coupons available right now.")
        #     conn.close()
        #     return

        # # Get first coupon
        # coupon = coupons[0].strip()

        # # Remove first coupon
        # with open("coupon.txt", "w") as file:
        #     file.writelines(coupons[1:])

        # Deduct 2 point
        cursor.execute(
            "UPDATE users SET points = points - 2 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

        conn.close()
        code = generate_code()
        cLink="https://t.me/+svfv7r3a_iQ4MDk9"
        bot.send_message(
        message.chat.id,
        f""" Congratulations,
            You Have redemed your 2 points you got acces to Premium Chanel For 1 Hours
    🔢 Your Unique Code:{code} 
Make a request on this link and share ur unique code with the admin.
Channel Link :{cLink}"""
    )
        bot.send_message(
    ADMIN_ID,
    f"""📢 New Redemption

👤 User ID: {user_id}
🔢 Code: {code}
💰 Points Used: 2
⏳ Duration: 1 Hour"""
)
    # 5 points
    elif message.text == "🎁 Redeem 5 Point- 6hrs":

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        points = result[0] if result else 0

        if points < 5:
            bot.send_message(
                message.chat.id,
                "❌ Insufficient Points!\nRefer friends to earn points."
            )
            conn.close()
            return

        # Get first coupon
        # coupon = coupons[0].strip()

        # # Remove first coupon
        # with open("coupon.txt", "w") as file:
        #     file.writelines(coupons[1:])

        # Deduct 5 point
        cursor.execute(
            "UPDATE users SET points = points - 5 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

        conn.close()
        code = generate_code()
        cLink="https://t.me/+svfv7r3a_iQ4MDk9"
        bot.send_message(
        message.chat.id,
        f""" Congratulations,
            You Have redemed your 5 points you got acces to Premium Chanel For 6 Hours
🔢 Your Unique Code:{code} 
Make a request on this link and share ur unique code with the admin.
Channel Link :{cLink}"""
    )
        bot.send_message(
    ADMIN_ID,
    f"""📢 New Redemption

👤 User ID: {user_id}
🔢 Code: {code}
💰 Points Used: 5
⏳ Duration: 6 Hour"""
)
    # 12 points
    elif message.text == "🎁 Redeem 12 Point- 1days":

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        points = result[0] if result else 0

        if points < 12:
            bot.send_message(
                message.chat.id,
                "❌ Insufficient Points!\nRefer friends to earn points."
            )
            conn.close()
            return

        # Get first coupon
        # coupon = coupons[0].strip()

        # # Remove first coupon
        # with open("coupon.txt", "w") as file:
        #     file.writelines(coupons[1:])

        # Deduct 1 point
        cursor.execute(
            "UPDATE users SET points = points - 12 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

        conn.close()
        code = generate_code()
        cLink="https://t.me/+svfv7r3a_iQ4MDk9"
        bot.send_message(
        message.chat.id,
        f""" Congratulations,
You Have redemed your 12 points you got acces to Premium Chanel For 1 day
🔢 Your Unique Code:{code}
Make a request on this link and share ur unique code with the admin.
Channel Link :{cLink}
"""
    )
        bot.send_message(
    ADMIN_ID,
    f"""📢 New Redemption

👤 User ID: {user_id}
🔢 Code: {code}
💰 Points Used: 12
⏳ Duration: 1 Day"""
)
    # 20 points
    elif message.text == "🎁 Redeem 20 Point- 2days":

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        points = result[0] if result else 0

        if points < 20:
            bot.send_message(
                message.chat.id,
                "❌ Insufficient Points!\nRefer friends to earn points."
            )
            conn.close()
            return

        # # Get first coupon
        # coupon = coupons[0].strip()

        # # Remove first coupon
        # with open("coupon.txt", "w") as file:
        #     file.writelines(coupons[1:])

        # Deduct 1 point
        cursor.execute(
            "UPDATE users SET points = points - 20 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

        conn.close()
        code = generate_code()
        cLink="https://t.me/+svfv7r3a_iQ4MDk9"
        bot.send_message(
        message.chat.id,
        f""" Congratulations,
You Have redemed your 20 points you got acces to Premium Chanel For 2 days 
🔢 Your Unique Code:{code}
Make a request on this link and share ur unique code with the admin.
Channel Link :{cLink}"""
    )
        bot.send_message(
    ADMIN_ID,
    f"""📢 New Redemption

👤 User ID: {user_id}
🔢 Code: {code}
💰 Points Used: 20
⏳ Duration: 2 Days"""
)
    # 60 points
    elif message.text == "🎁 Redeem 60 Point- 7days":

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        points = result[0] if result else 0

        if points < 60:
            bot.send_message(
                message.chat.id,
                "❌ Insufficient Points!\nRefer friends to earn points."
            )
            conn.close()
            return

        # # Get first coupon
        # coupon = coupons[0].strip()

        # # Remove first coupon
        # with open("coupon.txt", "w") as file:
        #     file.writelines(coupons[1:])

        # Deduct 1 point
        cursor.execute(
            "UPDATE users SET points = points - 60 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

        conn.close()
        code = generate_code()
        cLink="https://t.me/+svfv7r3a_iQ4MDk9"
        bot.send_message(
        message.chat.id,
        f""" Congratulations,
You Have redemed your 60 points you got acces to Premium Chanel For  7days
🔢 Your Unique Code:{code}
Make a request on this link and share ur unique code with the admin.
Channel Link :{cLink} """
    )
        bot.send_message(
    ADMIN_ID,
    f"""📢 New Redemption

👤 User ID: {user_id}
🔢 Code: {code}
💰 Points Used: 60
⏳ Duration: 7 Days"""
)
    # 256 POINTS
    elif message.text == "🎁 Redeem 230 Point- 30days":

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        points = result[0] if result else 0

        if points < 230:
            bot.send_message(
                message.chat.id,
                "❌ Insufficient Points!\nRefer friends to earn points."
            )
            conn.close()
            return

        # # Get first coupon
        # coupon = coupons[0].strip()

        # # Remove first coupon
        # with open("coupon.txt", "w") as file:
        #     file.writelines(coupons[1:])

        # Deduct 256 point
        cursor.execute(
            "UPDATE users SET points = points - 230 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

        conn.close()
        code = generate_code()
        cLink="https://t.me/+svfv7r3a_iQ4MDk9"
        bot.send_message(
        message.chat.id,
        f""" Congratulations,
            You Have redemed your 230 points you got acces to Premium Chanel For 30 days 
🔢 Your Unique Code:{code}
Make a request on this link and share ur unique code with the admin.
Channel Link :{cLink}"""
    )
        bot.send_message(
    ADMIN_ID,
    f"""📢 New Redemption

👤 User ID: {user_id}
🔢 Code: {code}
💰 Points Used: 230
⏳ Duration: 30 Days"""
)

        #features for admins 
    elif message.text == "📊 Total Users":

        if user_id != ADMIN_ID:
            return

        conn = sqlite3.connect("couponBot_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]

        conn.close()

        bot.send_message(message.chat.id, f"👥 Total Users: {total}")
    elif message.text == "🎯 Add Points To User":

        if user_id != ADMIN_ID:
            return

        msg = bot.send_message(
            message.chat.id,
            "Send user ID and points like this:\n\nUID POINTS\n\nExample:\n123456789 5"
        )

        bot.register_next_step_handler(msg, add_points_to_user)
    elif message.text == "➕ Add Coupon":

        if user_id != ADMIN_ID:
            return

        msg = bot.send_message(
            message.chat.id,
            "Send the coupon code to add:"
        )

        bot.register_next_step_handler(msg, save_coupon)
    elif message.text == "📦 Remaining Coupons":

        # if user_id != ADMIN_ID:
        #     return

        try:
            with open("coupon.txt", "r", encoding="utf-8") as file:
                coupons = file.readlines()

            total = len(coupons)

            bot.send_message(
                message.chat.id,
                f"📦 Remaining Coupons: \n ₹500 off Coupons Remaining={total}"
            )

        except FileNotFoundError:
            bot.send_message(
                message.chat.id,
                "⚠️ coupon.txt file not found."
            )
    elif message.text == "🗑 Delete All Coupons":

        if user_id != ADMIN_ID:
            return

        msg = bot.send_message(
            message.chat.id,
            "⚠️ Are you sure?\nType YES to delete all coupons."
        )

        bot.register_next_step_handler(msg, confirm_delete_all)
    elif message.text == "📢 Broadcast":

        if user_id != ADMIN_ID:
            return

        msg = bot.send_message(
            message.chat.id,
            "Send message to broadcast:"
        )

        bot.register_next_step_handler(msg, broadcast_message)

print("Bot Running...")
# bot.polling(none_stop=True, threaded=False)
# bot.polling()

# bot.infinity_polling()
bot.infinity_polling(timeout=60, long_polling_timeout=60)