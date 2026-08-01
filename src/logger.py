import logging
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR,"app.log")

os.makedirs(LOG_DIR,exist_ok=True)

logger = logging.getLogger("Chemical_equipment")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

# prevent duplicate logs
if not logger.handlers:

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)