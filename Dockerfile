FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run.py"]
```

---

**2. Railway da Start Command ni o'zgartiring:**

Railway dashboard → Sizning service → **Settings** tab → **Deploy** bo'limi → **Start Command** ga:
```
python run.py
