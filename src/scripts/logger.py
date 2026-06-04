"""
Logging standardisé pour le projet
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, DEBUG

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, level: str = LOG_LEVEL) -> logging.Logger:
    """
    Setup logger avec console et file handlers
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console Handler (always INFO or higher)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (DEBUG and above)
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create logger for module"""
    return logging.getLogger(name)


# ============================================
# Module-level logger
# ============================================

logger = setup_logger(__name__)

if DEBUG:
    logger.info("🔧 DEBUG MODE ENABLED")
else:
    logger.info("✅ PRODUCTION MODE")

logger.info(f"📝 Logs saved to: {LOG_FILE}")
