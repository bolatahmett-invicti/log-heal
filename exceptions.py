"""
Exception Handling
Custom exceptions and error handling utilities
"""

from typing import Optional
from logging_config import get_logger

logger = get_logger(__name__)


class LogHealException(Exception):
    """Base exception for LogHeal"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ConfigurationError(LogHealException):
    """Configuration error"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class ELKConnectionError(LogHealException):
    """ELK connection error"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "ELK_CONNECTION_ERROR", details)


class APIError(LogHealException):
    """API call error"""
    def __init__(self, message: str, status_code: int = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if status_code:
            details['status_code'] = status_code
        super().__init__(message, "API_ERROR", details)


class RateLimitError(LogHealException):
    """Rate limit exceeded error"""
    def __init__(self, message: str, retry_after: int = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class ValidationError(LogHealException):
    """Input validation error"""
    def __init__(self, message: str, field: str = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if field:
            details['field'] = field
        super().__init__(message, "VALIDATION_ERROR", details)


class TimeoutError(LogHealException):
    """Operation timeout error"""
    def __init__(self, message: str, timeout_seconds: int = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if timeout_seconds:
            details['timeout_seconds'] = timeout_seconds
        super().__init__(message, "TIMEOUT_ERROR", details)


class ProcessingError(LogHealException):
    """Processing error"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "PROCESSING_ERROR", details)


def handle_exception(exc: Exception, context: str = ""):
    """Handle exception with logging"""
    if isinstance(exc, LogHealException):
        logger.error(f"[{exc.error_code}] {context}: {exc.message}", exc_info=True)
        return exc.to_dict()
    else:
        logger.error(f"Unexpected error in {context}: {str(exc)}", exc_info=True)
        return {
            'error': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'details': {'context': context} if context else {}
        }
