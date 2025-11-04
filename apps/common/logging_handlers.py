import logging
import os
import traceback
from typing import Iterable, Optional

from apps.common.tasks_alerts import send_telegram_alert_task


class ProductionErrorFilter(logging.Filter):
    """Filter to reduce noise: allow only ERROR+ and ignore common benign cases.

    - Pass only if level >= ERROR
    - If record has `status` and it's < 500, drop it
    - Ignore asyncio.CancelledError and DisallowedHost
    """

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if record.levelno < logging.ERROR:
            return False

        status = getattr(record, "status", None)
        if isinstance(status, int) and status < 500:
            return False

        msg = str(getattr(record, "msg", ""))
        if "Not Found" in msg or "404" in msg:
            # typical benign 404s
            return False

        exc = None
        if record.exc_info:
            exc = record.exc_info[1]
        if exc is not None:
            if exc.__class__.__name__ in {"CancelledError", "DisallowedHost"}:
                return False

        return True


class TelegramAdminHandler(logging.Handler):
    """Logging handler that sends ERROR+ records to Telegram admins.

    It uses bot.data.config (BOT_TOKEN, ADMINS). If not available or disabled
    via ERROR_ALERTS_ENABLED, it silently does nothing.
    """

    def __init__(self):
        super().__init__()
        self.enabled = os.getenv("ERROR_ALERTS_ENABLED", "true").lower() in {"1", "true", "yes"}
        self.disabled = False
        admins = os.getenv("ADMINS", "").split(",")
        self.admin_ids = [a for a in (admins or []) if str(a).strip()]
        if not self.admin_ids or not self.enabled:
            # disable handler if not configured
            self.disabled = True

    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        if self.disabled:
            return
        try:
            text = self._format_text(record)
            # enqueue a single task that will send to all admins and chunk as needed
            send_telegram_alert_task.apply_async(kwargs={"text": text, "chat_ids": self.admin_ids})
        except Exception:  # pragma: no cover - best-effort
            # We should never raise from logging
            pass

    def _format_text(self, record: logging.LogRecord) -> str:
        title = f"[{record.levelname}] {record.name}"
        method = getattr(record, "method", "")
        path = getattr(record, "path", "")
        status = getattr(record, "status", "")
        ms = getattr(record, "ms", "")
        user_id = getattr(record, "user_id", "")
        ip = getattr(record, "ip", "")
        base_msg = str(record.getMessage())

        lines = [
            title,
            f"method={method} path={path} status={status} ms={ms} user_id={user_id} ip={ip}",
            "",
        ]

        if record.exc_info:
            tb = "".join(traceback.format_exception(*record.exc_info))
            lines.append("Traceback:\n" + tb)
        else:
            lines.append(base_msg)

        return "\n".join(lines)

    # sending is done in celery task
