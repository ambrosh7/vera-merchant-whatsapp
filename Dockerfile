FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/
COPY bot.py .
COPY conversation_handlers.py .
COPY dataset/ dataset/
COPY .env.example .env.example

EXPOSE 8080

# Keep a single long-lived process for the test window (no workers restart churn).
CMD ["uvicorn", "bot.app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "75"]
