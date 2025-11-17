"""
Test Configuration
Provides test fixtures and configuration
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from utils import SimpleCache, RateLimiter, CircuitBreaker
from exceptions import ValidationError


@pytest.fixture
def config():
    """Provide test configuration"""
    return Config()


@pytest.fixture
def cache():
    """Provide test cache"""
    return SimpleCache(ttl_seconds=1)


@pytest.fixture
def rate_limiter():
    """Provide test rate limiter"""
    return RateLimiter(max_calls=3, period_seconds=1)


@pytest.fixture
def circuit_breaker():
    """Provide test circuit breaker"""
    return CircuitBreaker(failure_threshold=2, recovery_timeout=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
