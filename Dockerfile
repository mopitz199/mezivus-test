FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM base AS local
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS production
CMD ["gunicorn", "mezivus.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4"]