FROM python:3.13-slim-trixie

WORKDIR /mdm-platform

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Ensure logs are immediately written to stdout/stderr
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application source
COPY . .

# Make scripts executable
RUN chmod +x ./scripts/init.sh \
    && chmod +x ./scripts/runner.sh

CMD ["./scripts/runner.sh"]