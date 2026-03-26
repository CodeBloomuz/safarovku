"""
ORZUGUL — Admin Boti (@OrzugulAdminBot)
Do'konlarni tasdiqlash, statistika, boshqaruv
"""

from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
from telegram.constants import ParseMode
from config import ADMIN_BOT_TOKEN, ADMIN_IDS, SHOP_BOT_TOKEN
from database import db


def fmt_price(p): return f"{p:,}".replace(",", " ")

def type_label(t): return "🌸 Gul do'koni" if t == "flower" else "🍰 Shirinlik do'koni"

def yn(v): return "Ha ✅" if v else "Yo'q ❌"

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
# /start
# ════════════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return

    stats = await db.get_stats()
    await update.message.reply_text(
        f"👑 *ORZUGUL Admin Panel*\n\n"
        f"🏪 Do'konlar: *{stats['total_shops']}* ta ({stats['approved_shops']} tasdiqlangan)\n"
        f"📦 Zakazlar: *{stats['total_orders']}* ta ({stats['new_orders']} yangi)\n"
        f"👤 Mijozlar: *{stats['total_customers']}* ta\n\n"
        f"Buyruqlar:\n"
        f"/pending — tasdiq kutayotgan do'konlar\n"
        f"/shops — barcha do'konlar\n"
        f"/orders — so'nggi zakazlar\n"
        f"/stats — statistika",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ Tasdiq kutayotganlar", callback_data="admin_pending")],
            [InlineKeyboardButton("🏪 Barcha do'konlar", callback_data="admin_shops")],
            [InlineKeyboardButton("📦 Zakazlar", callback_data="admin_orders")],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        ])
    )


# ════════════════════════════════════════════════
# TASDIQ KUTAYOTGAN DO'KONLAR
# ════════════════════════════════════════════════

async def cmd_pending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    shops = await db.get_pending_shops()
    if not shops:
        await update.message.reply_text("✅ Tasdiq kutayotgan do'kon yo'q!")
        return

    await update.message.reply_text(f"⏳ *{len(shops)} ta do'kon tasdiq kutmoqda:*", parse_mode=ParseMode.MARKDOWN)

    for shop in shops:
        count = await db.count_products(shop["id"])
        await update.message.reply_text(
            f"{shop_card(shop)}\n"
            f"📦 Mahsulotlar: *{count}* ta\n"
            f"🆔 ID: `{shop['id']}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{shop['id']}"),
                    InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{shop['id']}")
                ]
            ])
        )


# ════════════════════════════════════════════════
# BARCHA DO'KONLAR
# ════════════════════════════════════════════════

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


# ════════════════════════════════════════════════
# ZAKAZLAR
# ════════════════════════════════════════════════

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
# STATISTIKA
# ════════════════════════════════════════════════

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    stats = await db.get_stats()
    await update.message.reply_text(
        f"📊 *ORZUGUL Statistika*\n\n"
        f"🏪 Jami do'konlar: *{stats['total_shops']}*\n"
        f"✅ Tasdiqlangan: *{stats['approved_shops']}*\n"
        f"⏳ Tasdiq kutmoqda: *{stats['total_shops'] - stats['approved_shops']}*\n"
        f"🌸 Gul do'konlari: *{stats['flower_shops']}*\n"
        f"🍰 Shirinlik do'konlari: *{stats['sweet_shops']}*\n\n"
        f"📦 Jami zakazlar: *{stats['total_orders']}*\n"
        f"🆕 Yangi zakazlar: *{stats['new_orders']}*\n"
        f"👤 Mijozlar: *{stats['total_customers']}*",
        parse_mode=ParseMode.MARKDOWN
    )


# ════════════════════════════════════════════════
# TASDIQLASH / RAD ETISH CALLBACK
# ════════════════════════════════════════════════

async def approve_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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

        # Do'kon egasiga shop_bot orqali xabar
        try:
            from telegram import Bot
            shop_bot = Bot(SHOP_BOT_TOKEN)
            await shop_bot.send_message(
                shop["owner_id"],
                f"🎉 *Tabriklaymiz!*\n\n"
                f"Do'koningiz *{shop['name']}* tasdiqlandi!\n"
                f"Endi mijozlar sizga buyurtma bera oladi.\n\n"
                f"Buyurtmalarni kuzatish uchun /start bosing.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Shop notify error: {e}")

        await q.edit_message_text(
            f"✅ *Do'kon tasdiqlandi!*\n\n{shop_card(shop)}",
            parse_mode=ParseMode.MARKDOWN
        )

    else:  # reject
        # Do'kon egasiga xabar
        try:
            from telegram import Bot
            shop_bot = Bot(SHOP_BOT_TOKEN)
            await shop_bot.send_message(
                shop["owner_id"],
                "😔 Afsuski, do'koningiz tasdiqlanmadi.\n"
                "Batafsil ma'lumot uchun admin bilan bog'laning."
            )
        except Exception as e:
            print(f"Shop notify error: {e}")

        await q.edit_message_text(
            f"❌ *Do'kon rad etildi:* {shop['name']}",
            parse_mode=ParseMode.MARKDOWN
        )


# ════════════════════════════════════════════════
# INLINE CALLBACK MENYULAR
# ════════════════════════════════════════════════

async def admin_menu_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS:
        await q.answer("Ruxsat yo'q!", show_alert=True)
        return

    await q.answer()
    action = q.data

    if action == "admin_pending":
        shops = await db.get_pending_shops()
        if not shops:
            await q.edit_message_text("✅ Tasdiq kutayotgan do'kon yo'q!")
            return
        await q.edit_message_text(f"⏳ *{len(shops)} ta do'kon tasdiq kutmoqda:*", parse_mode=ParseMode.MARKDOWN)
        for shop in shops:
            count = await db.count_products(shop["id"])
            await q.message.reply_text(
                f"{shop_card(shop)}\n📦 Mahsulotlar: *{count}* ta",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{shop['id']}"),
                        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{shop['id']}")
                    ]
                ])
            )

    elif action == "admin_shops":
        shops = await db.get_all_shops()
        if not shops:
            await q.edit_message_text("Do'kon yo'q.")
            return
        text = "🏪 *Barcha do'konlar:*\n\n"
        for s in shops[:20]:
            icon = "✅" if s["is_approved"] else "⏳"
            text += f"{icon} [{s['id']}] — *{s['name']}*\n"
        await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]))

    elif action == "admin_orders":
        orders = await db.get_all_orders()
        if not orders:
            await q.edit_message_text("Zakaz yo'q.")
            return
        text = "📦 *So'nggi zakazlar:*\n\n"
        for o in orders[:15]:
            icon = {"new": "🆕", "accepted": "✅", "done": "🏁", "cancelled": "❌"}.get(o["status"], "•")
            text += f"{icon} #{o['id']} | {o['shop_name']} | {fmt_price(o['total_price'])} so'm\n"
        await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]))

    elif action == "admin_stats":
        stats = await db.get_stats()
        await q.edit_message_text(
            f"📊 *ORZUGUL Statistika*\n\n"
            f"🏪 Jami do'konlar: *{stats['total_shops']}*\n"
            f"✅ Tasdiqlangan: *{stats['approved_shops']}*\n"
            f"⏳ Tasdiq kutmoqda: *{stats['total_shops'] - stats['approved_shops']}*\n\n"
            f"📦 Jami zakazlar: *{stats['total_orders']}*\n"
            f"🆕 Yangi zakazlar: *{stats['new_orders']}*\n"
            f"👤 Mijozlar: *{stats['total_customers']}*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]))

    elif action == "admin_back":
        stats = await db.get_stats()
        await q.edit_message_text(
            f"👑 *ORZUGUL Admin Panel*\n\n"
            f"🏪 Do'konlar: *{stats['total_shops']}* ta\n"
            f"📦 Zakazlar: *{stats['total_orders']}* ta\n"
            f"👤 Mijozlar: *{stats['total_customers']}* ta",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏳ Tasdiq kutayotganlar", callback_data="admin_pending")],
                [InlineKeyboardButton("🏪 Barcha do'konlar", callback_data="admin_shops")],
                [InlineKeyboardButton("📦 Zakazlar", callback_data="admin_orders")],
                [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
            ])
        )


# ════════════════════════════════════════════════
# BOT YARATISH
# ════════════════════════════════════════════════

def create_admin_bot():
    app = Application.builder().token(ADMIN_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("shops", cmd_shops))
    app.add_handler(CommandHandler("orders", cmd_orders))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(approve_cb, pattern="^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(admin_menu_cb, pattern="^admin_"))

    return app
