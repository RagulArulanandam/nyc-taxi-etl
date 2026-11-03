"""
src/extract/logger.py

Every module does:

    from src.extract.logger import setup_logger
    log = setup_logger(__name__)

Handlers (console + rotating file) are attached once to the root logger, so
every module logs to the same place without duplicate output or several
handlers fighting over the same rotating file.
"""

import logging
from logging.handlers import RotatingFileHandler

from src.extract.config import LOG_FILE

_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"


def setup_logger(name: str = "extract") -> logging.Logger:
    """Return a named logger; configures the root handlers on first call."""
    root = logging.getLogger()
    if not root.handlers:
        root.setLevel(logging.INFO)
        fmt = logging.Formatter(_FORMAT)

        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)

        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
        fh.setFormatter(fmt)
        root.addHandler(fh)

    return logging.getLogger(name)
