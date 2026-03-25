# 🚀 GitHub + Railway — To'liq Qo'llanma

---

## PAPKA TUZILISHI (GitHub ga shunday yuklang)

```
termizbot/
├── bot/
│   └── bot.py
├── miniapp/
│   └── index.html
├── requirements.txt
├── railway.toml
├── Procfile
└── .gitignore
```

---

## 1-QADAM — GitHub Repo yaratish

1. **github.com** ga kiring (hisob yo'q bo'lsa yarating)
2. **"New repository"** tugmasini bosing
3. Repository nomi: `termizbot`
4. **Public** tanlang
5. **"Create repository"** bosing

---

## 2-QADAM — Fayllarni GitHub ga yuklash

Ochilgan sahifada **"uploading an existing file"** havolasini bosing.

Quyidagi fayllarni **birma-bir** yuklang:
- `bot/bot.py`  (bot papkasi ichida)
- `miniapp/index.html`  (miniapp papkasi ichida)
- `requirements.txt`
- `railway.toml`
- `Procfile`
- `.gitignore`

> ⚠️ Papkalarni to'g'ri joylashtiring:
> Upload vaqtida fayl nomini `bot/bot.py` deb yozing — GitHub papka yaratadi.

**"Commit changes"** tugmasini bosing.

---

## 3-QADAM — Mini App ni GitHub Pages ga chiqarish

1. GitHub repo → **Settings** tab
2. Chap menyu → **Pages**
3. Source: **Deploy from a branch**
4. Branch: **main**,  Folder: **/ (root)** — lekin bizda miniapp papkasida
5. Saqlang

> ⚠️ index.html root da bo'lishi kerak.
> Shuning uchun `miniapp/index.html` ni to'g'ridan **root ga** ham ko'chiring:
> Ya'ni `index.html` nomli fayl repo asosida bo'lsin.

**Sizning Mini App URL:** `https://GITHUBNOM.github.io/termizbot`

---

## 4-QADAM — BotFather dan token olish

1. Telegramda **@BotFather** ga boring
2. `/newbot` yozing
3. Bot nomi kiriting: `Termiz Flowers`
4. Username: `termizflowers_bot` (yoki boshqa)
5. BotFather **TOKEN** beradi — uni saqlang

---

## 5-QADAM — Admin ID olish

1. Telegramda **@userinfobot** ga `/start` yozing
2. U sizning **ID** ingizni ko'rsatadi
3. Masalan: `987654321`

---

## 6-QADAM — Railway da deploy qilish

### 6.1 — Railway hisob yaratish
1. **railway.app** ga boring
2. **"Start a New Project"**
3. **GitHub bilan kirish** (Login with GitHub)

### 6.2 — GitHub repo ulash
1. **"Deploy from GitHub repo"** bosing
2. `termizbot` ni tanlang
3. Railway avtomatik `requirements.txt` ni topadi

### 6.3 — Environment Variables qo'shish
Railway dashboard → Sizning loyiha → **Variables** tab:

| Kalit (Key)    | Qiymat (Value)                              |
|----------------|---------------------------------------------|
| `BOT_TOKEN`    | BotFather dan olgan token                   |
| `ADMIN_IDS`    | Sizning Telegram ID (masalan: `987654321`)  |
| `MINI_APP_URL` | `https://GITHUBNOM.github.io/termizbot`     |
| `SHOP_PHONE`   | `+998 90 XXX XX XX`                         |

### 6.4 — Deploy
Variables saqlangandan so'ng Railway avtomatik **restart** qiladi.

**Logs** tab da ko'ring:
```
✅ TermizBot ishga tushdi!
```

---

## 7-QADAM — BotFather da Mini App ulash

1. @BotFather → `/mybots`
2. Botingizni tanlang
3. **Bot Settings** → **Menu Button** → **Configure menu button**
4. URL: `https://GITHUBNOM.github.io/termizbot`
5. Text: `🌸 Buyurtma berish`

---

## 8-QADAM — Tekshirish

1. Botingizga `/start` yozing
2. `🌸 Buyurtma berish` tugmasini bosing
3. Mini App ochilishi kerak
4. Test buyurtma bering
5. Sizning Telegram ga xabar kelishi kerak ✅

---

## ADMIN BUYRUQLAR

Bot ichida yozing:
- `/admin` — oxirgi 10 buyurtma
- `/orders` — barchasi (tasdiqlash/bekor tugmalari bilan)

---

## MUAMMOLAR VA YECHIMLARI

**Bot javob bermayapti:**
→ Railway → Logs tekshiring
→ BOT_TOKEN to'g'ri ekanini tekshiring

**Mini App ochilmayapti:**
→ GitHub Pages faol ekanini tekshiring (Settings → Pages)
→ MINI_APP_URL to'g'ri ekanini tekshiring

**Xabar kelmayapti:**
→ ADMIN_IDS to'g'ri ekanini tekshiring
→ @userinfobot da ID ni qayta tekshiring

---

*Har qanday savol bo'lsa — so'rang!* 🚀
