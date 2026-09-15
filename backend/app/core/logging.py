import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Simple structured log formatter for development and production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return f"[{log_data['timestamp']}] [{log_data['level']}] {log_data['name']}: {log_data['message']}"


def setup_logging(debug: bool = True) -> logging.Logger:
    """Configure system-wide logging with structured output."""
    log_level = logging.DEBUG if debug else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicate lines
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(console_handler)

    # Suppress excessive verbosity from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("rasterio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logging.getLogger("sih1518")


logger = setup_logging()
