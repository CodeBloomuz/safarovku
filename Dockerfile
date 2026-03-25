FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

---

## `requirements.txt` fayli ham bo'lishi kerak:
```
aiogram==3.7.0
