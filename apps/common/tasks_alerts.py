import hashlib
import os
from typing import Iterable, List, Optional

import httpx
from celery import shared_task

try:
    import redis as redis_lib
except Exception:  # pragma: no cover
    redis_lib = None


def _chunk(text: str, size: int = 3800) -> Iterable[str]:
    for i in range(0, len(text), size):
        yield text[i : i + size]


def _get_redis():  # -> Optional[redis.Redis]
    if redis_lib is None:
        return None
    url = os.getenv("ALERT_REDIS_URL")
    if not url:
        # fallback to standard redis envs
        host = os.getenv("REDIS_HOST", "redis")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "0"))
        url = f"redis://{host}:{port}/{db}"
    try:
        return redis_lib.from_url(url)
    except Exception:
        return None


def _should_send(text: str, ttl: int) -> bool:
    r = _get_redis()
    if not r:
        return True  # no redis: no throttling
    # fingerprint based on first part to avoid token-specific mismatch
    base = text.strip().splitlines()
    head = "\n".join(base[:10])[:1000]
    fingerprint = hashlib.sha256(head.encode("utf-8")).hexdigest()
    key = f"alert:{fingerprint}"
    try:
        # SETNX with TTL via set(name, value, nx=True, ex=ttl)
        created = r.set(key, "1", nx=True, ex=ttl)
        return bool(created)
    except Exception:
        return True


def _get_admins_and_token() -> tuple[List[str], Optional[str]]:
    token = os.getenv("BOT_TOKEN")
    admins_env = os.getenv("ADMINS", "")
    admins = [a.strip() for a in admins_env.split(",") if a.strip()]
    return admins, token


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_telegram_alert_task(self, text: str, chat_ids: Optional[List[str]] = None) -> None:
    admins, token = _get_admins_and_token()
    if chat_ids:
        admins = chat_ids
    if not token or not admins:
        return

    throttle = int(os.getenv("ALERT_THROTTLE_SECONDS", "120"))
    if not _should_send(text, throttle):
        return

    api_base = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org")
    url = f"{api_base}/bot{token}/sendMessage"
    timeout = float(os.getenv("ALERT_HTTP_TIMEOUT", "5"))

    with httpx.Client(timeout=timeout) as client:
        for part in _chunk(text):
            for chat_id in admins:
                try:
                    client.post(url, data={"chat_id": chat_id, "text": part})
                except Exception as e:
                    # let autoretry handle transient failures
                    raise e


@shared_task(bind=True)
def send_unknown_phone_attempt_task(self, phone: str) -> None:
    """Notify admins that an unknown phone tried to access the system (Uzbek message).

    Per-phone throttle for a short window to avoid spam.
    """
    # Per-phone throttling (5 minutes)
    try:
        r = _get_redis()
        if r is not None:
            key = f"unknown_phone_attempt:{phone}"
            if r.exists(key):
                return
            r.set(key, "1", ex=int(os.getenv("UNKNOWN_PHONE_TTL", "300")))
    except Exception:
        pass

    text = (
        "Noma'lum telefon raqami bilan tizimga kirish urinish aniqlandi.\n"
        f"Telefon: {phone}\n"
        "Agar bu foydalanuvchi tizimga qo'shilishi kerak bo'lsa, iltimos admin paneldan yaratib bering."
    )
    send_telegram_alert_task.delay(text)
