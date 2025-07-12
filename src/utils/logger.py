"""
Secure logging configuration for Ricky application.
Implements JSON logging with security best practices.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from typing import Optional

from .config import config


def setup_logger(name: str = "ricky") -> logging.Logger:
    """
    Set up a secure logger with JSON formatting.
    
    Args:
        name: Logger name (default: "ricky")
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers = []
    
    # JSON formatter for structured logging
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp"}
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.LOG_FILE:
        log_path = Path(config.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotate logs at 10MB, keep 5 backup files
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Set secure permissions on log file
        try:
            log_path.chmod(0o600)  # Owner read/write only
        except:
            pass  # May fail on some systems
    
    return logger


class SecurityLogger:
    """
    Specialized logger for security events.
    Ensures sensitive data is not logged.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize security logger."""
        self.logger = logger or setup_logger("ricky.security")
    
    def log_auth_attempt(self, success: bool, reason: str = ""):
        """Log authentication attempt without exposing credentials."""
        self.logger.info(
            "Authentication attempt",
            extra={
                "event": "auth_attempt",
                "success": success,
                "reason": reason
            }
        )
    
    def log_image_access(self, image_id: int, action: str):
        """Log image access events."""
        self.logger.info(
            "Image access",
            extra={
                "event": "image_access",
                "image_id": image_id,
                "action": action
            }
        )
    
    def log_message_sent(self, image_id: int, success: bool, error: str = ""):
        """Log message sending events."""
        self.logger.info(
            "Message sent",
            extra={
                "event": "message_sent",
                "image_id": image_id,
                "success": success,
                "error": error
            }
        )
    
    def log_security_event(self, event_type: str, details: dict):
        """Log generic security events."""
        # Filter out sensitive keys
        sensitive_keys = {'password', 'token', 'secret', 'auth', 'key'}
        filtered_details = {
            k: v for k, v in details.items()
            if not any(sensitive in k.lower() for sensitive in sensitive_keys)
        }
        
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                "event": "security",
                "event_type": event_type,
                **filtered_details
            }
        )
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors without exposing sensitive information."""
        self.logger.error(
            f"Error in {context}",
            extra={
                "event": "error",
                "error_type": type(error).__name__,
                "error_message": str(error)[:200],  # Limit message length
                "context": context
            }
        )


# Create default logger instances
logger = setup_logger()
security_logger = SecurityLogger() 