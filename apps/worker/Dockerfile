# Same reasoning as apps/api/Dockerfile: build context is the project root.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY packages/core packages/core
COPY apps/worker apps/worker

RUN pip install --no-cache-dir ./packages/core ./apps/worker

WORKDIR /app/apps/worker

# No --pool=solo here: that flag exists only for Windows. The container is Linux,
# so Celery's default prefork pool is used, which is faster and the normal choice.
CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]