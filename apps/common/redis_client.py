from __future__ import annotations

import redis
from urllib.parse import urlparse
from django.conf import settings
from typing import Optional

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        # Prefer explicit env-style attributes if present; else parse from CELERY_BROKER_URL
        url = getattr(settings, "CELERY_BROKER_URL", "redis://redis:6379/0")
        parsed = urlparse(url)
        host = getattr(settings, "REDIS_HOST", None) or parsed.hostname or "redis"
        port = int(getattr(settings, "REDIS_PORT", None) or (parsed.port or 6379))
        # Allow override of DB used for OTP via OTP_REDIS_DB env
        db = int(getattr(settings, "OTP_REDIS_DB", None) or (parsed.path.lstrip("/") or 0))
        _redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    return _redis_client
