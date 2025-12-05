# Backend Dockerfile (FastAPI + Uvicorn)
FROM python:3.11-slim

WORKDIR /app

# system deps for pdf libs (adjust if you don't use them)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpoppler-cpp-dev poppler-utils default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# expose uvicorn port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
