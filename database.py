"""
ORZUGUL — Ma'lumotlar bazasi
SQLite + aiosqlite (async)
"""
import aiosqlite
import asyncio
from datetime import datetime
from config import DATABASE_PATH


# ════════════════════════════════════════════════
#  JADVALLAR YARATISH
# ════════════════════════════════════════════════

CREATE_TABLES = """
-- Do'konlar jadvali
CREATE TABLE IF NOT EXISTS shops (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        INTEGER NOT NULL UNIQUE,   -- Telegram user_id
    owner_username  TEXT,
    shop_type       TEXT NOT NULL,             -- 'flower' | 'sweet'
    name            TEXT NOT NULL,
    address         TEXT NOT NULL,
    phone           TEXT NOT NULL,
    has_delivery    INTEGER DEFAULT 0,          -- 0 yoki 1
    is_approved     INTEGER DEFAULT 0,          -- Admin tasdiqlashi
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- Mahsulotlar jadvali
CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id         INTEGER NOT NULL REFERENCES shops(id),
    name            TEXT NOT NULL,
    photo_id        TEXT NOT NULL,             -- Telegram file_id
    product_type    TEXT NOT NULL,             -- 'flower' | 'sweet'

    -- Gul uchun
    single_price    INTEGER DEFAULT 0,         -- Dona narxi (so'm)
    bouquet_price   INTEGER DEFAULT 0,         -- Buket narxi (so'm)
    flower_delivery INTEGER DEFAULT 0,

    -- Shirinlik uchun
    piece_price     INTEGER DEFAULT 0,         -- Bo'lak narxi
    full_price      INTEGER DEFAULT 0,         -- Butun tort narxi
    sweet_delivery  INTEGER DEFAULT 0,

    is_available    INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- Zakazlar jadvali
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id         INTEGER NOT NULL REFERENCES shops(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    customer_id     INTEGER NOT NULL,           -- Telegram user_id
    customer_name   TEXT,
    customer_phone  TEXT,
    quantity        INTEGER DEFAULT 1,
    order_type      TEXT NOT NULL,              -- 'single'|'bouquet'|'piece'|'full'
    total_price     INTEGER NOT NULL,
    address         TEXT NOT NULL,
    needs_delivery  INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'new',         -- 'new'|'accepted'|'done'|'cancelled'
    note            TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- Mijozlar jadvali (ixtiyoriy — statistika uchun)
CREATE TABLE IF NOT EXISTS customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id     INTEGER NOT NULL UNIQUE,
    username        TEXT,
    full_name       TEXT,
    phone           TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- Do'kon ro'yxatdan o'tish jarayoni (bosqichlar)
CREATE TABLE IF NOT EXISTS shop_registration (
    owner_id        INTEGER PRIMARY KEY,
    step            TEXT DEFAULT 'type',
    shop_type       TEXT,
    name            TEXT,
    address         TEXT,
    phone           TEXT,
    has_delivery    INTEGER,
    product_count   INTEGER DEFAULT 0,
    temp_product    TEXT   -- JSON: hozirgi qo'shilayotgan mahsulot
);
"""


# ════════════════════════════════════════════════
#  ASOSIY DATABASE KLASSI
# ════════════════════════════════════════════════

class Database:
    def __init__(self, path=DATABASE_PATH):
        self.path = path

    async def init(self):
        """Bazani ishga tushirish va jadvallarni yaratish"""
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(CREATE_TABLES)
            await db.commit()
        print(f"✅ Database tayyor: {self.path}")

    # ── SHOPS ────────────────────────────────────

    async def get_shops_by_type(self, shop_type: str) -> list:
        """Tasdiqlangan do'konlarni olish"""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM shops WHERE shop_type=? AND is_approved=1 AND is_active=1",
                (shop_type,)
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_shop_by_owner(self, owner_id: int) -> dict | None:
        """Do'kon egasi bo'yicha do'kon topish"""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM shops WHERE owner_id=?", (owner_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_shop_by_id(self, shop_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM shops WHERE id=?", (shop_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def create_shop(self, owner_id, owner_username, shop_type,
                          name, address, phone, has_delivery) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """INSERT INTO shops (owner_id, owner_username, shop_type, name, address, phone, has_delivery)
                   VALUES (?,?,?,?,?,?,?)""",
                (owner_id, owner_username, shop_type, name, address, phone, has_delivery)
            )
            await db.commit()
            return cursor.lastrowid

    async def approve_shop(self, shop_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE shops SET is_approved=1 WHERE id=?", (shop_id,))
            await db.commit()

    async def get_all_shops(self) -> list:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM shops ORDER BY created_at DESC") as c:
                return [dict(r) for r in await c.fetchall()]

    # ── PRODUCTS ─────────────────────────────────

    async def add_product(self, shop_id, name, photo_id, product_type,
                          single_price=0, bouquet_price=0, flower_delivery=0,
                          piece_price=0, full_price=0, sweet_delivery=0) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """INSERT INTO products
                   (shop_id, name, photo_id, product_type,
                    single_price, bouquet_price, flower_delivery,
                    piece_price, full_price, sweet_delivery)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (shop_id, name, photo_id, product_type,
                 single_price, bouquet_price, flower_delivery,
                 piece_price, full_price, sweet_delivery)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_products_by_shop(self, shop_id: int) -> list:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM products WHERE shop_id=? AND is_available=1", (shop_id,)
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_product_by_id(self, product_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM products WHERE id=?", (product_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def count_products(self, shop_id: int) -> int:
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM products WHERE shop_id=?", (shop_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ── ORDERS ───────────────────────────────────

    async def create_order(self, shop_id, product_id, customer_id, customer_name,
                           customer_phone, quantity, order_type, total_price,
                           address, needs_delivery, note="") -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """INSERT INTO orders
                   (shop_id, product_id, customer_id, customer_name, customer_phone,
                    quantity, order_type, total_price, address, needs_delivery, note)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (shop_id, product_id, customer_id, customer_name, customer_phone,
                 quantity, order_type, total_price, address, needs_delivery, note)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_orders_by_shop(self, shop_id: int, status=None) -> list:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                q = "SELECT o.*, p.name as product_name FROM orders o JOIN products p ON o.product_id=p.id WHERE o.shop_id=? AND o.status=? ORDER BY o.created_at DESC"
                args = (shop_id, status)
            else:
                q = "SELECT o.*, p.name as product_name FROM orders o JOIN products p ON o.product_id=p.id WHERE o.shop_id=? ORDER BY o.created_at DESC"
                args = (shop_id,)
            async with db.execute(q, args) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_all_orders(self) -> list:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT o.*, p.name as product_name, s.name as shop_name
                   FROM orders o
                   JOIN products p ON o.product_id=p.id
                   JOIN shops s ON o.shop_id=s.id
                   ORDER BY o.created_at DESC LIMIT 50"""
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def update_order_status(self, order_id: int, status: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
            await db.commit()

    async def get_order_by_id(self, order_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT o.*, p.name as product_name, s.name as shop_name, s.owner_id as shop_owner_id
                   FROM orders o
                   JOIN products p ON o.product_id=p.id
                   JOIN shops s ON o.shop_id=s.id
                   WHERE o.id=?""",
                (order_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # ── REGISTRATION PROGRESS ────────────────────

    async def set_reg_step(self, owner_id: int, **kwargs):
        """Ro'yxatdan o'tish bosqichini saqlash"""
        async with aiosqlite.connect(self.path) as db:
            # Mavjudligini tekshirish
            async with db.execute(
                "SELECT owner_id FROM shop_registration WHERE owner_id=?", (owner_id,)
            ) as c:
                exists = await c.fetchone()

            if exists:
                sets = ", ".join(f"{k}=?" for k in kwargs)
                vals = list(kwargs.values()) + [owner_id]
                await db.execute(f"UPDATE shop_registration SET {sets} WHERE owner_id=?", vals)
            else:
                kwargs["owner_id"] = owner_id
                cols = ", ".join(kwargs.keys())
                placeholders = ", ".join("?" * len(kwargs))
                await db.execute(
                    f"INSERT INTO shop_registration ({cols}) VALUES ({placeholders})",
                    list(kwargs.values())
                )
            await db.commit()

    async def get_reg(self, owner_id: int) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM shop_registration WHERE owner_id=?", (owner_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def delete_reg(self, owner_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM shop_registration WHERE owner_id=?", (owner_id,))
            await db.commit()

    # ── CUSTOMERS ────────────────────────────────

    async def upsert_customer(self, telegram_id, username, full_name, phone=None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO customers (telegram_id, username, full_name, phone)
                   VALUES (?,?,?,?)
                   ON CONFLICT(telegram_id) DO UPDATE SET
                   username=excluded.username, full_name=excluded.full_name""",
                (telegram_id, username, full_name, phone)
            )
            await db.commit()

    # ── STATISTICS ───────────────────────────────

    async def get_stats(self) -> dict:
        async with aiosqlite.connect(self.path) as db:
            stats = {}
            for key, query in [
                ("total_shops", "SELECT COUNT(*) FROM shops"),
                ("approved_shops", "SELECT COUNT(*) FROM shops WHERE is_approved=1"),
                ("flower_shops", "SELECT COUNT(*) FROM shops WHERE shop_type='flower' AND is_approved=1"),
                ("sweet_shops", "SELECT COUNT(*) FROM shops WHERE shop_type='sweet' AND is_approved=1"),
                ("total_orders", "SELECT COUNT(*) FROM orders"),
                ("new_orders", "SELECT COUNT(*) FROM orders WHERE status='new'"),
                ("total_customers", "SELECT COUNT(*) FROM customers"),
            ]:
                async with db.execute(query) as c:
                    row = await c.fetchone()
                    stats[key] = row[0] if row else 0
            return stats


# Global instance
db = Database()
