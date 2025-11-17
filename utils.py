"""
Utilities Module
Provides caching, rate limiting, retry logic, and input validation
"""

import functools
import time
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
import re
from logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter implementation"""
    
    def __init__(self, max_calls: int, period_seconds: int):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.calls: Dict[str, list] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if call is allowed"""
        now = time.time()
        
        if key not in self.calls:
            self.calls[key] = []
        
        # Remove old calls outside the period
        self.calls[key] = [
            call_time for call_time in self.calls[key]
            if now - call_time < self.period_seconds
        ]
        
        # Check if limit exceeded
        if len(self.calls[key]) >= self.max_calls:
            return False
        
        # Record this call
        self.calls[key].append(now)
        return True
    
    def wait_if_needed(self, key: str):
        """Wait if rate limit is reached"""
        while not self.is_allowed(key):
            time.sleep(0.1)


class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        value, expiry = self.cache[key]
        if time.time() > expiry:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache"""
        ttl = ttl_seconds or self.ttl_seconds
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if now > expiry
        ]
        for key in expired_keys:
            del self.cache[key]


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}. "
                            f"Retrying in {wait_time:.1f}s. Error: {str(e)}"
                        )
                        time.sleep(wait_time)
            
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    if not isinstance(value, str):
        return ""
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename"""
    # Remove path separators and special characters
    filename = filename.replace('/', '_').replace('\\', '_')
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    # Keep only alphanumeric, dash, underscore, dot
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    return filename or 'file'


def validate_json_input(data: Any, max_size: int = 10 * 1024 * 1024) -> bool:
    """Validate JSON input size"""
    try:
        import json
        json_str = json.dumps(data)
        return len(json_str.encode('utf-8')) <= max_size
    except Exception:
        return False


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception(
                    f"Circuit breaker is open. "
                    f"Retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt to reset"""
        if self.last_failure_time is None:
            return False
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout


# Global instances
_cache_instances: Dict[str, SimpleCache] = {}


def get_cache(name: str = 'default', ttl_seconds: int = 3600) -> SimpleCache:
    """Get or create cache instance"""
    if name not in _cache_instances:
        _cache_instances[name] = SimpleCache(ttl_seconds)
    return _cache_instances[name]
