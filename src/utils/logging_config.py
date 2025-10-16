"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger as loguru_logger


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """Setup application logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
    """
    # Remove default loguru handler
    loguru_logger.remove()
    
    # Console logging
    if enable_console:
        loguru_logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            colorize=True
        )
    
    # File logging
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )
    
    # Configure standard logging to work with loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = loguru_logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            loguru_logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set specific loggers
    for logger_name in ["requests", "urllib3", "httpx"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    loguru_logger.info(f"Logging configured - Level: {log_level}, File: {log_file or 'None'}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
