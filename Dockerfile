FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

# Copy application code
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Non-root user
RUN useradd -m -u 1000 pyworkspace
USER pyworkspace

EXPOSE 8080

# Default: run the API server
CMD ["uvicorn", "pyworkspace.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
