# Stockify - Backend FastAPI
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Layer caching: requirements di-install sebelum source di-copy.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Source backend (backend/.env dan *.db tidak ikut, lihat .dockerignore).
COPY backend/ ./

EXPOSE 8000

# Backend harus listen di 0.0.0.0 agar bisa diakses dari container lain.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
