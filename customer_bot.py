"""
ORZUGUL — Mijoz Boti (@OrzugulBot)
Gul va shirinlik buyurtma berish + Telegram Mini App
"""
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from config import (
    CUSTOMER_BOT_TOKEN, SHOP_BOT_TOKEN, ADMIN_IDS,
    WEBAPP_URL, WELCOME_CUSTOMER, ORDER_NOTIFICATION
)
from database import db

# ── Buyurtma bosqichlari ──────────────────────────
(
    ORD_PHONE, ORD_TYPE, ORD_QTY,
    ORD_ADDRESS, ORD_CONFIRM
) = range(5)


# ════════════════════════════════════════════════
#  YORDAMCHI
# ════════════════════════════════════════════════

def fmt_price(p): return f"{p:,}".replace(",", " ")

MAIN_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌸 Gullar", callback_data="cat_flower"),
     InlineKeyboardButton("🍰 Shirinliklar", callback_data="cat_sweet")],
    [InlineKeyboardButton("📱 Mini App (barcha do'konlar)", web_app=WebAppInfo(url=WEBAPP_URL))],
    [InlineKeyboardButton("📦 Mening zakazlarim", callback_data="my_orders")],
])


def product_info(p: dict) -> str:
    if p["product_type"] == "flower":
        return (
            f"🌸 *{p['name']}*\n"
            f"   • Dona: {fmt_price(p['single_price'])} so'm\n"
            f"   • Buket: {fmt_price(p['bouquet_price'])} so'm\n"
            f"   🚚 Yetkazib berish: {'Ha ✅' if p['flower_delivery'] else 'Yo\'q ❌'}"
        )
    else:
        return (
            f"🍰 *{p['name']}*\n"
            f"   • Bo'lak: {fmt_price(p['piece_price'])} so'm\n"
            f"   • Butun: {fmt_price(p['full_price'])} so'm\n"
            f"   🚚 Yetkazib berish: {'Ha ✅' if p['sweet_delivery'] else 'Yo\'q ❌'}"
        )


# ════════════════════════════════════════════════
#  /start
# ════════════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.upsert_customer(user.id, user.username, user.full_name)
    ctx.user_data.clear()

    await update.message.reply_text(
        f"👋 Salom, *{user.first_name}*!\n\n"
        "🌸 *ORZUGUL* — eng yaxshi gullar va shirinliklar\n\n"
        "Nima buyurtma qilmoqchisiz?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MAIN_KB
    )


# ════════════════════════════════════════════════
#  KATEGORIYA TANLASH
# ════════════════════════════════════════════════

async def category_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cat = q.data.split("_")[1]  # flower | sweet
    ctx.user_data["category"] = cat

    shops = await db.get_shops_by_type(cat)
    if not shops:
        await q.edit_message_text(
            f"{'🌸 Gul' if cat == 'flower' else '🍰 Shirinlik'} do'konlari hali yo'q.\n"
            "Tez orada qo'shiladi! 🙏",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_main")]])
        )
        return

    icon = "🌸" if cat == "flower" else "🍰"
    kb = [[InlineKeyboardButton(f"{icon} {s['name']}", callback_data=f"shop_{s['id']}")]
          for s in shops]
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")])

    await q.edit_message_text(
        f"{icon} *{'Gul' if cat == 'flower' else 'Shirinlik'} do'konlari*\n\n"
        f"Quyidagi do'konlardan birini tanlang:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ════════════════════════════════════════════════
#  DO'KON TANLASH
# ════════════════════════════════════════════════

async def shop_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    shop_id = int(q.data.split("_")[1])
    shop = await db.get_shop_by_id(shop_id)
    if not shop:
        await q.edit_message_text("Do'kon topilmadi.")
        return

    ctx.user_data["shop_id"] = shop_id
    ctx.user_data["shop_name"] = shop["name"]

    products = await db.get_products_by_shop(shop_id)
    if not products:
        await q.edit_message_text(
            f"🏪 *{shop['name']}*\n\nHozircha mahsulot yo'q.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"cat_{ctx.user_data.get('category','flower')}")]])
        )
        return

    icon = "🌸" if shop["shop_type"] == "flower" else "🍰"
    kb = [[InlineKeyboardButton(f"{icon} {p['name']}", callback_data=f"prod_{p['id']}")]
          for p in products]
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data=f"cat_{shop['shop_type']}")])

    text = (
        f"🏪 *{shop['name']}*\n"
        f"📍 {shop['address']}\n"
        f"📞 {shop['phone']}\n"
        f"🚚 Yetkazib berish: {'Ha ✅' if shop['has_delivery'] else 'Yo\'q ❌'}\n\n"
        f"*Mahsulotlarni tanlang:*"
    )
    await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                               reply_markup=InlineKeyboardMarkup(kb))


# ════════════════════════════════════════════════
#  MAHSULOT TANLASH
# ════════════════════════════════════════════════

async def product_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    product_id = int(q.data.split("_")[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await q.edit_message_text("Mahsulot topilmadi.")
        return

    ctx.user_data["product_id"] = product_id
    ctx.user_data["product"] = product

    # Rasmni yuborish
    try:
        await q.message.delete()
    except Exception:
        pass

    kb_rows = []
    if product["product_type"] == "flower":
        kb_rows = [
            [InlineKeyboardButton(f"🌸 Dona — {fmt_price(product['single_price'])} so'm", callback_data="type_single")],
            [InlineKeyboardButton(f"💐 Buket — {fmt_price(product['bouquet_price'])} so'm", callback_data="type_bouquet")],
        ]
    else:
        kb_rows = [
            [InlineKeyboardButton(f"🍰 Bo'lak — {fmt_price(product['piece_price'])} so'm", callback_data="type_piece")],
            [InlineKeyboardButton(f"🎂 Butun — {fmt_price(product['full_price'])} so'm", callback_data="type_full")],
        ]
    kb_rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data=f"shop_{product['shop_id']}")])

    caption = product_info(product)
    await q.message.reply_photo(
        photo=product["photo_id"],
        caption=caption + "\n\n*Turni tanlang:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb_rows)
    )


# ════════════════════════════════════════════════
#  BUYURTMA JARAYONI
# ════════════════════════════════════════════════

async def order_type_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    order_type = q.data.split("_")[1]  # single|bouquet|piece|full
    ctx.user_data["order_type"] = order_type
    product = ctx.user_data.get("product", {})

    price_map = {
        "single":  product.get("single_price", 0),
        "bouquet": product.get("bouquet_price", 0),
        "piece":   product.get("piece_price", 0),
        "full":    product.get("full_price", 0),
    }
    ctx.user_data["unit_price"] = price_map.get(order_type, 0)

    type_label = {
        "single": "Dona", "bouquet": "Buket",
        "piece": "Bo'lak", "full": "Butun"
    }.get(order_type, "")

    await q.edit_message_caption(
        caption=f"✅ Tur: *{type_label}* — {fmt_price(ctx.user_data['unit_price'])} so'm\n\n"
                f"Nechta buyurtma qilmoqchisiz?\n_(raqam yozing, masalan: 2)_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("1️⃣", callback_data="qty_1"),
            InlineKeyboardButton("2️⃣", callback_data="qty_2"),
            InlineKeyboardButton("3️⃣", callback_data="qty_3"),
            InlineKeyboardButton("5️⃣", callback_data="qty_5"),
        ]])
    )
    return ORD_QTY


async def qty_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    qty = int(q.data.split("_")[1])
    return await set_quantity(q.message, ctx, qty, is_caption=True)


async def qty_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text.strip())
        if qty < 1 or qty > 100:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ 1 dan 100 gacha raqam kiriting!")
        return ORD_QTY
    return await set_quantity(update.message, ctx, qty)


async def set_quantity(msg, ctx, qty: int, is_caption=False):
    ctx.user_data["quantity"] = qty
    total = ctx.user_data["unit_price"] * qty
    ctx.user_data["total_price"] = total

    product = ctx.user_data.get("product", {})
    shop_id = ctx.user_data.get("shop_id")
    shop = await db.get_shop_by_id(shop_id) if shop_id else {}

    # Yetkazib berish imkoni
    order_type = ctx.user_data.get("order_type", "")
    can_deliver = (
        (order_type in ["single", "bouquet"] and product.get("flower_delivery")) or
        (order_type in ["piece", "full"] and product.get("sweet_delivery")) or
        shop.get("has_delivery")
    )
    ctx.user_data["can_deliver"] = bool(can_deliver)

    kb = []
    if can_deliver:
        kb.append([InlineKeyboardButton("🚚 Yetkazib bersin", callback_data="del_yes"),
                   InlineKeyboardButton("🏃 O'zim olaman", callback_data="del_no")])
    else:
        kb.append([InlineKeyboardButton("🏃 O'zim olaman (yetkazib berish yo'q)", callback_data="del_no")])

    text = (
        f"🔢 Miqdor: *{qty} ta*\n"
        f"💰 Jami: *{fmt_price(total)} so'm*\n\n"
        f"Qanday olasiz?"
    )
    await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                          reply_markup=InlineKeyboardMarkup(kb))
    return ORD_TYPE


async def delivery_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    needs_delivery = q.data == "del_yes"
    ctx.user_data["needs_delivery"] = needs_delivery

    await q.edit_message_text(
        f"🚚 {'Yetkazib beriladi ✅' if needs_delivery else 'O\'zingiz olasiz 🏃'}\n\n"
        f"📍 {'Yetkazish manzilini' if needs_delivery else 'Qayerdan olishingizni'} yozing:",
        parse_mode=ParseMode.MARKDOWN
    )

    # Telefon so'rash
    await q.message.reply_text(
        "📞 Avval *telefon raqamingizni* kiriting yoki ulashing:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Raqamni ulashish", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ORD_PHONE


async def get_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    ctx.user_data["phone"] = phone
    needs_delivery = ctx.user_data.get("needs_delivery", False)

    await update.message.reply_text(
        f"✅ Telefon: *{phone}*\n\n"
        f"📍 {'Yetkazish manzilini' if needs_delivery else 'Qayerdan olishingiz manzilini'} yozing:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    return ORD_ADDRESS


async def get_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    ctx.user_data["address"] = address

    user = update.effective_user
    product = ctx.user_data.get("product", {})
    shop_id = ctx.user_data.get("shop_id")
    shop = await db.get_shop_by_id(shop_id) if shop_id else {}

    order_type_label = {
        "single": "Dona", "bouquet": "Buket",
        "piece": "Bo'lak", "full": "Butun"
    }.get(ctx.user_data.get("order_type", ""), "")

    summary = (
        f"📋 *Zakaz tasdiqlash*\n\n"
        f"🏪 Do'kon: {ctx.user_data.get('shop_name', '')}\n"
        f"🛍 Mahsulot: {product.get('name', '')}\n"
        f"📦 Tur: {order_type_label}\n"
        f"🔢 Miqdor: {ctx.user_data['quantity']} ta\n"
        f"💰 Jami: *{fmt_price(ctx.user_data['total_price'])} so'm*\n"
        f"📞 Tel: {ctx.user_data.get('phone', '')}\n"
        f"📍 Manzil: {address}\n"
        f"🚚 Yetkazib berish: {'Ha ✅' if ctx.user_data.get('needs_delivery') else 'Yo\'q ❌'}\n\n"
        f"Tasdiqlaysizmi?"
    )

    await update.message.reply_text(
        summary,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_yes"),
             InlineKeyboardButton("❌ Bekor qilish", callback_data="confirm_no")]
        ])
    )
    return ORD_CONFIRM


async def confirm_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "confirm_no":
        await q.edit_message_text("❌ Zakaz bekor qilindi. /start bosing.")
        ctx.user_data.clear()
        return ConversationHandler.END

    # Zakazni saqlash
    user = q.from_user
    product = ctx.user_data["product"]

    order_id = await db.create_order(
        shop_id=ctx.user_data["shop_id"],
        product_id=ctx.user_data["product_id"],
        customer_id=user.id,
        customer_name=user.full_name or user.first_name,
        customer_phone=ctx.user_data.get("phone", ""),
        quantity=ctx.user_data["quantity"],
        order_type=ctx.user_data["order_type"],
        total_price=ctx.user_data["total_price"],
        address=ctx.user_data["address"],
        needs_delivery=int(ctx.user_data.get("needs_delivery", False)),
    )

    await q.edit_message_text(
        f"🎉 *Zakaz qabul qilindi!*\n\n"
        f"📦 Zakaz raqami: *#{order_id}*\n"
        f"💰 Jami: *{fmt_price(ctx.user_data['total_price'])} so'm*\n\n"
        f"Do'kon tez orada siz bilan bog'lanadi!\n"
        f"📞 {ctx.user_data.get('phone', '')}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_main")]])
    )

    # Do'kon egasiga xabar yuborish (SHOP BOT orqali)
    await notify_shop_owner(ctx, order_id)
    ctx.user_data.clear()
    return ConversationHandler.END


async def notify_shop_owner(ctx: ContextTypes.DEFAULT_TYPE, order_id: int):
    """Do'kon egasiga yangi zakaz haqida xabar"""
    from telegram import Bot
    order = await db.get_order_by_id(order_id)
    if not order:
        return

    shop = await db.get_shop_by_id(order["shop_id"])
    if not shop:
        return

    del_note = "🚚 Yetkazib berish kerak" if order["needs_delivery"] else "🏃 Mijoz o'zi oladi"
    text = (
        f"🔔 *Yangi Zakaz! #{order_id}*\n\n"
        f"🛍 Mahsulot: {order['product_name']}\n"
        f"🔢 Miqdor: {order['quantity']} ta\n"
        f"💰 Jami: {fmt_price(order['total_price'])} so'm\n"
        f"👤 Mijoz: {order['customer_name']}\n"
        f"📞 Tel: {order['customer_phone']}\n"
        f"📍 Manzil: {order['address']}\n"
        f"{del_note}\n"
        f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    try:
        shop_bot = Bot(SHOP_BOT_TOKEN)
        await shop_bot.send_message(
            shop["owner_id"],
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Qabul qilish", callback_data=f"accept_{order_id}"),
                 InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{order_id}")]
            ])
        )
    except Exception as e:
        print(f"Notify error: {e}")


# ════════════════════════════════════════════════
#  MENING ZAKAZLARIM
# ════════════════════════════════════════════════

async def my_orders_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id

    async with __import__("aiosqlite").connect(__import__("config").DATABASE_PATH) as dbc:
        dbc.row_factory = __import__("aiosqlite").Row
        async with dbc.execute(
            """SELECT o.*, p.name as product_name, s.name as shop_name
               FROM orders o JOIN products p ON o.product_id=p.id
               JOIN shops s ON o.shop_id=s.id
               WHERE o.customer_id=? ORDER BY o.created_at DESC LIMIT 10""",
            (user_id,)
        ) as c:
            orders = [dict(r) for r in await c.fetchall()]

    if not orders:
        await q.edit_message_text(
            "📦 Hali zakaz bermagansiz.\n\nBuyurtma berish uchun:",
            reply_markup=MAIN_KB
        )
        return

    text = "📦 *Mening zakazlarim:*\n\n"
    icons = {"new": "🆕", "accepted": "✅", "done": "🏁", "cancelled": "❌"}
    for o in orders:
        icon = icons.get(o["status"], "•")
        text += f"{icon} #{o['id']} | *{o['product_name']}* x{o['quantity']} | {fmt_price(o['total_price'])} so'm\n"
        text += f"   🏪 {o['shop_name']} | {o['created_at'][:16]}\n\n"

    await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]))


async def back_main_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🌸 *ORZUGUL* — nima buyurtma qilmoqchisiz?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MAIN_KB
    )


# ════════════════════════════════════════════════
#  BOT YARATISH
# ════════════════════════════════════════════════

def create_customer_bot():
    app = Application.builder().token(CUSTOMER_BOT_TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_type_cb, pattern="^type_")],
        states={
            ORD_QTY:     [
                CallbackQueryHandler(qty_cb, pattern="^qty_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, qty_text),
            ],
            ORD_TYPE:    [CallbackQueryHandler(delivery_cb, pattern="^del_")],
            ORD_PHONE:   [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, get_phone)],
            ORD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            ORD_CONFIRM: [CallbackQueryHandler(confirm_cb, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(category_cb, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(shop_cb, pattern="^shop_"))
    app.add_handler(CallbackQueryHandler(product_cb, pattern="^prod_"))
    app.add_handler(CallbackQueryHandler(my_orders_cb, pattern="^my_orders$"))
    app.add_handler(CallbackQueryHandler(back_main_cb, pattern="^back_main$"))
    app.add_handler(order_conv)

    return app
