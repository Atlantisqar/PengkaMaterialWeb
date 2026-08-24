FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /storage/attachments
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed_default_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
