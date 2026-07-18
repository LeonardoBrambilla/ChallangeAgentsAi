import json
import logging
import time
from typing import Any, Callable


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": round(record.created, 3),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_fields"):
            payload.update(record.extra_fields)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("assistant")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, message: str, **fields: Any) -> None:
    logger.info(message, extra={"extra_fields": fields})


def timed(logger: logging.Logger, event: str) -> Callable:
    """Decorator that logs start/end/duration of a tool or node call as structured JSON."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            log_event(logger, f"{event}.start")
            try:
                result = func(*args, **kwargs)
                log_event(logger, f"{event}.end", duration_ms=round((time.monotonic() - start) * 1000, 1))
                return result
            except Exception as exc:
                log_event(logger, f"{event}.error", error=str(exc))
                raise

        return wrapper

    return decorator
