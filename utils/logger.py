import logging
from settings import settings


def setup_logger():
    logger = logging.getLogger(settings.logger_name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(fmt))

    logger.addHandler(handler)
