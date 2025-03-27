FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

COPY --from=ghcr.io/astral-sh/uv:0.6.10 /uv /bin/uv

ENV PATH="/app/.venv/bin:$PATH"

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/app

RUN useradd -ms /bin/bash celery

COPY --chown=celery:celery ./scripts /app/scripts

COPY --chown=celery:celery ./pyproject.toml ./uv.lock /app/

COPY --chown=celery:celery ./src /app/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

CMD ["fastapi", "run", "--workers", "4", "src/main.py"]
