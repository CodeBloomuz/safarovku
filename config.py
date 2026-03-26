# ════════════════════════════════════════════════
#  ORZUGUL — Konfiguratsiya
#  Bu faylni o'zingizning tokenlaringiz bilan to'ldiring
# ════════════════════════════════════════════════

# ── Bot tokenlar (@BotFather dan oling) ─────────
CUSTOMER_BOT_TOKEN = "8648436007:AAELNuhZcPqdv977Po3fB7sR41qJHQsx-q4"       # @OrzugulBot tokeni
SHOP_BOT_TOKEN     = "8415013128:AAHJjjnjFyaGhMDSMo32TCa0u0kwvWtZ83M"        # @OrzugulShopBot tokeni

# ── Admin Telegram ID lari ───────────────────────
ADMIN_IDS = [123456789]   # O'zingizning Telegram ID ingiz

# ── Ma'lumotlar bazasi ───────────────────────────
DATABASE_PATH = "orzugul.db"

# ── Telegram Mini App URL ────────────────────────
# Mini App ni hosting ga joylashtirgandan keyin URL ni qo'ying
# Masalan: https://yourdomain.com/orzugul/webapp/index.html
# Yoki GitHub Pages: https://username.github.io/orzugul/
WEBAPP_URL = "https://yourdomain.com/webapp/index.html"

# ── Botlar USERNAME lari ─────────────────────────
CUSTOMER_BOT_USERNAME = "@OrzugulBot"
SHOP_BOT_USERNAME     = "@OrzugulShopBot"

# ── Mahsulot sozlamalari ─────────────────────────
MIN_PRODUCTS = 5          # Do'kon uchun minimal mahsulot soni

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
