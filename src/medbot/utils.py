import logging
import sys
from typing import Optional


class LoggerNameFilter(logging.Filter):
    """Allow records only from specified logger name prefixes."""
    def __init__(self, allowed_prefixes: Optional[list[str]] = None):
        super().__init__()
        self.allowed = tuple(allowed_prefixes or ())

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.allowed:
            return True
        # allow if record.name starts with any configured prefix
        return not record.name.startswith(self.allowed)


def setup_logging(
    log_level=logging.INFO,
    log_file: Optional[str] = None,
    file_logger_names: Optional[list[str]] = None
):
    """Configure logging for the entire package.
    If file_logger_names is provided, only loggers whose name starts with
    one of those prefixes will be written to the file.
    """
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

    # log filter
    logger_filter = LoggerNameFilter(file_logger_names)

    # Log to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(logger_filter)
    logger.addHandler(stream_handler)

    # Optional log to file
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(logger_filter)
        logger.addHandler(file_handler)

    return logger
