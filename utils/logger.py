import logging
import sys
from typing import Callable

LoggerCreator = Callable[[str], logging.Logger]


def create_logger(name, level=logging.INFO, *, format: str):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if len(logger.handlers) > 0:
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_default_logger(name, level=logging.INFO):
    return create_logger(
        name, level, format="[%(asctime)s] %(name)s | %(levelname)s | %(message)s"
    )
