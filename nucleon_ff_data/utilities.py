"""Utility routines for nucleon_ff_data module
"""
import logging


def set_up_logger(name: str) -> logging.Logger:
    """Sets up command line logger

    Loggers default level is WARNING. Only contains stdout logger.

    **Arguments**
        name: str
            Name of the logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    formatter = logging.Formatter("[%(asctime)s|%(name)s@%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
