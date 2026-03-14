FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN groupadd -r app && useradd -r -g app -u 1000 app

RUN mkdir -p /shared && chmod 777 /shared

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini alembic.ini

RUN mkdir -p /home/app/.cache/uv && chown -R app:app /app /home/app

USER app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn api.main:app --host 0.0.0.0 --port 8000"]