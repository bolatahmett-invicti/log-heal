#!/usr/bin/env python3
"""
Health Check Script
Verifies all components are working correctly
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, ConfigError
from logging_config import get_logger
from elk_connector import create_elk_connector
from utils import SimpleCache, RateLimiter, CircuitBreaker

logger = get_logger(__name__)


def check_config():
    """Check configuration is valid"""
    try:
        config = get_config()
        
        # Test required fields
        _ = config.openai_api_key
        _ = config.app_env
        _ = config.app_log_level
        
        logger.info("✓ Configuration check passed")
        return True
    except ConfigError as e:
        logger.error(f"✗ Configuration check failed: {e}")
        return False


def check_logging():
    """Check logging setup"""
    try:
        test_logger = get_logger("test")
        test_logger.info("✓ Logging check passed")
        return True
    except Exception as e:
        print(f"✗ Logging check failed: {e}")
        return False


def check_elk_connection():
    """Check ELK connection"""
    try:
        config = get_config()
        elk = create_elk_connector(
            use_mock=config.elk_use_mock,
            host=config.elk_host,
            port=config.elk_port,
            username=config.elk_username,
            password=config.elk_password
        )
        
        if elk.connect():
            logger.info("✓ ELK connection check passed")
            return True
        else:
            if config.elk_use_mock:
                logger.info("⚠ ELK connection check: using mock mode")
                return True
            else:
                logger.warning("✗ ELK connection check failed")
                return False
    except Exception as e:
        logger.error(f"✗ ELK connection check failed: {e}")
        return False


def check_caching():
    """Check caching system"""
    try:
        cache = SimpleCache(ttl_seconds=60)
        
        # Test set/get
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        
        if value == "test_value":
            logger.info("✓ Caching check passed")
            return True
        else:
            logger.error("✗ Caching check failed: value mismatch")
            return False
    except Exception as e:
        logger.error(f"✗ Caching check failed: {e}")
        return False


def check_rate_limiting():
    """Check rate limiting"""
    try:
        limiter = RateLimiter(max_calls=3, period_seconds=60)
        
        # Test rate limit
        results = []
        for i in range(5):
            results.append(limiter.is_allowed("test_client"))
        
        # Should be [T, T, T, F, F]
        if results == [True, True, True, False, False]:
            logger.info("✓ Rate limiting check passed")
            return True
        else:
            logger.error(f"✗ Rate limiting check failed: {results}")
            return False
    except Exception as e:
        logger.error(f"✗ Rate limiting check failed: {e}")
        return False


def check_circuit_breaker():
    """Check circuit breaker"""
    try:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def failing_func():
            raise Exception("Test error")
        
        # Should fail twice then open
        failures = 0
        for i in range(3):
            try:
                cb.call(failing_func)
            except Exception as e:
                if "Circuit breaker is open" in str(e):
                    break
                failures += 1
        
        if cb.state == "open":
            logger.info("✓ Circuit breaker check passed")
            return True
        else:
            logger.error("✗ Circuit breaker check failed")
            return False
    except Exception as e:
        logger.error(f"✗ Circuit breaker check failed: {e}")
        return False


def main():
    """Run all health checks"""
    logger.info("=" * 60)
    logger.info("LogHeal Health Check")
    logger.info("=" * 60)
    
    checks = [
        ("Configuration", check_config),
        ("Logging", check_logging),
        ("ELK Connection", check_elk_connection),
        ("Caching", check_caching),
        ("Rate Limiting", check_rate_limiting),
        ("Circuit Breaker", check_circuit_breaker),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"✗ {name} check error: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    logger.info(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("✓ All health checks passed")
        return 0
    else:
        logger.error("✗ Some health checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
