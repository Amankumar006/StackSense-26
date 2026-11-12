FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and project files
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY data/ /app/data/
COPY tests/ /app/tests/

# Install StackSense and its dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create outputs directory
RUN mkdir -p /app/outputs

ENTRYPOINT ["stacksense"]
CMD ["--help"]
