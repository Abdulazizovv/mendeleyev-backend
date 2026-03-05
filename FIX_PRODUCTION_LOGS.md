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
This error happens when the container runs as the non-root `django` user while `/usr/src/app/logs` is a Docker volume (or bind mount) owned by `root`, so the process can’t create/write `app.log`.

Fix is two parts:
1) Start the container as `root` and let `docker/entrypoint.sh` `chown` the mounted volumes, then drop privileges to `django` via `gosu`.
2) Ensure the services that run the entrypoint have `CAP_CHOWN` (`cap_add: CHOWN`) so the permission fix actually works even with `cap_drop: ALL`.

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
- `Dockerfile`: removed `USER django` so the entrypoint runs as `root` first and can fix mounted volume permissions, then drops to `django`.
- `docker-compose.yml`: added `cap_add: CHOWN` to `mendeleyev_celery` and `mendeleyev_celery_beat` (Django already had it).

## Rollback (if needed)
```bash
git checkout HEAD~1
docker compose down
docker compose up -d
```
