FROM python:3.12-slim

ENV APP_ENV=development \
    HOST=0.0.0.0 \
    PORT=8766 \
    CATALOG_DB_PATH=/data/catalog.sqlite3 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir /data \
    && chown app:app /data

COPY --chown=app:app . .

USER app
EXPOSE 8766
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8766", "--database", "/data/catalog.sqlite3"]

