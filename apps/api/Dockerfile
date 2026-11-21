# Build context MUST be the project root (not apps/api), because this image
# needs both packages/core and apps/api copied in. docker-compose.yml sets
# context: ../.. and dockerfile: apps/api/Dockerfile for exactly this reason.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# psycopg[binary] needs libpq at runtime on slim images
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY packages/core packages/core
COPY apps/api apps/api

RUN pip install --no-cache-dir ./packages/core ./apps/api

WORKDIR /app/apps/api
EXPOSE 8000

# --host 0.0.0.0 is required inside a container, or the port is never reachable from outside it
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]