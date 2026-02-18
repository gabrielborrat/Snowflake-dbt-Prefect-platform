"""
Logging Configuration
---------------------
Structured logging setup using loguru.
Used across all ingestion scripts and orchestration flows.
"""

import sys
from loguru import logger
from ingestion.config import LOG_LEVEL


def setup_logger(module_name: str = "ingestion") -> logger:
    """
    Configure and return a loguru logger instance.

    Args:
        module_name: Name of the module for log identification.

    Returns:
        Configured loguru logger.
    """
    # Remove default handler
    logger.remove()

    # Console handler — structured, colored output
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[module]}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Bind module name to all log messages
    bound_logger = logger.bind(module=module_name)

    return bound_logger
