"""
Structured Logging Configuration
Provides JSON-formatted logging for better monitoring and analysis
"""
import logging
import sys
import os
from pythonjsonlogger import jsonlogger


def setup_logging():
    """Configure structured logging with JSON format"""
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'
    
    logger = logging.getLogger('recipe_recommender')
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers (close them first to avoid resource leaks)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    if log_format == 'json':
        # JSON formatter for production
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    else:
        # Text formatter for development
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for errors
    error_file = os.getenv('ERROR_LOG_FILE', 'logs/errors.log')
    if error_file:
        os.makedirs(os.path.dirname(error_file), exist_ok=True)
        file_handler = logging.FileHandler(error_file)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create global logger instance
logger = setup_logging()
