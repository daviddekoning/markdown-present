FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Defaults to running Uvicorn on 8080
ENV PORT=8080

# Copy lock and project files
COPY pyproject.toml ./
# If uv.lock exists, it'll copy it. If not, we still need to sync.
COPY uv.lock* ./

# Install dependencies (without creating a virtual environment, we can just use uv run which automatically resolves)
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy application code
COPY backend /app/backend
COPY frontend /app/frontend

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
