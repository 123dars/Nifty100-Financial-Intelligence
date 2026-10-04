import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def _configure() -> None:
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())

    formatter = logging.Formatter(_LOG_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            _LOG_DIR / "app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # Ignore file logging failures (e.g. read-only filesystem).
        pass

    # Silence noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(name)


def get_log_dir() -> Path:
    return _LOG_DIR