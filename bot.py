"""
TermizBot — Gul & Tort do'koni
Railway + GitHub deployment version
Sozlamalar: Railway dashboard da environment variables orqali
"""

import asyncio
import logging
import json
import sqlite3
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

# ============================================================
# ⚙️ Railway environment variables dan o'qiladi
# ============================================================
BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS    = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://example.com")
SHOP_PHONE   = os.environ.get("SHOP_PHONE", "+998 90 XXX XX XX")
SHOP_NAME    = "🌸 Termiz Flowers & Sweets"
DB_PATH      = "/app/data/orders.db"   # Railway persistent volume
# ============================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE
# ============================================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number     TEXT UNIQUE,
            user_id          INTEGER,
            user_name        TEXT,
            items            TEXT,
            total            TEXT,
            delivery_date    TEXT,
            delivery_time    TEXT,
            address          TEXT,
            landmark         TEXT,
            recipient_name   TEXT,
            recipient_phone  TEXT,
            sender_phone     TEXT,
            pay_method       TEXT,
            gift_message     TEXT,
            source           TEXT DEFAULT 'bot',
            status           TEXT DEFAULT 'yangi',
            created_at       TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    con.commit()
    con.close()

def save_order(data: dict, user_id: int, user_name: str, source='miniapp'):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO orders
        (order_number,user_id,user_name,items,total,delivery_date,
         delivery_time,address,landmark,recipient_name,recipient_phone,
         sender_phone,pay_method,gift_message,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get('orderNumber',''),
        user_id, user_name,
        data.get('items',''),
        data.get('total',''),
        data.get('deliveryDate',''),
        data.get('deliveryTime',''),
        data.get('address',''),
        data.get('landmark',''),
        data.get('recipientName',''),
        data.get('recipientPhone',''),
        data.get('senderPhone',''),
        data.get('payMethod',''),
        data.get('giftMessage',''),
        source
    ))
    con.commit()
    con.close()

def get_orders(limit=20):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return rows

def get_user_orders(user_id):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT order_number,items,delivery_date,delivery_time,status FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 5",
        (user_id,)
    ).fetchall()
    con.close()
    return rows

def update_status(order_number, status):
    con = sqlite3.connect(DB_PATH)
    con.execute("UPDATE orders SET status=? WHERE order_number=?", (status, order_number))
    con.commit()
    con.close()

# ============================================================
# KEYBOARDS
# ============================================================
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌸 Buyurtma berish", web_app=WebAppInfo(url=MINI_APP_URL))],
        [KeyboardButton(text="📋 Mening buyurtmalarim")],
        [KeyboardButton(text="📞 Bog'lanish"), KeyboardButton(text="ℹ️ Haqida")],
    ], resize_keyboard=True)

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def pay_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💵 Naqd pul")],
        [KeyboardButton(text="📲 Click / Payme")],
        [KeyboardButton(text="❌ Bekor qilish")],
    ], resize_keyboard=True)

def time_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="09:00–11:00"), KeyboardButton(text="11:00–13:00")],
        [KeyboardButton(text="13:00–15:00"), KeyboardButton(text="15:00–17:00")],
        [KeyboardButton(text="17:00–19:00"), KeyboardButton(text="19:00–21:00")],
        [KeyboardButton(text="❌ Bekor qilish")],
    ], resize_keyboard=True)

def product_kb(products):
    rows = [[KeyboardButton(text=f"{name} — {price:,} so'm")] for name, price in products]
    rows.append([KeyboardButton(text="❌ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

# ============================================================
# STATES
# ============================================================
class OrderForm(StatesGroup):
    product_type    = State()
    product_name    = State()
    delivery_date   = State()
    delivery_time   = State()
    address         = State()
    landmark        = State()
    recipient_name  = State()
    recipient_phone = State()
    sender_phone    = State()
    pay_method      = State()
    confirm         = State()

# ============================================================
# PRODUCTS
# ============================================================
GUL_PRODUCTS = [
    ("🌹 Qizil atirgullar (11 ta)", 120000),
    ("🤍 Oq atirgullar (7 ta)",     90000),
    ("💐 Aralash guldasta (21 ta)", 180000),
    ("🌷 Tulip guldasta (15 ta)",   100000),
    ("🌼 Sariq atirgullar (9 ta)",   95000),
    ("🌸 Premium guldasta (51 ta)", 450000),
]
TORT_PRODUCTS = [
    ("🎂 Tug'ilgan kun torti (1 kg)",  85000),
    ("🍫 Shokoladli tort (1.5 kg)",   120000),
    ("🍬 Macaron to'plami (12 dona)",  65000),
    ("🍓 Mevali tort (2 kg)",         150000),
    ("🧁 Cupcake to'plami (6 ta)",     55000),
    ("💍 Nikoh torti (3 kg)",         280000),
]

def order_to_text(data: dict) -> str:
    return (
        f"🧾 <b>Buyurtma №{data.get('orderNumber','—')}</b>\n\n"
        f"🛍 <b>Mahsulot:</b>\n{data.get('items','—')}\n\n"
        f"💰 <b>Jami:</b> {data.get('total','—')}\n\n"
        f"📅 <b>Sana:</b> {data.get('deliveryDate','—')}\n"
        f"⏰ <b>Vaqt:</b> {data.get('deliveryTime','—')}\n\n"
        f"📍 <b>Manzil:</b> {data.get('address','—')}\n"
        f"🏪 <b>Mo'ljal:</b> {data.get('landmark','—')}\n\n"
        f"👤 <b>Qabul qiluvchi:</b> {data.get('recipientName','—')}\n"
        f"📱 <b>Tel (qabul):</b> {data.get('recipientPhone','—')}\n"
        f"📞 <b>Tel (buyurtmachi):</b> {data.get('senderPhone','—')}\n\n"
        f"💳 <b>To'lov:</b> {data.get('payMethod','—')}\n"
        f"💌 <b>Xabar:</b> {data.get('giftMessage','—')}"
    )

# ============================================================
# HANDLERS
# ============================================================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"👋 Assalomu alaykum! <b>{SHOP_NAME}</b>ga xush kelibsiz!\n\n"
        "🌹 Gullar va 🎂 tortlar — tez yetkazib beramiz!\n\n"
        "👇 <b>«Buyurtma berish»</b> tugmasini bosing:",
        parse_mode="HTML",
        reply_markup=main_kb()
    )

@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext):
    await state.clear()
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        return
    save_order(data, message.from_user.id, message.from_user.full_name, source='miniapp')
    await message.answer(
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n{order_to_text(data)}\n\n"
        f"📞 Operator <b>{data.get('senderPhone','—')}</b> ga tez orada qo'ng'iroq qiladi.",
        parse_mode="HTML", reply_markup=main_kb()
    )
    await notify_admins(message.bot, data, message.from_user, "🌐 Mini App")

@router.message(F.text == "🌸 Buyurtma berish")
async def order_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderForm.product_type)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌹 Gullar"), KeyboardButton(text="🎂 Tortlar")],
        [KeyboardButton(text="❌ Bekor qilish")],
    ], resize_keyboard=True)
    await message.answer("📦 Nima buyurtma qilasiz?", reply_markup=kb)

@router.message(OrderForm.product_type, F.text == "🌹 Gullar")
async def choose_gul(message: Message, state: FSMContext):
    await state.update_data(product_type="Gul")
    await state.set_state(OrderForm.product_name)
    await message.answer("🌹 Qaysi guldastani tanlaysiz?", reply_markup=product_kb(GUL_PRODUCTS))

@router.message(OrderForm.product_type, F.text == "🎂 Tortlar")
async def choose_tort(message: Message, state: FSMContext):
    await state.update_data(product_type="Tort")
    await state.set_state(OrderForm.product_name)
    await message.answer("🎂 Qaysi tortni tanlaysiz?", reply_markup=product_kb(TORT_PRODUCTS))

@router.message(OrderForm.product_name)
async def got_product(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(product_name=message.text)
    await state.set_state(OrderForm.delivery_date)
    await message.answer(
        "📅 Yetkazib berish sanasini kiriting:\n"
        "Masalan: <b>20.06.2025</b>",
        parse_mode="HTML", reply_markup=cancel_kb()
    )

@router.message(OrderForm.delivery_date)
async def got_date(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(delivery_date=message.text)
    await state.set_state(OrderForm.delivery_time)
    await message.answer("⏰ Yetkazib berish vaqtini tanlang:", reply_markup=time_kb())

@router.message(OrderForm.delivery_time)
async def got_time(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(delivery_time=message.text)
    await state.set_state(OrderForm.address)
    await message.answer(
        "📍 <b>Manzilni kiriting:</b>\nKo'cha, uy raqami, qavat.",
        parse_mode="HTML", reply_markup=cancel_kb()
    )

@router.message(OrderForm.address)
async def got_address(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(address=message.text)
    await state.set_state(OrderForm.landmark)
    await message.answer(
        "🏪 <b>Yaqin mashhur joy (Mo'ljal):</b>\n"
        "<i>Masalan: Termiz bozori yonida</i>\n\n"
        "Yo'q bo'lsa <b>yo'q</b> deb yozing.",
        parse_mode="HTML", reply_markup=cancel_kb()
    )

@router.message(OrderForm.landmark)
async def got_landmark(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(landmark="—" if message.text.lower() == "yo'q" else message.text)
    await state.set_state(OrderForm.recipient_name)
    await message.answer(
        "👤 <b>Qabul qiluvchining to'liq ismi va familiyasi:</b>",
        parse_mode="HTML", reply_markup=cancel_kb()
    )

@router.message(OrderForm.recipient_name)
async def got_recipient_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(recipient_name=message.text)
    await state.set_state(OrderForm.recipient_phone)
    await message.answer("📱 <b>Qabul qiluvchining telefon raqami:</b>", parse_mode="HTML", reply_markup=cancel_kb())

@router.message(OrderForm.recipient_phone)
async def got_recipient_phone(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(recipient_phone=message.text)
    await state.set_state(OrderForm.sender_phone)
    await message.answer("📞 <b>Sizning telefon raqamingiz:</b>", parse_mode="HTML", reply_markup=cancel_kb())

@router.message(OrderForm.sender_phone)
async def got_sender_phone(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    await state.update_data(sender_phone=message.text)
    await state.set_state(OrderForm.pay_method)
    await message.answer("💳 To'lov usulini tanlang:", reply_markup=pay_kb())

@router.message(OrderForm.pay_method)
async def got_pay(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish": return await cancel(message, state)
    if message.text not in ["💵 Naqd pul", "📲 Click / Payme"]:
        await message.answer("⚠️ Tugmalardan birini tanlang:", reply_markup=pay_kb())
        return
    await state.update_data(pay_method=message.text)
    data = await state.get_data()
    order_num = "TF-" + datetime.now().strftime("%d%H%M%S")
    await state.update_data(order_number=order_num)
    await state.set_state(OrderForm.confirm)

    confirm_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Tasdiqlash")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ], resize_keyboard=True)

    await message.answer(
        f"📋 <b>Buyurtma ma'lumotlari:</b>\n\n"
        f"🛍 {data.get('product_name','—')}\n"
        f"📅 {data.get('delivery_date','—')}  ⏰ {data.get('delivery_time','—')}\n"
        f"📍 {data.get('address','—')}\n"
        f"🏪 {data.get('landmark','—')}\n"
        f"👤 {data.get('recipient_name','—')}\n"
        f"📱 {data.get('recipient_phone','—')}\n"
        f"📞 {data.get('sender_phone','—')}\n"
        f"💳 {data.get('pay_method','—')}\n\n"
        f"✅ Tasdiqlaysizmi?",
        parse_mode="HTML", reply_markup=confirm_kb
    )

@router.message(OrderForm.confirm, F.text == "✅ Tasdiqlash")
async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    order_data = {
        "orderNumber":    data.get("order_number", "TF-000"),
        "items":          data.get("product_name", ""),
        "total":          "—",
        "deliveryDate":   data.get("delivery_date", ""),
        "deliveryTime":   data.get("delivery_time", ""),
        "address":        data.get("address", ""),
        "landmark":       data.get("landmark", "—"),
        "recipientName":  data.get("recipient_name", ""),
        "recipientPhone": data.get("recipient_phone", ""),
        "senderPhone":    data.get("sender_phone", ""),
        "payMethod":      data.get("pay_method", ""),
        "giftMessage":    "—"
    }
    save_order(order_data, message.from_user.id, message.from_user.full_name, source='bot')
    await state.clear()
    await message.answer(
        f"🎉 <b>Buyurtma qabul qilindi!</b>\n\n"
        f"№: <b>{order_data['orderNumber']}</b>\n\n"
        f"📞 Operator <b>{order_data['senderPhone']}</b> ga tez orada qo'ng'iroq qiladi.",
        parse_mode="HTML", reply_markup=main_kb()
    )
    await notify_admins(message.bot, order_data, message.from_user, "🤖 Telegram Bot")

@router.message(OrderForm.confirm)
async def confirm_other(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await cancel(message, state)

@router.message(F.text == "📋 Mening buyurtmalarim")
async def my_orders(message: Message):
    rows = get_user_orders(message.from_user.id)
    if not rows:
        await message.answer("📭 Hali buyurtma bermagansiz.", reply_markup=main_kb())
        return
    STATUS = {"yangi":"🟡","tasdiqlangan":"✅","yetkazildi":"🎁","bekor":"❌"}
    text = "📋 <b>Oxirgi buyurtmalaringiz:</b>\n\n"
    for r in rows:
        s = STATUS.get(r["status"], "🔵")
        text += f"{s} №{r['order_number']}  {r['delivery_date']}  {r['delivery_time']}\n{r['items'][:45]}...\n\n"
    await message.answer(text, parse_mode="HTML", reply_markup=main_kb())

@router.message(F.text == "📞 Bog'lanish")
async def contact(message: Message):
    await message.answer(
        f"📞 <b>Bog'lanish</b>\n\n📱 {SHOP_PHONE}\n🕐 08:00 – 22:00\n📍 Termiz, Surxondaryo",
        parse_mode="HTML", reply_markup=main_kb()
    )

@router.message(F.text == "ℹ️ Haqida")
async def about(message: Message):
    await message.answer(
        f"🌸 <b>{SHOP_NAME}</b>\n\n"
        "• Tez yetkazib berish (2–3 soat)\n"
        "• Yangi va sifatli mahsulotlar\n"
        "• Qulay narxlar\n"
        "• 7 kun, 08:00 – 22:00",
        parse_mode="HTML", reply_markup=main_kb()
    )

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    orders = get_orders(10)
    STATUS = {"yangi":"🟡","tasdiqlangan":"✅","yetkazildi":"🎁","bekor":"❌"}
    text = f"👨‍💼 <b>Admin Panel</b>\nSo'nggi {len(orders)} ta buyurtma:\n\n"
    for o in orders:
        s = STATUS.get(o["status"],"🔵")
        text += f"{s} №{o['order_number']} | {o['delivery_date']} | {o['recipient_name']}\n"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("orders"))
async def list_orders(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    orders = get_orders(20)
    if not orders:
        await message.answer("📭 Buyurtmalar yo'q.")
        return
    STATUS = {"yangi":"🟡","tasdiqlangan":"✅","yetkazildi":"🎁","bekor":"❌"}
    for o in orders:
        data = {
            "orderNumber":   o["order_number"],
            "items":         o["items"],
            "total":         o["total"],
            "deliveryDate":  o["delivery_date"],
            "deliveryTime":  o["delivery_time"],
            "address":       o["address"],
            "landmark":      o["landmark"],
            "recipientName": o["recipient_name"],
            "recipientPhone":o["recipient_phone"],
            "senderPhone":   o["sender_phone"],
            "payMethod":     o["pay_method"],
            "giftMessage":   o["gift_message"],
        }
        s = STATUS.get(o["status"],"🔵")
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Tasdiqlash",  callback_data=f"ok_{o['order_number']}"),
            InlineKeyboardButton(text="🎁 Yetkazildi", callback_data=f"done_{o['order_number']}"),
            InlineKeyboardButton(text="❌ Bekor",      callback_data=f"cancel_{o['order_number']}"),
        ]])
        await message.answer(
            f"{s} <b>Holat: {o['status']}</b>\n{order_to_text(data)}",
            parse_mode="HTML", reply_markup=kb
        )

@router.callback_query(F.data.startswith("ok_"))
async def admin_ok(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return
    update_status(cb.data[3:], "tasdiqlangan")
    await cb.answer("✅ Tasdiqlandi!")
    await cb.message.edit_text(cb.message.text + "\n\n✅ <b>TASDIQLANDI</b>", parse_mode="HTML")

@router.callback_query(F.data.startswith("done_"))
async def admin_done(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return
    update_status(cb.data[5:], "yetkazildi")
    await cb.answer("🎁 Yetkazildi!")
    await cb.message.edit_text(cb.message.text + "\n\n🎁 <b>YETKAZILDI</b>", parse_mode="HTML")

@router.callback_query(F.data.startswith("cancel_"))
async def admin_cancel(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return
    update_status(cb.data[7:], "bekor")
    await cb.answer("❌ Bekor qilindi")
    await cb.message.edit_text(cb.message.text + "\n\n❌ <b>BEKOR QILINDI</b>", parse_mode="HTML")

# ============================================================
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_kb())

async def notify_admins(bot: Bot, data: dict, user, source: str):
    text = (
        f"🔔 <b>YANGI BUYURTMA!</b> ({source})\n"
        f"👤 @{user.username or '—'} | {user.full_name} | ID: {user.id}\n\n"
        f"{order_to_text(data)}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash",  callback_data=f"ok_{data.get('orderNumber','')}"),
        InlineKeyboardButton(text="🎁 Yetkazildi", callback_data=f"done_{data.get('orderNumber','')}"),
        InlineKeyboardButton(text="❌ Bekor",      callback_data=f"cancel_{data.get('orderNumber','')}"),
    ]])
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            logger.warning(f"Admin {admin_id}ga yuborib bo'lmadi: {e}")

async def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN o'rnatilmagan! Railway → Variables ga qo'shing.")
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    logger.info("✅ TermizBot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
