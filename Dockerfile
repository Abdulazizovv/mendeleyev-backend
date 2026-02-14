# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /usr/src/app

# Install system dependencies (including curl for healthcheck)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r django && useradd -r -g django django

# Install Python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Create directories with correct permissions
RUN mkdir -p /usr/src/app/staticfiles /usr/src/app/media /usr/src/app/celerybeat \
    && chown -R django:django /usr/src/app

# Make entrypoint executable
RUN chmod +x /usr/src/app/docker/entrypoint.sh

# Switch to non-root user (PRODUCTION)
# Comment this line for development if you get permission errors
USER django

# Expose port
EXPOSE 8000

# run the application with ASGI (async)
ENTRYPOINT ["/usr/src/app/docker/entrypoint.sh"]