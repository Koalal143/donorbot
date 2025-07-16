FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ARG MODE=prod
ENV PYTHONPATH="/app" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1 \
    MODE=$MODE

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "$MODE" = "dev" ]; then \
        uv sync --frozen --no-install-project --group dev; \
    else \
        uv sync --frozen --no-install-project; \
    fi

ADD . /app

FROM python:3.12-slim-bookworm

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

CMD python src/main.py
