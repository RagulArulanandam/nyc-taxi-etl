"""
src/extract/logger.py
 
Call setup_logger() once at startup. Every other module does:
 
    from src.extract.logger import setup_logger
    log = setup_logger(__name__)
 
This gives each module its own named logger that inherits the same
handlers and level — console + rotating file, no duplicate output.
"""

import logging
from logging.handlers import RotatingFileHandler
from src.extract.config import LOG_FILE


def setup_logger(name: str = "extract") -> logging.Logger:
    """
    Return a logger with console + rotating-file handlers.
    Safe to call multiple times — handlers are only added once.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger