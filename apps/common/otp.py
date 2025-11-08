from __future__ import annotations

import logging
import random
from typing import Optional
import threading
import time

from django.conf import settings
from .redis_client import get_redis

logger = logging.getLogger("apps.auth")


class _MemoryStore:
    """Lightweight in-memory store with TTL for dev fallback when Redis is unavailable.

    NOTE: This is per-process and not suitable for multi-worker production, but fine for local/dev.
    """

    def __init__(self):
        self._data: dict[str, tuple[str | int, float | None]] = {}
        self._lock = threading.Lock()

    def _purge(self, key: str):
        val = self._data.get(key)
        if not val:
            return
        _, expires_at = val
        if expires_at is not None and time.time() >= expires_at:
            self._data.pop(key, None)

    def setex(self, key: str, ttl_seconds: int, value: str | int):
        with self._lock:
            self._data[key] = (value, time.time() + ttl_seconds)

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            self._purge(key)
            val = self._data.get(key)
            return None if val is None else str(val[0])

    def exists(self, key: str) -> bool:
        with self._lock:
            self._purge(key)
            return key in self._data

    def ttl(self, key: str) -> int:
        with self._lock:
            self._purge(key)
            val = self._data.get(key)
            if not val:
                return -2  # Redis semantics: key does not exist
            _, expires_at = val
            if expires_at is None:
                return -1
            return max(0, int(expires_at - time.time()))

    def delete(self, key: str):
        with self._lock:
            self._data.pop(key, None)

    def incr(self, key: str) -> int:
        with self._lock:
            self._purge(key)
            val = self._data.get(key)
            if val is None:
                self._data[key] = (1, None)
                return 1
            current, expires_at = val
            current_int = int(current) + 1
            self._data[key] = (current_int, expires_at)
            return current_int

    def expire(self, key: str, ttl_seconds: int):
        with self._lock:
            val = self._data.get(key)
            if val is None:
                return
            v, _ = val
            self._data[key] = (v, time.time() + ttl_seconds)


_memory_store = _MemoryStore()


def _get_store():
    """Get Redis client if available; otherwise use in-memory fallback."""
    try:
        r = get_redis()
        # Ensure connection works; if not, fall back
        try:
            r.ping()
            return r
        except Exception:
            logger.warning("Redis unavailable, using in-memory OTP store")
            return _memory_store
    except Exception:
        logger.warning("Redis init failed, using in-memory OTP store")
        return _memory_store


def _key_for_code(phone: str, purpose: str = "generic") -> str:
    return f"{settings.OTP_REDIS_PREFIX}:{purpose}:code:{phone}"


def _key_for_cooldown(phone: str, purpose: str = "generic") -> str:
    return f"{settings.OTP_REDIS_PREFIX}:{purpose}:cooldown:{phone}"


def _key_for_attempts(phone: str, purpose: str = "generic") -> str:
    return f"{settings.OTP_REDIS_PREFIX}:{purpose}:attempts:{phone}"


def _mask_phone(phone: str) -> str:
    p = phone.strip()
    if len(p) <= 4:
        return "*" * len(p)
    return p[:2] + "*" * max(0, len(p) - 5) + p[-3:]


class OTPError(Exception):
    pass


class OTPService:
    """Redis-backed OTP service with cooldown and attempt limits."""

    @staticmethod
    def generate_code(length: int | None = None) -> str:
        length = length or settings.OTP_CODE_LENGTH
        start = 10 ** (length - 1)
        end = (10 ** length) - 1
        return str(random.randint(start, end))

    @classmethod
    def request_code(cls, phone: str, *, purpose: str = "generic") -> dict:
        r = _get_store()
        cooldown_key = _key_for_cooldown(phone, purpose)
        if r.exists(cooldown_key):
            ttl = r.ttl(cooldown_key)
            raise OTPError(f"Too many requests. Try again in {ttl if ttl else 'a few'} seconds.")

        code = cls.generate_code()
        code_key = _key_for_code(phone, purpose)
        r.setex(code_key, settings.OTP_CODE_TTL_SECONDS, code)
        # set request cooldown to avoid spamming
        r.setex(cooldown_key, settings.OTP_REQUEST_COOLDOWN_SECONDS, 1)
        # reset attempts for fresh code
        r.delete(_key_for_attempts(phone, purpose))

        # Enqueue SMS send via Celery
        try:
            from .tasks_otp import send_sms_otp_task
            send_sms_otp_task.delay(phone, code)
        except Exception:
            logger.exception("Failed to enqueue OTP send task")

        logger.info(
            "OTP requested",
            extra={
                "phone_masked": _mask_phone(phone),
                "ttl": settings.OTP_CODE_TTL_SECONDS,
                "purpose": purpose,
            },
        )
        return {"sent": True, "phone_masked": _mask_phone(phone), "expires_in": settings.OTP_CODE_TTL_SECONDS, "purpose": purpose}

    @classmethod
    def verify_code(cls, phone: str, code: str, *, purpose: str = "generic") -> bool:
        r = _get_store()
        attempts_key = _key_for_attempts(phone, purpose)
        code_key = _key_for_code(phone, purpose)

        stored: Optional[str] = r.get(code_key)
        if not stored:
            logger.warning("OTP verify failed: no code", extra={"phone_masked": _mask_phone(phone), "purpose": purpose})
            return False

        if stored != str(code).strip():
            # increment attempts and optionally lockout
            attempts = r.incr(attempts_key)
            max_attempts = settings.OTP_MAX_ATTEMPTS
            if attempts == 1:
                # align attempts ttl with code ttl
                ttl = r.ttl(code_key)
                if ttl and ttl > 0:
                    r.expire(attempts_key, ttl)
            logger.warning(
                "OTP verify failed: wrong code",
                extra={
                    "phone_masked": _mask_phone(phone),
                    "attempts": attempts,
                    "max_attempts": max_attempts,
                    "purpose": purpose,
                },
            )
            if attempts >= max_attempts:
                # Invalidate the code to force re-request
                r.delete(code_key)
            return False

        # success: cleanup keys
        r.delete(code_key)
        r.delete(attempts_key)
        logger.info("OTP verify success", extra={"phone_masked": _mask_phone(phone), "purpose": purpose})
        return True
