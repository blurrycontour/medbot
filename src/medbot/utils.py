import logging
import sys
from typing import Optional


def setup_logging(log_level=logging.INFO, log_file: Optional[str] = None):
    """Configure logging for the entire package."""
    # Create a root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Prevent adding handlers multiple times if called again
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Log to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Optional log to file
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
