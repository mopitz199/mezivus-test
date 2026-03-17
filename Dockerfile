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
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]

FROM base AS production
RUN python manage.py collectstatic --noinput
# The PORT is set by Cloud Run, so we use it in the command to bind the server to the correct port.
CMD ["sh", "-c", "gunicorn mezivus.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4"]