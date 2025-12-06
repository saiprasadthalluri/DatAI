FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy all application files first
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini ./
COPY pyproject.toml ./
COPY ./add_columns.py ./

# Install dependencies (not editable for production)
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port (Cloud Run uses 8080)
EXPOSE 8080

# Start server (skip migrations for now - run separately)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]




