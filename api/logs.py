import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class Log:
    BASE_DIR = Path("logs")

    @staticmethod
    def get(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if logger.handlers:
            return logger

        log_dir = Log.BASE_DIR / name
        log_dir.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # --- INFO / WARNING ---
        info_handler = TimedRotatingFileHandler(
            log_dir / "info.log",
            when="midnight",
            interval=1,
            backupCount=14,
            encoding="utf-8"
        )
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)

        # --- ERROR / CRITICAL ---
        error_handler = TimedRotatingFileHandler(
            log_dir / "error.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # --- CONSOLE ---
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(info_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

        return logger