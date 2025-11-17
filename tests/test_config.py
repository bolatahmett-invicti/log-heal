"""
Tests for configuration module
"""

import os
import pytest
from config import Config, ConfigError


class TestConfig:
    """Test Config functionality"""
    
    def test_config_get_string(self, config):
        """Test getting string config"""
        result = config.get_string("NONEXISTENT", "default_value")
        assert result == "default_value"
    
    def test_config_get_int(self, config):
        """Test getting integer config"""
        os.environ["TEST_INT"] = "42"
        result = config.get_int("TEST_INT")
        assert result == 42
    
    def test_config_get_bool(self, config):
        """Test getting boolean config"""
        os.environ["TEST_BOOL"] = "true"
        result = config.get_bool("TEST_BOOL")
        assert result is True
    
    def test_config_required_missing(self, config):
        """Test required config raises error"""
        with pytest.raises(ConfigError):
            config.get("MISSING_REQUIRED", required=True)
    
    def test_config_invalid_int(self, config):
        """Test invalid integer raises error"""
        os.environ["INVALID_INT"] = "not_an_int"
        with pytest.raises(ConfigError):
            config.get_int("INVALID_INT")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
