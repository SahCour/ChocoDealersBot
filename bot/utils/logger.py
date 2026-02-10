"""
Logging configuration using Loguru
"""

from loguru import logger
import sys
from pathlib import Path


def setup_logger(log_level: str = "INFO", log_file: str = "./logs/chocodealers_bot.log"):
    """
    Setup loguru logger with file and console outputs

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
    """
    # Remove default handler
    logger.remove()

    # Add console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # Add file handler with rotation
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="1 month",
        compression="zip"
    )

    logger.info(f"Logger initialized. Level: {log_level}, File: {log_file}")
