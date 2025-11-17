import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from datetime import datetime, timedelta

# --- Bot sozlamalari ---
TOKEN = "8113479785:AAEUnC7EFtM4mupcMXfUKs2VhaNf5o-YTA8"
GROUP_ID = -1002850022891  # Guruh IDsi
TOPIC_ID = 52  # Topic IDsi (zakazlar tushadigan forum topic)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Foydalanuvchilar ---
USERS = {7731365451: "admin"}  # Admin IDsi va roli

# --- Viloyat va tumanlar ---
REGIONS = {
    "Toshkent shahri": ["Olmazor", "Shayxontohur", "Yashnobod", "Chilonzor", "Mirzo Ulug'bek", "Uchtepa", "Yunusobod", "Bektemir", "Mirobod", "Sergeli", "Yangihayot"],
    "Toshkent viloyati": ["Bekobod", "Bo‘ka", "Bo‘stonliq", "Zangiota", "Ohangaron", "Parkent", "Piskent", "Chinoz", "Yuqori Chirchiq", "Yangiyo‘l", "O‘rta Chirchiq", "Qibray", "Quyi Chirchiq"],
    "Samarqand viloyati": ["Samarqand", "Bulung‘ur", "Jomboy", "Kattaqo‘rg‘on", "Narpay", "Oqdaryo", "Paxtachi", "Payariq", "Past Darg‘om", "Qo‘shrabot", "Registon", "Siyob", "Toyloq", "Urgut"],
    "Buxoro viloyati": ["Buxoro", "G‘ijduvon", "Jondor", "Kogon", "Olot", "Peshku", "Qorako‘l", "Qorovulbozor", "Romitan", "Shofirkon", "Vobkent"],
    "Andijon viloyati": ["Andijon", "Asaka", "Baliqchi", "Bo‘z", "Izboskan", "Jalaquduq", "Marhamat", "Oltinko‘l", "Shahrixon", "Ulug‘nor", "Xo‘jaobod", "Xonobod", "Yangiqo‘rg‘on"],
    "Farg‘ona viloyati": ["Farg‘ona", "Qo‘qon", "Marg‘ilon", "Beshariq", "Bag‘dod", "Buvayda", "Dang‘ara", "Furqat", "Qo‘shtepa", "Quva", "Rishton", "So‘x", "Toshloq", "Uchko‘prik", "Yozyovon", "Yorqin"],
    "Namangan viloyati": ["Namangan", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin", "Pop", "To‘raqo‘rg‘on", "Uchqo‘rg‘on", "Uychi", "Yangiqo‘rg‘on"],
    "Jizzax viloyati": ["Jizzax", "Arnasoy", "Baxmal", "Do‘stlik", "Forish", "G‘allaorol", "Mirzacho‘l", "Paxtakor", "Sharof Rashidov", "Yangiobod", "Zomin", "Zarbdor", "Zafarobod"],
    "Sirdaryo viloyati": ["Guliston", "Boyovut", "Mirzaobod", "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo", "Xovos"],
    "Qashqadaryo viloyati": ["Qarshi", "Chiroqchi", "G‘uzor", "Koson", "Mirishkor", "Muborak", "Nishon", "Shahrisabz", "Yakkabog‘"],
    "Surxondaryo viloyati": ["Termiz", "Angor", "Boysun", "Denov", "Jarqo‘rg‘on", "Muzrobod", "Oltinsoy", "Sariosiyo", "Uzun", "Sherobod"],
    "Navoiy viloyati": ["Navoiy", "Karmana", "Tomdi", "Qiziltepa", "Navbahor", "Zafarabad", "Uchquduq", "Konimex", "Nurota"],
    "Xorazm viloyati": ["Urganch", "Gurlan", "Shovot", "Yangibozor", "Xonqa", "Xiva", "Yangiariq", "Hazorasp"],
    "Qoraqalpog‘iston Respublikasi": ["Nukus", "Amudaryo", "Beruniy", "Bo‘zatov", "Ellikqal’a", "Kegeyli", "Qanliko‘l", "Qorao‘zak", "Shumanay", "Tuproqqum", "Xo‘jayli"]
}

# --- Kitoblar ---
BOOKS = ["Kayzen", "Biznesni qadamba qadam tizimlashtirish ", "37-qoida","Yengil venchur","Nega ular ishlamaydi","Marketingda rad etib bo'lmaydigan 150-uslub","Cheksiz mijozlar oqimiga ega bo'lishda 440 amaliy keys","Pulni onasini bilasizmi","Biznes va Islom"]

# --- Global ma’lumotlar ---
user_data_dict = {}
orders_history = {}
order_counter = 0

# --- Klaviaturalar ---
def make_keyboard(options):
    return InlineKeyboardMarkup([[InlineKeyboardButton(opt, callback_data=opt)] for opt in options])

def book_keyboard(selected_books):
    buttons = []
    for book in BOOKS:
        text = f"✅ {book}" if book in selected_books else book
        buttons.append([InlineKeyboardButton(text, callback_data=f"book_{book}")])
    buttons.append([InlineKeyboardButton("✔️ Tanlash tugadi", callback_data="done_books")])
    return InlineKeyboardMarkup(buttons)

def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Naqt", callback_data="pay_cash")],
        [InlineKeyboardButton("Karta", callback_data="pay_card")]
    ])

def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_order")]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Bugungi sotuv", callback_data="report_day")],
        [InlineKeyboardButton("📆 Oylik sotuv", callback_data="report_month")],
        [InlineKeyboardButton("👤 AddUser", callback_data="add_user")]
    ])

def role_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Admin", callback_data="role_admin")],
        [InlineKeyboardButton("Hodim", callback_data="role_hodim")]
    ])

def date_selection_keyboard(start_date, days=7):
    buttons = []
    for i in range(days):
        d = start_date - timedelta(days=i)
        text = d.strftime("%Y-%m-%d")
        buttons.append([InlineKeyboardButton(text, callback_data=f"date_{text}")])
    return InlineKeyboardMarkup(buttons)

def month_selection_keyboard(year):
    months = [f"{m:02d}" for m in range(1, 13)]
    buttons = []
    for m in months:
        date = f"{year}-{m}"
        buttons.append([InlineKeyboardButton(date, callback_data=f"month_{date}")])
    return InlineKeyboardMarkup(buttons)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    role = USERS.get(user_id, "hodim")
    keyboard = [[InlineKeyboardButton("➕ Yangi zakaz", callback_data="new_order")]]
    if role == "admin":
        keyboard.append([InlineKeyboardButton("📊 Admin Panel", callback_data="admin_panel")])
    await update.message.reply_text("Assalomu alaykum! Menyudan tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Sotuv hisobot ---
async def send_sales_report(update, context, report_date, admin_private=False):
    orders = orders_history.get(report_date, [])
    if not orders:
        text = f"{report_date} kuni zakaz yo‘q."
        if admin_private:
            await update.callback_query.message.reply_text(text)
        else:
            await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=TOPIC_ID, text=text)
        return

    total_sum = sum(o["total"] for o in orders)
    region_count = {}
    book_count = {}
    for o in orders:
        region_count[o["region"]] = region_count.get(o["region"], 0) + 1
        for book in o["books"]:
            book_count[book] = book_count.get(book, 0) + 1

    text = f"📅 {report_date} sotuvlar:\n💰 Jami summa: {total_sum} so‘m\n\nViloyat bo‘yicha:\n"
    for r, c in region_count.items(): text += f"- {r}: {c} ta zakaz\n"
    text += "\nKitob bo‘yicha:\n"
    for b, c in book_count.items(): text += f"- {b}: {c} ta\n"

    if admin_private:
        await update.callback_query.message.reply_text(text)
    else:
        await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=TOPIC_ID, text=text)

# --- Callback handler ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_counter
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    role = USERS.get(user_id, "hodim")

    # ===========================
    # Sotuv bo‘limi
    # ===========================
    if data == "new_order":
        order_counter += 1
        today = datetime.now().strftime("%Y-%m-%d")
        user_data_dict[user_id] = {"order_id": order_counter, "date": today, "seller": query.from_user.full_name, "books": []}
        await query.message.reply_text("👤 Mijoz ismini kiriting:")
        context.user_data["step"] = "name"
        return

    if data in REGIONS.keys() and context.user_data.get("step") == "region":
        user_data_dict[user_id]["region"] = data
        keyboard = make_keyboard(REGIONS[data])
        await query.message.reply_text("📍 Tumanni tanlang:", reply_markup=keyboard)
        context.user_data["step"] = "district"
        return

    if context.user_data.get("step") == "district" and any(data in v for v in REGIONS.values()):
        user_data_dict[user_id]["district"] = data
        await query.message.reply_text("📚 Kitoblarni tanlang:", reply_markup=book_keyboard([]))
        context.user_data["step"] = "books"
        return

    if data.startswith("book_") and context.user_data.get("step") == "books":
        book = data.replace("book_", "")
        if book not in user_data_dict[user_id]["books"]:
            user_data_dict[user_id]["books"].append(book)
        else:
            user_data_dict[user_id]["books"].remove(book)
        await query.message.edit_text("📚 Kitoblarni tanlang:", reply_markup=book_keyboard(user_data_dict[user_id]["books"]))
        return

    if data == "done_books" and context.user_data.get("step") == "books":
        await query.message.reply_text("💳 To‘lov turini tanlang:", reply_markup=payment_keyboard())
        context.user_data["step"] = "payment"
        return

    if data.startswith("pay_") and context.user_data.get("step") == "payment":
        user_data_dict[user_id]["payment"] = data.replace("pay_", "")
        await query.message.reply_text("💰 Umumiy summani kiriting (so‘m):")
        context.user_data["step"] = "total"
        return

    if data == "confirm_order":
        d = user_data_dict[user_id]
        summary = (f"🆔 Zakaz ID: {d['order_id']}\n"
                   f"👤 Mijoz: {d['name']}\n"
                   f"📱 Telefon: {d['phone']}\n"
                   f"📍 Manzil: {d['region']}, {d['district']}\n"
                   f"📚 Kitoblar: {', '.join(d['books'])}\n"
                   f"💳 To‘lov turi: {d['payment']}\n"
                   f"💰 Umumiy summa: {d['total']} so‘m\n"
                   f"💵 Avans: {d['advance']} so‘m\n"
                   f"💸 Qolgan summa: {d['total'] - d['advance']} so‘m\n"
                   f"📝 Izoh: {d['note']}\n"
                   f"👨‍💼 Sotuvchi: {d['seller']}\n"
                   f"📅 Sana: {d['date']}")
        await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=TOPIC_ID, text=summary)
        await query.message.reply_text("✅ Zakaz tasdiqlandi va guruhga yuborildi.")
        orders_history.setdefault(d["date"], []).append(d)
        context.user_data["step"] = None
        del user_data_dict[user_id]
        return

    if data == "cancel_order":
        await query.message.reply_text("❌ Zakaz bekor qilindi.")
        context.user_data["step"] = None
        if user_id in user_data_dict:
            del user_data_dict[user_id]
        return

    # ===========================
    # Admin panel
    # ===========================
    if role != "admin":
        return

    if data == "admin_panel":
        await query.message.reply_text("Admin panel:", reply_markup=admin_panel_keyboard())
        return

    if data == "report_day":
        today = datetime.now().strftime("%Y-%m-%d")
        await send_sales_report(update, context, today, admin_private=True)
        return

    if data == "report_month":
        year = datetime.now().year
        await query.message.reply_text("📅 Oyni tanlang:", reply_markup=month_selection_keyboard(year))
        return

    if data.startswith("month_"):
        selected_month = data.replace("month_", "")  # masalan: 2025-09
        year, month = map(int, selected_month.split("-"))
        start_date = datetime(year, month, 1)

        # Oydagi kunlar soni
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - start_date).days

        buttons = []
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            buttons.append([InlineKeyboardButton(date_str, callback_data=f"date_{date_str}")])

        # "Oy bo‘yicha umumiy statistika" tugmasi
        buttons.append([InlineKeyboardButton(f"📊 {selected_month} umumiy statistika", callback_data=f"month_report_{selected_month}")])

        await query.message.reply_text(f"📅 {selected_month} uchun sanani tanlang:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("month_report_"):
        selected_month = data.replace("month_report_", "")  # masalan: 2025-09
        orders = []
        for date_str, daily_orders in orders_history.items():
            if date_str.startswith(selected_month):
                orders.extend(daily_orders)

        if not orders:
            await query.message.reply_text(f"{selected_month} oyida zakaz yo‘q.")
            return

        total_sum = sum(o["total"] for o in orders)
        region_count = {}
        book_count = {}
        for o in orders:
            region_count[o["region"]] = region_count.get(o["region"], 0) + 1
            for book in o["books"]:
                book_count[book] = book_count.get(book, 0) + 1

        text = f"📆 {selected_month} oylik sotuvlar:\n💰 Jami summa: {total_sum} so‘m\n\nViloyat bo‘yicha:\n"
        for r, c in region_count.items(): text += f"- {r}: {c} ta zakaz\n"
        text += "\nKitob bo‘yicha:\n"
        for b, c in book_count.items(): text += f"- {b}: {c} ta\n"

        await query.message.reply_text(text)
        return

    if data.startswith("date_"):
        selected_date = data.replace("date_","")
        await send_sales_report(update, context, selected_date, admin_private=True)
        return

    if data == "add_user":
        await query.message.reply_text("👤 Hodim ismini kiriting:")
        context.user_data["step"] = "add_user_name"
        return

    if data in ["role_admin", "role_hodim"] and context.user_data.get("step") == "add_user_role":
        new_id = context.user_data["new_user_id"]
        new_name = context.user_data["new_user_name"]
        USERS[new_id] = "admin" if data == "role_admin" else "hodim"
        await query.message.reply_text(f"✅ {new_name} muvaffaqiyatli qo‘shildi: {new_id} → {USERS[new_id]}")
        context.user_data["step"] = None
        return

# --- Matnli javoblar ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    step = context.user_data.get("step")

    if step == "name":
        user_data_dict[user_id]["name"] = update.message.text
        await update.message.reply_text("📞 Telefon raqamini kiriting (13 belgili, masalan: +998901234567):")
        context.user_data["step"] = "phone"
        return

    if step == "phone":
        phone = update.message.text
        if not (phone.startswith("+998") and len(phone) == 13 and phone[1:].isdigit()):
            await update.message.reply_text("❌ Noto‘g‘ri raqam. Iltimos, +998 bilan boshlanadigan 13 belgili raqam kiriting.")
            return
        user_data_dict[user_id]["phone"] = phone
        keyboard = make_keyboard(list(REGIONS.keys()))
        await update.message.reply_text("📍 Viloyatni tanlang:", reply_markup=keyboard)
        context.user_data["step"] = "region"
        return

    if step == "total":
        try:
            total = int(update.message.text)
            user_data_dict[user_id]["total"] = total
            await update.message.reply_text("💵 Avans summasini kiriting:")
            context.user_data["step"] = "advance"
        except:
            await update.message.reply_text("❌ Son kiritish kerak.")
        return

    if step == "advance":
        try:
            advance = int(update.message.text)
            user_data_dict[user_id]["advance"] = advance
            await update.message.reply_text("📝 Izoh kiriting:")
            context.user_data["step"] = "note"
        except:
            await update.message.reply_text("❌ Son kiritish kerak.")
        return

    if step == "note":
        user_data_dict[user_id]["note"] = update.message.text
        await update.message.reply_text("✅ Hammasi to‘g‘rimi?", reply_markup=confirm_keyboard())
        context.user_data["step"] = "confirm"
        return

    if step == "add_user_name":
        context.user_data["new_user_name"] = update.message.text
        await update.message.reply_text("🆔 Foydalanuvchi Telegram ID sini kiriting:")
        context.user_data["step"] = "add_user_id"
        return

    if step == "add_user_id":
        try:
            new_id = int(update.message.text)
            context.user_data["new_user_id"] = new_id
            await update.message.reply_text("Rolni tanlang:", reply_markup=role_keyboard())
            context.user_data["step"] = "add_user_role"
        except:
            await update.message.reply_text("❌ ID faqat son bo‘lishi kerak.")
        return

# --- Main ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
