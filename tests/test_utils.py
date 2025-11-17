"""
Tests for utils module
"""

import pytest
import time
from utils import (
    SimpleCache, RateLimiter, CircuitBreaker,
    validate_email, validate_url, sanitize_string,
    sanitize_filename, retry
)


class TestSimpleCache:
    """Test SimpleCache functionality"""
    
    def test_cache_set_get(self, cache):
        """Test basic cache operations"""
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'
    
    def test_cache_expiry(self, cache):
        """Test cache expiration"""
        cache.set('key1', 'value1', ttl_seconds=0.1)
        assert cache.get('key1') == 'value1'
        time.sleep(0.2)
        assert cache.get('key1') is None
    
    def test_cache_clear(self, cache):
        """Test cache clearing"""
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        assert cache.get('key1') is None
        assert cache.get('key2') is None


class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    def test_rate_limit_allowed(self, rate_limiter):
        """Test rate limit allows calls within limit"""
        assert rate_limiter.is_allowed('client1')
        assert rate_limiter.is_allowed('client1')
        assert rate_limiter.is_allowed('client1')
    
    def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit blocks calls"""
        assert rate_limiter.is_allowed('client1')
        assert rate_limiter.is_allowed('client1')
        assert rate_limiter.is_allowed('client1')
        assert not rate_limiter.is_allowed('client1')
    
    def test_rate_limit_reset(self, rate_limiter):
        """Test rate limit resets after period"""
        assert rate_limiter.is_allowed('client1')
        assert rate_limiter.is_allowed('client1')
        assert rate_limiter.is_allowed('client1')
        assert not rate_limiter.is_allowed('client1')
        
        time.sleep(1.1)
        assert rate_limiter.is_allowed('client1')


class TestCircuitBreaker:
    """Test CircuitBreaker functionality"""
    
    def test_circuit_breaker_open(self, circuit_breaker):
        """Test circuit breaker opens on failures"""
        def failing_func():
            raise Exception("Test error")
        
        # First two failures
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        
        # Third attempt should fail with circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is open"):
            circuit_breaker.call(failing_func)
    
    def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery"""
        def failing_func():
            raise Exception("Test error")
        
        # Open the circuit
        circuit_breaker.failure_threshold = 1
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == 'open'
        
        # Wait for recovery window
        circuit_breaker.recovery_timeout = 0
        
        def success_func():
            return "success"
        
        # Should recover after timeout
        result = circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == 'closed'


class TestValidation:
    """Test validation functions"""
    
    def test_validate_email_valid(self):
        """Test valid email validation"""
        assert validate_email("user@example.com")
        assert validate_email("test.user+tag@domain.co.uk")
    
    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        assert not validate_email("invalid-email")
        assert not validate_email("@example.com")
        assert not validate_email("user@")
    
    def test_validate_url_valid(self):
        """Test valid URL validation"""
        assert validate_url("https://example.com")
        assert validate_url("http://subdomain.example.com/path")
    
    def test_validate_url_invalid(self):
        """Test invalid URL validation"""
        assert not validate_url("not a url")
        assert not validate_url("example.com")


class TestSanitization:
    """Test sanitization functions"""
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        assert sanitize_string("  test  ") == "test"
        assert sanitize_string("test\x00string") == "teststring"
    
    def test_sanitize_string_max_length(self):
        """Test string max length"""
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        assert sanitize_filename("normal-file.txt") == "normal-file.txt"
        assert sanitize_filename("../../../etc/passwd") == "........etcpasswd"
        assert sanitize_filename("<script>alert('xss')</script>") == "scriptalertxssscript"


class TestRetry:
    """Test retry decorator"""
    
    def test_retry_success_first_attempt(self):
        """Test retry on first attempt"""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def succeeds():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = succeeds()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Test retry succeeds after failures"""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Failure")
            return "success"
        
        result = fails_twice()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_all_failures(self):
        """Test retry fails after all attempts"""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")
        
        with pytest.raises(Exception):
            always_fails()
        
        assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
