import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "livetranslate.log"


def setup_logger(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=2 * 1024 * 1024,  # 2 MB
            backupCount=3,
            encoding="utf-8",
        ),
    ]
    logging.basicConfig(level=level, format=fmt, handlers=handlers)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
