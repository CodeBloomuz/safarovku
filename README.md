# 🌸 ORZUGUL — Telegram Bot Ekosistema

## Loyiha tuzilmasi

```
orzugul/
├── config.py          # Token va sozlamalar
├── database.py        # SQLite ma'lumotlar bazasi
├── customer_bot.py    # Mijoz boti (@OrzugulBot)
├── shop_bot.py        # Do'kon boti (@OrzugulShopBot)
├── run.py             # Ikki botni birga ishga tushirish
├── requirements.txt
└── webapp/
    └── index.html     # Telegram Mini App
```

## O'rnatish

```bash
pip install -r requirements.txt
```

## Sozlash

`config.py` faylida:
- `CUSTOMER_BOT_TOKEN` — mijoz botining tokeni (@BotFather dan)
- `SHOP_BOT_TOKEN` — do'kon botining tokeni
- `ADMIN_IDS` — admin Telegram ID lari

## Ishga tushirish

```bash
python run.py
```

## Botlar

| Bot | Maqsad |
|-----|--------|
| @OrzugulBot | Mijozlar uchun — buyurtma berish, Mini App |
| @OrzugulShopBot | Do'konlar uchun — ro'yxat, mahsulot, zakazlar |

## Oqim

### Do'kon ro'yxatdan o'tishi:
1. @OrzugulShopBot ga /start
2. Xizmat turi → Gul / Shirinlik
3. Do'kon nomi, manzil, telefon
4. Yetkazib berish bormi?
5. Kamida 5 ta mahsulot (rasm + narx)
6. Tasdiqlash kutish

### Mijoz buyurtmasi:
1. @OrzugulBot ga /start
2. Mini App yoki inline — Gullar / Shirinliklar
3. Do'kon tanlash
4. Mahsulot tanlash
5. Miqdor + manzil
6. Do'kon egasiga bildirishnoma

### Admin:
- /stats — statistika
- /shops — do'konlar ro'yxati
- /orders — barcha zakazlar
- Do'konni tasdiqlash/rad etish
