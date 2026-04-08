import logging
import logging.handlers
from pathlib import Path

from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    settings = get_settings()

    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("TutorRAG")

    log_level_name = str(settings.LOG_LEVEL).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(log_level)
    logger.propagate = False

    # Prevent duplicate handlers on repeated imports
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        # If file logging fails, keep console logging so the app can still run
        pass

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Logging initialized successfully.")
    return logger


logger = setup_logging()