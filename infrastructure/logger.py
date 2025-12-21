"""Logging system for YouTube Monitor & Translator."""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    log_dir: str = "logs",
    debug: bool = False,
    log_file: bool = True,
) -> logging.Logger:
    """
    Set up logger with both file and console handlers.

    Args:
        name: Logger name (defaults to root logger if None)
        log_dir: Directory for log files
        debug: Enable debug level logging
        log_file: Write logs to file

    Returns:
        Configured logger instance
    """
    # Determine log level
    level = logging.DEBUG if debug else logging.INFO

    # Create logs directory if needed
    if log_file and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Define log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if enabled)
    if log_file:
        log_file_path = os.path.join(
            log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def configure_root_logger(
    debug: bool = False, log_dir: str = "logs", log_file: bool = True
) -> None:
    """
    Configure root logger for the entire application.

    Args:
        debug: Enable debug level logging
        log_dir: Directory for log files
        log_file: Write logs to file
    """
    setup_logger(name=None, log_dir=log_dir, debug=debug, log_file=log_file)
    logging.debug("Root logger configured")
