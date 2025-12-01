
FROM python:3.11-slim

# تثبيت المكتبات المطلوبة
RUN apt-get update && apt-get install -y \
    ffmpeg \
    stunnel4 \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ الملفات
COPY . .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir \
    python-telegram-bot==20.7 \
    python-dotenv==1.0.0 \
    Flask==3.0.0

# إنشاء مجلد stunnel
RUN mkdir -p /tmp/stunnel

# المنفذ
EXPOSE 10000

# تشغيل البوت
CMD ["python", "bot.py"]
