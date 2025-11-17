"""
Configuration Management
Handles environment variables and application settings
"""

import os
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration error"""
    pass


class Config:
    """Application configuration"""
    
    def __init__(self):
        self._load_env()
    
    def _load_env(self):
        """Load environment variables"""
        from dotenv import load_dotenv
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
        else:
            logger.warning(f".env file not found at {env_file}")
    
    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """Get configuration value"""
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ConfigError(f"Required configuration '{key}' not found")
        
        # Type conversions
        if value is not None:
            if isinstance(default, bool):
                return value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(default, int):
                try:
                    return int(value)
                except ValueError:
                    raise ConfigError(f"Configuration '{key}' must be an integer, got '{value}'")
        
        return value
    
    def get_int(self, key: str, default: int = 0, required: bool = False) -> int:
        """Get integer configuration"""
        value = self.get(key, required=required)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            raise ConfigError(f"Configuration '{key}' must be an integer, got '{value}'")
    
    def get_bool(self, key: str, default: bool = False, required: bool = False) -> bool:
        """Get boolean configuration"""
        value = self.get(key, required=required)
        if value is None:
            return default
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def get_string(self, key: str, default: str = "", required: bool = False) -> str:
        """Get string configuration"""
        value = self.get(key, required=required)
        return value if value is not None else default
    
    # OpenAI Configuration
    @property
    def openai_api_key(self) -> str:
        return self.get_string("OPENAI_API_KEY", required=True)
    
    @property
    def openai_model(self) -> str:
        return self.get_string("OPENAI_MODEL", "gpt-4o")
    
    # Elasticsearch Configuration
    @property
    def elk_host(self) -> str:
        return self.get_string("ELK_HOST", "localhost")
    
    @property
    def elk_port(self) -> int:
        return self.get_int("ELK_PORT", 9200)
    
    @property
    def elk_username(self) -> Optional[str]:
        return self.get_string("ELK_USERNAME") or None
    
    @property
    def elk_password(self) -> Optional[str]:
        return self.get_string("ELK_PASSWORD") or None
    
    @property
    def elk_use_mock(self) -> bool:
        return self.get_bool("ELK_USE_MOCK", False)
    
    @property
    def elk_index_pattern(self) -> str:
        return self.get_string("ELK_INDEX_PATTERN", "logs-*")
    
    @property
    def elk_time_range_minutes(self) -> int:
        return self.get_int("ELK_TIME_RANGE_MINUTES", 180)
    
    # Git Configuration
    @property
    def git_repo_path(self) -> str:
        return self.get_string("GIT_REPO_PATH", ".")
    
    @property
    def git_default_branch(self) -> str:
        return self.get_string("GIT_DEFAULT_BRANCH", "main")
    
    @property
    def git_branch_prefix(self) -> str:
        return self.get_string("GIT_BRANCH_PREFIX", "fix/")
    
    @property
    def git_author_name(self) -> str:
        return self.get_string("GIT_AUTHOR_NAME", "LogHeal Bot")
    
    @property
    def git_author_email(self) -> str:
        return self.get_string("GIT_AUTHOR_EMAIL", "logheal@bot.local")
    
    # Application Configuration
    @property
    def app_env(self) -> str:
        return self.get_string("APP_ENV", "development")
    
    @property
    def app_debug(self) -> bool:
        return self.get_bool("APP_DEBUG", False)
    
    @property
    def app_log_level(self) -> str:
        return self.get_string("APP_LOG_LEVEL", "INFO")
    
    @property
    def app_port(self) -> int:
        return self.get_int("APP_PORT", 8501)
    
    @property
    def app_timeout_seconds(self) -> int:
        return self.get_int("APP_TIMEOUT_SECONDS", 300)
    
    # Caching Configuration
    @property
    def cache_enabled(self) -> bool:
        return self.get_bool("CACHE_ENABLED", True)
    
    @property
    def cache_ttl_seconds(self) -> int:
        return self.get_int("CACHE_TTL_SECONDS", 3600)
    
    # Security Configuration
    @property
    def max_retries(self) -> int:
        return self.get_int("MAX_RETRIES", 3)
    
    @property
    def rate_limit_calls(self) -> int:
        return self.get_int("RATE_LIMIT_CALLS", 10)
    
    @property
    def rate_limit_period_seconds(self) -> int:
        return self.get_int("RATE_LIMIT_PERIOD_SECONDS", 60)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config"""
    global _config
    if _config is None:
        _config = Config()
    return _config
