"""
ORZUGUL — Ikki bot + API Server birga ishga tushirish
"""
import asyncio
import logging

from customer_bot import create_customer_bot
from shop_bot import create_shop_bot
from api import run_api
from database import db

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def run_bot(app, name: str):
    await app.initialize()
    await app.start()
    logger.info(f"✅ {name} ishga tushdi!")
    await app.updater.start_polling(
        allowed_updates=["message", "callback_query", "edited_message"]
    )
    await asyncio.Event().wait()


async def main():
    await db.init()
    logger.info("✅ Database tayyor")

    customer_app = create_customer_bot()
    shop_app     = create_shop_bot()

    logger.info("🚀 ORZUGUL Ekosistema ishga tushmoqda...")

    # Uchta jarayon parallel ishlaydi
    await asyncio.gather(
        run_bot(customer_app, "Mijoz boti (@OrzugulBot)"),
        run_bot(shop_app,     "Do'kon boti (@OrzugulShopBot)"),
        run_api(),            # API + Mini App server
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Tizim to'xtatildi.")
