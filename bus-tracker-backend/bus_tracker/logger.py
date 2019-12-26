import logging
from typing import Optional

DEFAULT_APP_LOGGER = "bus-tracker"


def set_logger(verbose: int, name: str = DEFAULT_APP_LOGGER) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    if verbose > 1:
        level = logging.DEBUG

    logger = logging.getLogger(name)
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def get_logger(suffix: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(DEFAULT_APP_LOGGER)
    if suffix is None:
        return logger
    return logger.getChild(suffix)
