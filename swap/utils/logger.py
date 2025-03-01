import sys
from loguru import logger
from typing import Optional
from swap.config import settings


class CustomLogger:
    @staticmethod
    def setup_logger(
        log_level: str = settings.system.log_level, log_file: Optional[str] = None
    ) -> None:
        logger.remove()  # Remove default logger
        logger.add(sys.stderr, level=log_level)
        if log_file:
            logger.add(log_file, level=log_level, rotation="10 MB")

    @staticmethod
    def get_logger():
        return logger


logger = CustomLogger.get_logger()
