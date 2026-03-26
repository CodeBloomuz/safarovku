FROM python:3.11-slim

WORKDIR /app

# Requirements o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha fayllarni ko'chirish
COPY . .

# Ishga tushirish
CMD ["python", "run.py"]
