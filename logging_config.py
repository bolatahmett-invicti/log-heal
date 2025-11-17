"""
Logging Configuration
Provides structured logging with rotation and error tracking
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

from config import get_config


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging():
    """Setup application logging"""
    config = get_config()
    
    # Create logs directory
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    log_level = getattr(logging, config.app_log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    if config.app_debug:
        console_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = logs_dir / f"logheal-{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=7
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(console_formatter)
    root_logger.addHandler(file_handler)
    
    # JSON file handler for structured logging
    json_log_file = logs_dir / f"logheal-json-{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    json_handler = logging.handlers.RotatingFileHandler(
        json_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=7
    )
    json_handler.setLevel(logging.WARNING)  # Only log warnings and errors as JSON
    json_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(json_handler)
    
    return root_logger


# Initialize logging
logger = setup_logging()


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get logger for module"""
    return logging.LoggerAdapter(
        logging.getLogger(name),
        extra={'extra_fields': {}}
    )


class LogContext:
    """Context manager for adding extra fields to logs"""
    
    def __init__(self, logger: logging.LoggerAdapter, **fields):
        self.logger = logger
        self.fields = fields
    
    def __enter__(self):
        if hasattr(self.logger.logger, 'extra_fields'):
            self.logger.logger.extra_fields.update(self.fields)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.logger.logger, 'extra_fields'):
            for key in self.fields:
                self.logger.logger.extra_fields.pop(key, None)
