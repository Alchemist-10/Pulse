FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# entrypoint runs `alembic upgrade head` then the idempotent identity seed
# loader, then exec's the CMD. Synthea (Java) is dev-time only: its output
# is committed under seed/data/ and bind-mounted, so no JDK in this image.
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
