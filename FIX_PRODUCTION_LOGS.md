# Fix Production Logging Errors

## Problem
Services (Django, Celery, Celery Beat) are failing with:
```
PermissionError: [Errno 13] Permission denied: '/usr/src/app/logs/app.log'
```

This causes:
- Django to crash (Nginx 502 errors)
- Celery workers to fail
- Celery Beat scheduler to fail

## Solution
Added `logs_volume` to docker-compose.yml for proper log file permissions.

## Deployment Steps (Run on Production Server)

```bash
# 1. Navigate to application directory
cd /srv/apps/mendeleyev-backend

# 2. Pull latest changes
git pull origin main

# 3. Stop all services
docker compose down

# 4. Remove old containers (if needed)
docker compose rm -f

# 5. Start services with new configuration
docker compose up -d

# 6. Watch logs to verify everything starts correctly
docker compose logs -f

# 7. Check service health
docker compose ps
```

## Expected Result
All services should start successfully:
- ✅ mendeleyev_db: healthy
- ✅ mendeleyev_redis: healthy
- ✅ mendeleyev_django: healthy
- ✅ mendeleyev_celery: running
- ✅ mendeleyev_celery_beat: running
- ✅ mendeleyev_nginx: healthy

## Verification
```bash
# Check Django is responding
curl http://localhost:8180/admin/

# Check logs are being written
docker compose exec mendeleyev_django ls -la /usr/src/app/logs/

# View application logs
docker compose logs mendeleyev_django --tail 50
```

## What Changed
- Added `logs_volume:/usr/src/app/logs` mount to:
  - mendeleyev_django service
  - mendeleyev_celery service
  - mendeleyev_celery_beat service
- Created new named volume `logs_volume` for persistent log storage

## Rollback (if needed)
```bash
git checkout HEAD~1
docker compose down
docker compose up -d
```
