import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Lambda already configures the root handler; only the level is set."""
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    return logger
