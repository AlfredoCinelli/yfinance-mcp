FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy package source and install
COPY src/ ./src/
RUN uv sync --frozen --no-dev

EXPOSE 1000

ENTRYPOINT ["uv", "run", "finance-mcp-server"]
