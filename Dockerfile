# Python 3.11 жеңілдетілген нұсқасын қолданамыз
FROM python:3.11-slim

# Жұмыс папкасын орнату
WORKDIR /app

# Тәуелділіктерді орнату
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Жоба файлдарын көшіру
COPY server.py .
COPY core/ core/
COPY static/ static/

# VAPID кілттерін көшіру (егер бар болса)
COPY server.py vapid_*.pe[m] ./

# Flask/aiohttp портты ашу
EXPOSE 7435

# Серверді қосу
CMD ["python", "server.py"]
