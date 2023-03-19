import logging
import os

_logger = logging.getLogger(__name__)


def get_var(keyname: str):
    value = os.getenv(keyname, None)
    if not value:
        raise ValueError(keyname)
    return value
