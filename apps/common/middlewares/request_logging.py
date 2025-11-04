import asyncio
import logging
import time
from typing import Callable, Optional
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("django.request")


class RequestLoggingMiddleware:
    """Logs each request/response with latency and minimal context.

    Fields: method, path, status, ms, user_id, ip, ua
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        response: Optional[HttpResponse] = None
        exc: Optional[BaseException] = None
        try:
            response = self.get_response(request)
            return response
        except asyncio.CancelledError as e:
            # Client disconnected / ASGI cancellation. Log as info and re-raise.
            exc = e
            raise
        except Exception as e:  # noqa: BLE001 - we want to log any exception
            exc = e
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            user_id = getattr(getattr(request, "user", None), "id", None)
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
            ua = request.META.get("HTTP_USER_AGENT", "")
            status_code = getattr(response, "status_code", 0)
            level = logger.error if exc else logger.info
            # Human-readable message (works for text formatters), while extra fields
            # are included for JSON formatters.
            msg = (
                f"method={getattr(request, 'method', '')} "
                f"path={getattr(request, 'get_full_path', lambda: '')()} "
                f"status={status_code} ms={duration_ms} "
                f"user_id={user_id} ip={ip}"
            )
            level(
                msg,
                extra={
                    "method": getattr(request, "method", ""),
                    "path": getattr(request, "get_full_path", lambda: "")(),
                    "status": status_code,
                    "ms": duration_ms,
                    "user_id": user_id,
                    "ip": ip,
                    "ua": ua[:200],  # avoid very long UA
                    "exc_type": exc.__class__.__name__ if exc else None,
                },
            )
