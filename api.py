"""
ORZUGUL — API Server (aiohttp)
Mini App uchun real-time ma'lumot beradi
"""
import asyncio
import aiohttp
from aiohttp import web
from database import db
from config import CUSTOMER_BOT_TOKEN

API_PORT = 8080


# ════════════════════════════════════════════════
#  CORS va JSON yordamchisi
# ════════════════════════════════════════════════

def json_response(data, status=200):
    return web.Response(
        text=__import__("json").dumps(data, ensure_ascii=False),
        content_type="application/json",
        status=status,
        headers={
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )


async def options_handler(request):
    return web.Response(
        headers={
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )


# ════════════════════════════════════════════════
#  ENDPOINTLAR
# ════════════════════════════════════════════════

async def get_shops(request):
    """GET /api/shops?type=flower|sweet"""
    shop_type = request.rel_url.query.get("type")
    if shop_type:
        shops = await db.get_shops_by_type(shop_type)
    else:
        shops = await db.get_all_shops()
    # is_approved filtr
    shops = [s for s in shops if s.get("is_approved")]
    return json_response(shops)


async def get_shop(request):
    """GET /api/shops/{id}"""
    shop_id = int(request.match_info["id"])
    shop = await db.get_shop_by_id(shop_id)
    if not shop or not shop.get("is_approved"):
        return json_response({"error": "topilmadi"}, 404)
    return json_response(shop)


async def get_products(request):
    """GET /api/products?shop_id=1"""
    shop_id = request.rel_url.query.get("shop_id")
    if not shop_id:
        return json_response({"error": "shop_id kerak"}, 400)
    products = await db.get_products_by_shop(int(shop_id))
    # Har bir mahsulotga rasm URL qo'shish
    for p in products:
        p["photo_url"] = f"/api/photo/{p['photo_id']}"
    return json_response(products)


async def get_photo(request):
    """
    GET /api/photo/{file_id}
    Telegram file_id → rasmni proksi qilib beradi
    Mini App rasm ko'rish uchun ishlatadi
    """
    file_id = request.match_info["file_id"]

    # Telegram'dan fayl URL ni olish
    tg_url = f"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/getFile?file_id={file_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(tg_url) as resp:
                data = await resp.json()

            if not data.get("ok"):
                raise ValueError("Fayl topilmadi")

            file_path = data["result"]["file_path"]
            img_url = f"https://api.telegram.org/file/bot{CUSTOMER_BOT_TOKEN}/{file_path}"

            # Rasmni olib, foydalanuvchiga uzatish
            async with session.get(img_url) as img_resp:
                content_type = img_resp.headers.get("Content-Type", "image/jpeg")
                img_data = await img_resp.read()

        return web.Response(
            body=img_data,
            content_type=content_type,
            headers={"Access-Control-Allow-Origin": "*",
                     "Cache-Control": "public, max-age=86400"}
        )
    except Exception as e:
        # Fallback — placeholder rasm
        return web.Response(
            body=b"",
            status=404,
            headers={"Access-Control-Allow-Origin": "*"}
        )


async def get_stats(request):
    """GET /api/stats"""
    stats = await db.get_stats()
    return json_response(stats)


# ════════════════════════════════════════════════
#  APP YARATISH
# ════════════════════════════════════════════════

def create_api_app():
    app = web.Application()
    app.router.add_get ("/api/shops",          get_shops)
    app.router.add_get ("/api/shops/{id}",     get_shop)
    app.router.add_get ("/api/products",       get_products)
    app.router.add_get ("/api/photo/{file_id}", get_photo)
    app.router.add_get ("/api/stats",          get_stats)
    app.router.add_route("OPTIONS", "/{path_info:.*}", options_handler)

    # Mini App faylini statik berish
    import os
    webapp_dir = os.path.join(os.path.dirname(__file__), "webapp")
    app.router.add_static("/", path=webapp_dir, name="static")

    return app


async def run_api():
    app = create_api_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", API_PORT)
    await site.start()
    print(f"✅ API Server: http://localhost:{API_PORT}")
    print(f"   Mini App:   http://localhost:{API_PORT}/index.html")
    await asyncio.Event().wait()
