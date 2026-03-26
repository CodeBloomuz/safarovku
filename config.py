# ════════════════════════════════════════════════
# ORZUGUL — Konfiguratsiya
# ════════════════════════════════════════════════

# ── Bot tokenlar (@BotFather dan oling) ─────────
CUSTOMER_BOT_TOKEN = "8648436007:AAELNuhZcPqdv977Po3fB7sR41qJHQsx-q4"   # @OrzugulBot
SHOP_BOT_TOKEN     = "8415013128:AAHJjjnjFyaGhMDSMo32TCa0u0kwvWtZ83M"   # @OrzugulShopBot
ADMIN_BOT_TOKEN    = "8693071773:AAGzyOvTmLVQc5Jbd6bxnQEpGH5ysv3rVz8"   # @OrzugulAdminBot

# ── Admin Telegram ID lari ───────────────────────
ADMIN_IDS = [6551375195]

# ── Ma'lumotlar bazasi ───────────────────────────
DATABASE_PATH = "orzugul.db"

# ── Telegram Mini App URL ────────────────────────
WEBAPP_URL = "https://yourdomain.com/webapp/index.html"

# ── Botlar USERNAME lari ─────────────────────────
CUSTOMER_BOT_USERNAME = "@OrzugulBot"
SHOP_BOT_USERNAME     = "@OrzugulShopBot"
ADMIN_BOT_USERNAME    = "@OrzugulAdminBot"

# ── Mahsulot sozlamalari ─────────────────────────
MIN_PRODUCTS = 5

# ── Xabar matnlari ──────────────────────────────
WELCOME_CUSTOMER = """
🌸 *ORZUGUL*ga xush kelibsiz!

Sizga eng go'zal gullar va mazali shirinliklarni yetkazib beramiz 🍰

Quyidagilardan birini tanlang:
"""

WELCOME_SHOP = """
🏪 *ORZUGUL* Do'kon Tizimiga Xush Kelibsiz!

Bu bot orqali siz:
✅ Do'koningizni ro'yxatdan o'tkaza olasiz
✅ Mahsulotlaringizni qo'sha olasiz
✅ Kelgan zakazlarni ko'ra olasiz

Boshlash uchun /start ni bosing
"""

ORDER_NOTIFICATION = """
🔔 *Yangi Zakaz!*

👤 Mijoz: {customer_name}
📱 Tel: {customer_phone}
🛍 Mahsulot: {product_name}
🔢 Miqdor: {quantity} ta
💰 Jami: {total_price} so'm
📍 Manzil: {address}
{delivery_note}
⏰ Vaqt: {time}
"""
