"""
ORZUGUL — Do'kon Boti (@OrzugulShopBot)
Do'konlarni ro'yxatdan o'tkazish va zakazlarni boshqarish
"""
import json
import asyncio
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from config import SHOP_BOT_TOKEN, ADMIN_IDS, MIN_PRODUCTS, CUSTOMER_BOT_USERNAME
from database import db

# ── Bosqichlar ───────────────────────────────────
(
    REG_TYPE, REG_NAME, REG_ADDRESS, REG_PHONE, REG_DELIVERY,
    PROD_PHOTO, PROD_NAME, PROD_PRICE_SINGLE, PROD_PRICE_BOUQUET,
    PROD_DELIVERY, PROD_PIECE, PROD_FULL, PROD_SWEET_DELIVERY,
    PROD_MORE
) = range(14)


# ════════════════════════════════════════════════
#  YORDAMCHI FUNKSIYALAR
# ════════════════════════════════════════════════

def type_label(t): return "🌸 Gul do'koni" if t == "flower" else "🍰 Shirinlik do'koni"
def yn(v): return "Ha ✅" if v else "Yo'q ❌"
def fmt_price(p): return f"{p:,}".replace(",", " ")

def order_status_label(s):
    return {"new": "🆕 Yangi", "accepted": "✅ Qabul qilindi",
            "done": "🏁 Bajarildi", "cancelled": "❌ Bekor qilindi"}.get(s, s)


def shop_card(shop) -> str:
    return (
        f"🏪 *{shop['name']}*\n"
        f"{type_label(shop['shop_type'])}\n"
        f"📍 {shop['address']}\n"
        f"📞 {shop['phone']}\n"
        f"🚚 Yetkazib berish: {yn(shop['has_delivery'])}\n"
        f"{'✅ Tasdiqlangan' if shop['is_approved'] else '⏳ Tasdiq kutilmoqda'}"
    )


# ════════════════════════════════════════════════
#  /start
# ════════════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    shop = await db.get_shop_by_owner(user.id)

    if shop:
        # Mavjud do'kon egasi
        await show_shop_menu(update, shop)
    else:
        # Yangi ro'yxatdan o'tish
        await update.message.reply_text(
            "🌸 *ORZUGUL* Do'kon Tizimiga Xush Kelibsiz!\n\n"
            "Bu orqali siz do'koningizni ro'yxatdan o'tkazib,\n"
            "mijozlardan zakaz qabul qila olasiz.\n\n"
            "Do'koningiz qaysi sohada?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌸 Gul do'koni", callback_data="reg_type_flower")],
                [InlineKeyboardButton("🍰 Shirinlik do'koni", callback_data="reg_type_sweet")],
            ])
        )


async def show_shop_menu(update: Update, shop: dict):
    pending = await db.get_orders_by_shop(shop["id"], status="new")
    badge = f" 🔴 {len(pending)} yangi" if pending else ""

    kb = [
        [InlineKeyboardButton(f"📦 Zakazlar{badge}", callback_data="menu_orders")],
        [InlineKeyboardButton("🛍 Mahsulotlarim", callback_data="menu_products")],
        [InlineKeyboardButton("🏪 Do'kon ma'lumotlari", callback_data="menu_shopinfo")],
        [InlineKeyboardButton("➕ Mahsulot qo'shish", callback_data="menu_addprod")],
    ]

    text = (
        f"👋 Salom, *{shop['name']}*!\n\n"
        f"{'✅ Do\'koningiz faol' if shop['is_approved'] else '⏳ Do\'koningiz tasdiq kutmoqda'}\n"
        f"📦 Yangi zakazlar: *{len(pending)}* ta\n\n"
        "Nima qilmoqchisiz?"
    )

    msg = update.message or update.callback_query.message
    await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                         reply_markup=InlineKeyboardMarkup(kb))


# ════════════════════════════════════════════════
#  RO'YXATDAN O'TISH — CALLBACK
# ════════════════════════════════════════════════

async def reg_type_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    shop_type = q.data.split("_")[2]  # flower | sweet
    owner_id = q.from_user.id

    await db.set_reg_step(owner_id, step="name", shop_type=shop_type)

    label = type_label(shop_type)
    await q.edit_message_text(
        f"✅ Tanlov: *{label}*\n\n"
        f"Do'koningizning *nomini* kiriting:\n"
        f"_(masalan: Gulnora Flower Shop)_",
        parse_mode=ParseMode.MARKDOWN
    )
    ctx.user_data["reg"] = True
    return REG_NAME


async def reg_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Nom juda qisqa. Qaytadan kiriting:")
        return REG_NAME

    await db.set_reg_step(update.effective_user.id, step="address", name=name)
    await update.message.reply_text(
        f"✅ Nom: *{name}*\n\n📍 Do'koningizning *manzilini* kiriting:\n_(masalan: Termiz, Mustaqillik ko'chasi 15)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return REG_ADDRESS


async def reg_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    await db.set_reg_step(update.effective_user.id, step="phone", address=address)
    await update.message.reply_text(
        f"✅ Manzil saqlandi.\n\n📞 *Telefon raqamingizni* kiriting yoki ulashing:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Raqamni ulashish", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return REG_PHONE


async def reg_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    await db.set_reg_step(update.effective_user.id, step="delivery", phone=phone)
    await update.message.reply_text(
        f"✅ Telefon: *{phone}*\n\n🚚 Do'koningizda *yetkazib berish* xizmati bormi?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    await asyncio.sleep(0.3)
    await update.message.reply_text(
        "Tanlang:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ha ✅", callback_data="reg_del_1"),
             InlineKeyboardButton("Yo'q ❌", callback_data="reg_del_0")]
        ])
    )
    return REG_DELIVERY


async def reg_delivery_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    has_delivery = int(q.data.split("_")[2])
    owner_id = q.from_user.id

    reg = await db.get_reg(owner_id)
    await db.set_reg_step(owner_id, step="products", has_delivery=has_delivery)

    shop_type = reg["shop_type"]
    example = (
        "🌸 *Gul* uchun: rasm → nom → dona narxi → buket narxi → yetkazib berish"
        if shop_type == "flower" else
        "🍰 *Shirinlik* uchun: rasm → nom → bo'lak narxi → butun narxi → yetkazib berish"
    )

    await q.edit_message_text(
        f"✅ Yetkazib berish: *{yn(has_delivery)}*\n\n"
        f"Endi *mahsulotlarni* qo'shing.\n"
        f"Kamida *{MIN_PRODUCTS} ta* mahsulot kerak.\n\n"
        f"{example}\n\n"
        f"Boshlash uchun *1-mahsulotning rasmini* yuboring 📸",
        parse_mode=ParseMode.MARKDOWN
    )
    ctx.user_data["adding_product"] = True
    return PROD_PHOTO


# ════════════════════════════════════════════════
#  MAHSULOT QO'SHISH — RO'YXATDAN O'TISH
# ════════════════════════════════════════════════

async def prod_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Iltimos, *rasm* yuboring (fayl emas)!", parse_mode=ParseMode.MARKDOWN)
        return PROD_PHOTO

    photo_id = update.message.photo[-1].file_id
    owner_id = update.effective_user.id
    reg = await db.get_reg(owner_id)

    ctx.user_data["temp_photo"] = photo_id

    product_type = reg["shop_type"] if reg else ctx.user_data.get("shop_type", "flower")
    ctx.user_data["prod_type"] = product_type

    count = reg["product_count"] if reg else 0
    await update.message.reply_text(
        f"📸 Rasm qabul qilindi! (#{count+1})\n\n"
        f"Endi *mahsulot nomini* kiriting:\n_(masalan: Qizil Lola)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return PROD_NAME


async def prod_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    ctx.user_data["temp_name"] = name
    prod_type = ctx.user_data.get("prod_type", "flower")

    if prod_type == "flower":
        await update.message.reply_text(
            f"✅ Mahsulot: *{name}*\n\n"
            f"🌸 *Dona narxini* kiriting (so'mda):\n_(masalan: 5000)_",
            parse_mode=ParseMode.MARKDOWN
        )
        return PROD_PRICE_SINGLE
    else:
        await update.message.reply_text(
            f"✅ Mahsulot: *{name}*\n\n"
            f"🍰 *Bo'lak narxini* kiriting (so'mda):\n_(masalan: 15000)_",
            parse_mode=ParseMode.MARKDOWN
        )
        return PROD_PIECE


# ── Gul narxlari ─────────────────────────────────

async def prod_price_single(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", "").replace(",", ""))
        ctx.user_data["temp_single"] = price
        await update.message.reply_text(
            f"✅ Dona narxi: *{fmt_price(price)} so'm*\n\n"
            f"💐 *Buket narxini* kiriting:\n_(masalan: 50000)_",
            parse_mode=ParseMode.MARKDOWN
        )
        return PROD_PRICE_BOUQUET
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting! Masalan: 5000")
        return PROD_PRICE_SINGLE


async def prod_price_bouquet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", "").replace(",", ""))
        ctx.user_data["temp_bouquet"] = price
        await update.message.reply_text(
            f"✅ Buket narxi: *{fmt_price(price)} so'm*\n\n"
            f"🚚 Bu gul uchun *yetkazib berish* bormi?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Ha ✅", callback_data="pd_del_1"),
                 InlineKeyboardButton("Yo'q ❌", callback_data="pd_del_0")]
            ])
        )
        return PROD_DELIVERY
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PROD_PRICE_BOUQUET


async def prod_flower_delivery_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    delivery = int(q.data.split("_")[2])
    ctx.user_data["temp_flower_del"] = delivery
    await q.edit_message_text(
        f"✅ Yetkazib berish: *{yn(delivery)}*\n\nMahsulot saqlanmoqda...",
        parse_mode=ParseMode.MARKDOWN
    )
    return await save_flower_product(q, ctx)


# ── Shirinlik narxlari ────────────────────────────

async def prod_piece_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", "").replace(",", ""))
        ctx.user_data["temp_piece"] = price
        await update.message.reply_text(
            f"✅ Bo'lak narxi: *{fmt_price(price)} so'm*\n\n"
            f"🎂 *Butun tort narxini* kiriting:\n_(masalan: 120000)_",
            parse_mode=ParseMode.MARKDOWN
        )
        return PROD_FULL
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PROD_PIECE


async def prod_full_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", "").replace(",", ""))
        ctx.user_data["temp_full"] = price
        await update.message.reply_text(
            f"✅ Butun narxi: *{fmt_price(price)} so'm*\n\n"
            f"🚚 Bu shirinlik uchun *yetkazib berish* bormi?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Ha ✅", callback_data="sd_del_1"),
                 InlineKeyboardButton("Yo'q ❌", callback_data="sd_del_0")]
            ])
        )
        return PROD_SWEET_DELIVERY
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PROD_FULL


async def prod_sweet_delivery_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    delivery = int(q.data.split("_")[2])
    ctx.user_data["temp_sweet_del"] = delivery
    await q.edit_message_text(
        f"✅ Yetkazib berish: *{yn(delivery)}*",
        parse_mode=ParseMode.MARKDOWN
    )
    return await save_sweet_product(q, ctx)


# ════════════════════════════════════════════════
#  MAHSULOT SAQLASH
# ════════════════════════════════════════════════

async def save_flower_product(q_or_msg, ctx):
    owner_id = q_or_msg.from_user.id
    reg = await db.get_reg(owner_id)

    # Do'kon ID ni topish (ro'yxatdan o'tish yoki mavjud)
    shop = await db.get_shop_by_owner(owner_id)
    shop_id = shop["id"] if shop else None

    if not shop_id:
        # Ro'yxatdan o'tish jarayonida — avval do'konni yaratish kerak
        shop_id = await finish_shop_creation(owner_id, reg)

    await db.add_product(
        shop_id=shop_id,
        name=ctx.user_data["temp_name"],
        photo_id=ctx.user_data["temp_photo"],
        product_type="flower",
        single_price=ctx.user_data.get("temp_single", 0),
        bouquet_price=ctx.user_data.get("temp_bouquet", 0),
        flower_delivery=ctx.user_data.get("temp_flower_del", 0),
    )

    count = await db.count_products(shop_id)
    await db.set_reg_step(owner_id, product_count=count)

    return await ask_more_products(q_or_msg, ctx, count, shop_id)


async def save_sweet_product(q_or_msg, ctx):
    owner_id = q_or_msg.from_user.id
    reg = await db.get_reg(owner_id)

    shop = await db.get_shop_by_owner(owner_id)
    shop_id = shop["id"] if shop else None

    if not shop_id:
        shop_id = await finish_shop_creation(owner_id, reg)

    await db.add_product(
        shop_id=shop_id,
        name=ctx.user_data["temp_name"],
        photo_id=ctx.user_data["temp_photo"],
        product_type="sweet",
        piece_price=ctx.user_data.get("temp_piece", 0),
        full_price=ctx.user_data.get("temp_full", 0),
        sweet_delivery=ctx.user_data.get("temp_sweet_del", 0),
    )

    count = await db.count_products(shop_id)
    await db.set_reg_step(owner_id, product_count=count)

    return await ask_more_products(q_or_msg, ctx, count, shop_id)


async def finish_shop_creation(owner_id: int, reg: dict) -> int:
    """Do'konni bazaga saqlash"""
    shop_id = await db.create_shop(
        owner_id=owner_id,
        owner_username=None,
        shop_type=reg["shop_type"],
        name=reg["name"],
        address=reg["address"],
        phone=reg["phone"],
        has_delivery=reg["has_delivery"]
    )
    return shop_id


async def ask_more_products(q_or_msg, ctx, count: int, shop_id: int):
    msg = q_or_msg.message if hasattr(q_or_msg, "message") else q_or_msg

    min_ok = count >= MIN_PRODUCTS
    status = f"✅ {count} ta mahsulot qo'shildi" if min_ok else f"⚠️ {count}/{MIN_PRODUCTS} ta — yana {MIN_PRODUCTS-count} ta kerak"

    kb = [[InlineKeyboardButton("➕ Yana mahsulot qo'shish", callback_data="more_prod")]]
    if min_ok:
        kb.append([InlineKeyboardButton("✅ Tugatish va yuborish", callback_data="finish_reg")])

    await msg.reply_text(
        f"🎉 Mahsulot saqlandi!\n{status}\n\n"
        f"Davom etasizmi?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return PROD_MORE


async def more_prod_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    reg = await db.get_reg(q.from_user.id)
    prod_type = reg["shop_type"] if reg else "flower"
    ctx.user_data["prod_type"] = prod_type
    count = await db.count_products((await db.get_shop_by_owner(q.from_user.id))["id"])
    await q.edit_message_text(
        f"📸 *{count+1}-mahsulotning rasmini* yuboring:",
        parse_mode=ParseMode.MARKDOWN
    )
    return PROD_PHOTO


async def finish_reg_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    owner_id = q.from_user.id
    shop = await db.get_shop_by_owner(owner_id)

    if not shop:
        await q.edit_message_text("❌ Xatolik yuz berdi. /start dan boshlang.")
        return ConversationHandler.END

    await db.delete_reg(owner_id)

    # Admin ga xabar
    count = await db.count_products(shop["id"])
    for admin_id in ADMIN_IDS:
        try:
            from telegram import Bot
            bot = Bot(SHOP_BOT_TOKEN)
            await bot.send_message(
                admin_id,
                f"🆕 *Yangi do'kon tasdiqlash kutmoqda!*\n\n"
                f"{shop_card(shop)}\n"
                f"📦 Mahsulotlar: {count} ta\n"
                f"ID: `{shop['id']}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{shop['id']}"),
                     InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{shop['id']}")]
                ])
            )
        except Exception:
            pass

    await q.edit_message_text(
        "🎉 *Zo'r! Ro'yxatdan o'tish yakunlandi!*\n\n"
        f"Do'koningiz: *{shop['name']}*\n"
        f"Mahsulotlar: *{count} ta*\n\n"
        f"⏳ Admin tasdiqlashini kuting.\n"
        f"Tasdiqlangandan so'ng mijozlar buyurtma bera boshlaydi!\n\n"
        f"📱 Mijoz boti: {CUSTOMER_BOT_USERNAME}",
        parse_mode=ParseMode.MARKDOWN
    )
    ctx.user_data.clear()
    return ConversationHandler.END


# ════════════════════════════════════════════════
#  MENYU CALLBACKLARI
# ════════════════════════════════════════════════

async def menu_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    owner_id = q.from_user.id
    shop = await db.get_shop_by_owner(owner_id)

    if not shop:
        await q.edit_message_text("Do'kon topilmadi. /start bosing.")
        return

    action = q.data

    if action == "menu_orders":
        await show_orders(q, shop)
    elif action == "menu_products":
        await show_products(q, shop)
    elif action == "menu_shopinfo":
        await q.edit_message_text(
            f"🏪 *Do'kon ma'lumotlari*\n\n{shop_card(shop)}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")]])
        )
    elif action == "menu_addprod":
        reg = await db.get_reg(owner_id)
        if not reg:
            await db.set_reg_step(owner_id, step="products",
                                  shop_type=shop["shop_type"],
                                  has_delivery=shop["has_delivery"])
        ctx.user_data["prod_type"] = shop["shop_type"]
        await q.edit_message_text(
            "📸 Yangi mahsulotning *rasmini* yuboring:",
            parse_mode=ParseMode.MARKDOWN
        )
        return PROD_PHOTO
    elif action == "back_menu":
        await show_shop_menu(update, shop)


async def show_orders(q, shop):
    orders = await db.get_orders_by_shop(shop["id"])
    if not orders:
        await q.edit_message_text(
            "📦 Hozircha zakaz yo'q.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")]])
        )
        return

    text = "📦 *Zakazlar ro'yxati:*\n\n"
    kb = []
    for o in orders[:10]:
        status_icon = {"new": "🆕", "accepted": "✅", "done": "🏁", "cancelled": "❌"}.get(o["status"], "•")
        text += f"{status_icon} #{o['id']} — {o['product_name']} x{o['quantity']} — {fmt_price(o['total_price'])} so'm\n"
        kb.append([InlineKeyboardButton(
            f"{status_icon} #{o['id']} — {o['product_name']}",
            callback_data=f"order_{o['id']}"
        )])
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")])
    await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                               reply_markup=InlineKeyboardMarkup(kb))


async def show_products(q, shop):
    products = await db.get_products_by_shop(shop["id"])
    if not products:
        await q.edit_message_text(
            "🛍 Mahsulot yo'q. ➕ Qo'shing!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Mahsulot qo'shish", callback_data="menu_addprod")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")],
            ])
        )
        return

    text = f"🛍 *Mahsulotlar ({len(products)} ta):*\n\n"
    for p in products:
        if p["product_type"] == "flower":
            text += f"🌸 *{p['name']}*\n   Dona: {fmt_price(p['single_price'])} | Buket: {fmt_price(p['bouquet_price'])} so'm\n\n"
        else:
            text += f"🍰 *{p['name']}*\n   Bo'lak: {fmt_price(p['piece_price'])} | Butun: {fmt_price(p['full_price'])} so'm\n\n"

    await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")]]))


async def order_detail_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    order_id = int(q.data.split("_")[1])
    order = await db.get_order_by_id(order_id)
    if not order:
        await q.edit_message_text("Zakaz topilmadi.")
        return

    shop = await db.get_shop_by_owner(q.from_user.id)
    if not shop or shop["id"] != order["shop_id"]:
        await q.answer("Bu zakaz sizga tegishli emas.", show_alert=True)
        return

    del_note = "🚚 Yetkazib berish kerak" if order["needs_delivery"] else "🏃 Mijoz o'zi oladi"
    text = (
        f"📦 *Zakaz #{order['id']}*\n\n"
        f"🛍 Mahsulot: {order['product_name']}\n"
        f"🔢 Miqdor: {order['quantity']} ta\n"
        f"💰 Jami: {fmt_price(order['total_price'])} so'm\n"
        f"👤 Mijoz: {order['customer_name']}\n"
        f"📞 Tel: {order['customer_phone']}\n"
        f"📍 Manzil: {order['address']}\n"
        f"{del_note}\n"
        f"📌 Holat: {order_status_label(order['status'])}\n"
        f"⏰ Vaqt: {order['created_at']}"
    )

    kb = []
    if order["status"] == "new":
        kb.append([InlineKeyboardButton("✅ Qabul qilish", callback_data=f"accept_{order_id}"),
                   InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{order_id}")])
    elif order["status"] == "accepted":
        kb.append([InlineKeyboardButton("🏁 Bajarildi", callback_data=f"done_{order_id}")])
    kb.append([InlineKeyboardButton("🔙 Zakazlarga", callback_data="menu_orders")])

    await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                               reply_markup=InlineKeyboardMarkup(kb))


async def order_action_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split("_")
    action, order_id = parts[0], int(parts[1])
    status_map = {"accept": "accepted", "cancel": "cancelled", "done": "done"}
    new_status = status_map.get(action)
    if not new_status:
        return

    await db.update_order_status(order_id, new_status)
    order = await db.get_order_by_id(order_id)

    label = order_status_label(new_status)
    await q.edit_message_text(
        f"✅ Zakaz #{order_id} holati: *{label}*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Zakazlarga", callback_data="menu_orders")]])
    )

    # Mijozga ham xabar (customer bot orqali — agar kerak bo'lsa)


# ════════════════════════════════════════════════
#  ADMIN PANEL
# ════════════════════════════════════════════════

async def admin_approve_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS:
        await q.answer("Ruxsat yo'q!", show_alert=True)
        return
    await q.answer()

    parts = q.data.split("_")
    action, shop_id = parts[0], int(parts[1])
    shop = await db.get_shop_by_id(shop_id)
    if not shop:
        await q.edit_message_text("Do'kon topilmadi.")
        return

    if action == "approve":
        await db.approve_shop(shop_id)
        result_text = f"✅ Do'kon tasdiqlandi: *{shop['name']}*"
        # Do'kon egasiga xabar
        try:
            await ctx.bot.send_message(
                shop["owner_id"],
                "🎉 *Tabriklaymiz!*\n\n"
                f"Do'koningiz *{shop['name']}* tasdiqlandi!\n"
                f"Endi mijozlar sizga buyurtma bera oladi.\n\n"
                f"Buyurtmalarni kuzatish uchun /start bosing.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass
    else:
        result_text = f"❌ Do'kon rad etildi: *{shop['name']}*"
        try:
            await ctx.bot.send_message(
                shop["owner_id"],
                "😔 Afsuski, do'koningiz tasdiqlanmadi.\n"
                "Batafsil ma'lumot uchun admin bilan bog'laning.",
            )
        except Exception:
            pass

    await q.edit_message_text(result_text, parse_mode=ParseMode.MARKDOWN)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    stats = await db.get_stats()
    await update.message.reply_text(
        f"📊 *ORZUGUL Statistika*\n\n"
        f"🏪 Jami do'konlar: {stats['total_shops']}\n"
        f"✅ Tasdiqlangan: {stats['approved_shops']}\n"
        f"🌸 Gul do'konlari: {stats['flower_shops']}\n"
        f"🍰 Shirinlik do'konlari: {stats['sweet_shops']}\n\n"
        f"📦 Jami zakazlar: {stats['total_orders']}\n"
        f"🆕 Yangi zakazlar: {stats['new_orders']}\n"
        f"👤 Mijozlar: {stats['total_customers']}",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_shops(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    shops = await db.get_all_shops()
    if not shops:
        await update.message.reply_text("Do'kon yo'q.")
        return
    text = "🏪 *Barcha do'konlar:*\n\n"
    for s in shops[:20]:
        icon = "✅" if s["is_approved"] else "⏳"
        text += f"{icon} [{s['id']}] {type_label(s['shop_type'])} — *{s['name']}*\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    orders = await db.get_all_orders()
    if not orders:
        await update.message.reply_text("Zakaz yo'q.")
        return
    text = "📦 *So'nggi zakazlar:*\n\n"
    for o in orders[:15]:
        icon = {"new": "🆕", "accepted": "✅", "done": "🏁", "cancelled": "❌"}.get(o["status"], "•")
        text += f"{icon} #{o['id']} | {o['shop_name']} | {o['product_name']} | {fmt_price(o['total_price'])} so'm\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ════════════════════════════════════════════════
#  BOT YARATISH
# ════════════════════════════════════════════════

def create_shop_bot():
    app = Application.builder().token(SHOP_BOT_TOKEN).build()

    # Ro'yxatdan o'tish conversation
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(reg_type_cb, pattern="^reg_type_"),
            CallbackQueryHandler(more_prod_cb, pattern="^more_prod$"),
            CallbackQueryHandler(menu_cb, pattern="^menu_addprod$"),
        ],
        states={
            REG_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_ADDRESS:       [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_address)],
            REG_PHONE:         [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, reg_phone)],
            REG_DELIVERY:      [CallbackQueryHandler(reg_delivery_cb, pattern="^reg_del_")],
            PROD_PHOTO:        [MessageHandler(filters.PHOTO, prod_photo)],
            PROD_NAME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_name)],
            PROD_PRICE_SINGLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_price_single)],
            PROD_PRICE_BOUQUET:[MessageHandler(filters.TEXT & ~filters.COMMAND, prod_price_bouquet)],
            PROD_DELIVERY:     [CallbackQueryHandler(prod_flower_delivery_cb, pattern="^pd_del_")],
            PROD_PIECE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_piece_price)],
            PROD_FULL:         [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_full_price)],
            PROD_SWEET_DELIVERY:[CallbackQueryHandler(prod_sweet_delivery_cb, pattern="^sd_del_")],
            PROD_MORE:         [
                CallbackQueryHandler(more_prod_cb, pattern="^more_prod$"),
                CallbackQueryHandler(finish_reg_cb, pattern="^finish_reg$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("shops", cmd_shops))
    app.add_handler(CommandHandler("orders", cmd_orders))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_approve_cb, pattern="^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(order_detail_cb, pattern="^order_"))
    app.add_handler(CallbackQueryHandler(order_action_cb, pattern="^(accept|cancel|done)_"))
    app.add_handler(CallbackQueryHandler(menu_cb, pattern="^(menu_|back_)"))

    return app
