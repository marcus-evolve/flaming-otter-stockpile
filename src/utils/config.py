"""
Secure configuration management for Ricky application.
Handles environment variables with validation and security best practices.
"""

import os
import secrets
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class Config:
    """
    Secure configuration manager with validation.
    Implements security best practices for configuration handling.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Twilio Configuration
        self.TWILIO_ACCOUNT_SID = self._get_required_env("TWILIO_ACCOUNT_SID")
        self.TWILIO_AUTH_TOKEN = self._get_required_env("TWILIO_AUTH_TOKEN")
        self.TWILIO_PHONE_NUMBER = self._validate_phone_number(
            self._get_required_env("TWILIO_PHONE_NUMBER")
        )
        self.RECIPIENT_PHONE_NUMBER = self._validate_phone_number(
            self._get_required_env("RECIPIENT_PHONE_NUMBER")
        )
        
        # Database Configuration
        self.DATABASE_URL = self._validate_database_url(
            self._get_env("DATABASE_URL", "sqlite:///data/ricky.db")
        )
        
        # Security Configuration
        self.SECRET_KEY = self._get_env("SECRET_KEY", self._generate_secret_key())
        self.ALLOWED_HOSTS = self._parse_allowed_hosts(
            self._get_env("ALLOWED_HOSTS", "localhost,127.0.0.1")
        )
        
        # Scheduling Configuration
        self.MIN_INTERVAL_HOURS = self._validate_positive_int(
            self._get_env("MIN_INTERVAL_HOURS", "24"), "MIN_INTERVAL_HOURS"
        )
        self.MAX_INTERVAL_HOURS = self._validate_positive_int(
            self._get_env("MAX_INTERVAL_HOURS", "90"), "MAX_INTERVAL_HOURS"
        )
        
        # Validate interval logic
        if self.MIN_INTERVAL_HOURS >= self.MAX_INTERVAL_HOURS:
            raise ConfigurationError(
                "MIN_INTERVAL_HOURS must be less than MAX_INTERVAL_HOURS"
            )
        
        # File Upload Configuration
        self.MAX_IMAGE_SIZE_MB = self._validate_positive_int(
            self._get_env("MAX_IMAGE_SIZE_MB", "10"), "MAX_IMAGE_SIZE_MB"
        )
        self.MAX_IMAGE_SIZE_BYTES = self.MAX_IMAGE_SIZE_MB * 1024 * 1024
        self.ALLOWED_IMAGE_EXTENSIONS = self._parse_extensions(
            self._get_env("ALLOWED_IMAGE_EXTENSIONS", "jpg,jpeg,png,gif")
        )
        
        # Logging Configuration
        self.LOG_LEVEL = self._validate_log_level(
            self._get_env("LOG_LEVEL", "INFO")
        )
        self.LOG_FILE = self._get_env("LOG_FILE", "logs/ricky.log")
        
        # Environment
        self.ENVIRONMENT = self._validate_environment(
            self._get_env("ENVIRONMENT", "development")
        )
        
        # Application paths
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.IMAGES_DIR = self.DATA_DIR / "images"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # Create necessary directories
        self._create_directories()
    
    @staticmethod
    def _get_env(key: str, default: Optional[str] = None) -> str:
        """Get environment variable with optional default."""
        return os.environ.get(key, default)
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.environ.get(key)
        if not value:
            raise ConfigurationError(f"Required environment variable '{key}' is not set")
        return value
    
    @staticmethod
    def _validate_phone_number(phone: str) -> str:
        """Validate phone number format."""
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Basic validation - should start with + and have 10-15 digits
        if not cleaned.startswith('+'):
            raise ConfigurationError(f"Phone number must start with '+': {phone}")
        
        digits_only = cleaned[1:]
        if not (10 <= len(digits_only) <= 15):
            raise ConfigurationError(
                f"Phone number must have 10-15 digits: {phone}"
            )
        
        if not digits_only.isdigit():
            raise ConfigurationError(
                f"Phone number contains invalid characters: {phone}"
            )
        
        return cleaned
    
    @staticmethod
    def _validate_database_url(url: str) -> str:
        """Validate database URL format."""
        try:
            parsed = urlparse(url)
            allowed_schemes = ['sqlite', 'postgresql', 'postgres']
            if parsed.scheme not in allowed_schemes:
                raise ConfigurationError(
                    f"Invalid database scheme. Must be one of: {allowed_schemes}"
                )
            return url
        except Exception as e:
            raise ConfigurationError(f"Invalid database URL: {e}")
    
    @staticmethod
    def _generate_secret_key() -> str:
        """Generate a secure random secret key."""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def _parse_allowed_hosts(hosts_str: str) -> List[str]:
        """Parse and validate allowed hosts."""
        hosts = [h.strip() for h in hosts_str.split(',') if h.strip()]
        if not hosts:
            raise ConfigurationError("ALLOWED_HOSTS cannot be empty")
        return hosts
    
    @staticmethod
    def _validate_positive_int(value: str, name: str) -> int:
        """Validate that a value is a positive integer."""
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError()
            return int_value
        except ValueError:
            raise ConfigurationError(f"{name} must be a positive integer")
    
    @staticmethod
    def _parse_extensions(extensions_str: str) -> List[str]:
        """Parse and validate file extensions."""
        extensions = [
            ext.strip().lower().lstrip('.')
            for ext in extensions_str.split(',')
            if ext.strip()
        ]
        
        # Validate extensions contain only alphanumeric characters
        for ext in extensions:
            if not ext.isalnum():
                raise ConfigurationError(f"Invalid file extension: {ext}")
        
        return extensions
    
    @staticmethod
    def _validate_log_level(level: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level_upper = level.upper()
        if level_upper not in valid_levels:
            raise ConfigurationError(
                f"Invalid log level. Must be one of: {valid_levels}"
            )
        return level_upper
    
    @staticmethod
    def _validate_environment(env: str) -> str:
        """Validate environment name."""
        valid_envs = ['development', 'staging', 'production']
        env_lower = env.lower()
        if env_lower not in valid_envs:
            raise ConfigurationError(
                f"Invalid environment. Must be one of: {valid_envs}"
            )
        return env_lower
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [self.DATA_DIR, self.IMAGES_DIR, self.LOGS_DIR]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # Set secure permissions (owner read/write/execute only)
            directory.chmod(0o700)
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == 'development'


# Singleton instance
config = Config() 