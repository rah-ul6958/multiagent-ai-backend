import logging
import sys

from pythonjsonlogger import jsonlogger

logger = logging.getLogger()

logger.setLevel(logging.INFO)

stream = logging.StreamHandler(sys.stdout)

formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s"
)

stream.setFormatter(formatter)

logger.addHandler(stream)