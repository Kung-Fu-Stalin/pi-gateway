FROM python:3.12-slim-bookworm
LABEL authors="kung_fu_stalin"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN groupadd -r app && useradd -r -g app app

RUN mkdir -p /data /var/log/squid && chown app:app /data /var/log/squid

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY src/ src/
COPY migrations/ migrations/
COPY templates/ templates/
COPY alembic.ini alembic.ini

RUN mkdir -p /home/app/.cache/uv && chown -R app:app /app /home/app

USER app

RUN mkdir -p /data && touch /data/domains.txt /data/passwd /data/db.sqlite3 && chown -R app:app /data

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn api.main:app --host 0.0.0.0 --port 8000"]