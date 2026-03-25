CMD ["python", "bot.py"]
```

**Variant B** — Agar `bot/` papka umuman yo'q bo'lsa:
```
safarovku/
├── bot/
│   └── bot.py
```
Shu tuzilmada fayl yarating.

**Variant C** — Railway'da `Procfile` orqali:
Repoga `Procfile` fayl qo'shing:
```
worker: python bot/bot.py
