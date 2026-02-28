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
        gosu \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# RUN groupadd -r django && useradd -r -g django django

RUN addgroup -g 1000 django \
    && adduser -D -u 1000 -G django django
USER django

# Install Python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Create directories with correct permissions
RUN mkdir -p /usr/src/app/staticfiles /usr/src/app/media /usr/src/app/celerybeat /usr/src/app/logs \
    && chown -R django:django /usr/src/app

# Make entrypoint executable
RUN chmod +x /usr/src/app/docker/entrypoint.sh

# Expose port
EXPOSE 8000

# run the application with ASGI (async)
ENTRYPOINT ["/usr/src/app/docker/entrypoint.sh"]
