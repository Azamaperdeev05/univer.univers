import logging
import sys


def createLogger(name, level=logging.INFO, *, format: str):
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


def getDefaultLogger(name, level=logging.INFO):
    return createLogger(
        name, level, format="[%(asctime)s] %(name)s | %(levelname)s | %(message)s"
    )
