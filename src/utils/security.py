"""
Security utilities for Ricky application.
Implements file validation, path traversal prevention, and other security features.
"""

import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import filetype

from .config import config
from .logger import security_logger


class SecurityError(Exception):
    """Raised when a security validation fails."""
    pass


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure filename to prevent directory traversal and other attacks.
    
    Args:
        original_filename: Original filename from user input
    
    Returns:
        Secure filename with random prefix
    """
    # Extract extension safely
    extension = ""
    if '.' in original_filename:
        parts = original_filename.rsplit('.', 1)
        if len(parts) == 2 and parts[1].isalnum():
            extension = f".{parts[1].lower()}"
    
    # Generate random filename
    random_name = secrets.token_urlsafe(16)
    return f"{random_name}{extension}"


def validate_image_file(file_path: Path, max_size_bytes: Optional[int] = None) -> Tuple[bool, str]:
    """
    Validate an image file for security and integrity.
    
    Args:
        file_path: Path to the image file
        max_size_bytes: Maximum allowed file size in bytes
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not file_path.exists():
            return False, "File does not exist"
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            return False, "File is empty"
        
        if max_size_bytes and file_size > max_size_bytes:
            return False, f"File size exceeds maximum allowed ({max_size_bytes} bytes)"
        
        # Verify file type using filetype library
        kind = filetype.guess(str(file_path))
        
        allowed_types = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        
        if not kind or kind.extension not in allowed_types:
            detected_type = kind.extension if kind else "unknown"
            security_logger.log_security_event(
                "invalid_file_type",
                {"detected_type": detected_type, "file": str(file_path)}
            )
            return False, f"Invalid file type: {detected_type}"
        
        # Verify using PIL as additional check
        try:
            with Image.open(file_path) as img:
                img.verify()
                
                # Check image dimensions to prevent decompression bombs
                width, height = img.size
                max_pixels = 50_000_000  # 50 megapixels
                if width * height > max_pixels:
                    return False, "Image dimensions too large"
                
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
        
        return True, ""
        
    except Exception as e:
        security_logger.log_error(e, "validate_image_file")
        return False, f"Validation error: {str(e)}"


def secure_path_join(base_path: Path, *paths: str) -> Path:
    """
    Safely join paths preventing directory traversal attacks.
    
    Args:
        base_path: Base directory path
        *paths: Path components to join
    
    Returns:
        Joined path
    
    Raises:
        SecurityError: If resulting path is outside base directory
    """
    # Join paths
    joined = base_path
    for path in paths:
        # Remove any directory traversal attempts
        clean_path = path.replace('..', '').replace('~', '')
        joined = joined / clean_path
    
    # Resolve to absolute path
    resolved = joined.resolve()
    base_resolved = base_path.resolve()
    
    # Check if resolved path is within base directory
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        security_logger.log_security_event(
            "path_traversal_attempt",
            {"attempted_path": str(joined), "base_path": str(base_path)}
        )
        raise SecurityError("Path traversal attempt detected")
    
    return resolved


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate cryptographic hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hex digest of the file hash
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def generate_hmac_signature(data: str, key: Optional[str] = None) -> str:
    """
    Generate HMAC signature for data integrity.
    
    Args:
        data: Data to sign
        key: Secret key (uses config.SECRET_KEY if not provided)
    
    Returns:
        HMAC signature
    """
    if key is None:
        key = config.SECRET_KEY
    
    return hmac.new(
        key.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def verify_hmac_signature(data: str, signature: str, key: Optional[str] = None) -> bool:
    """
    Verify HMAC signature.
    
    Args:
        data: Original data
        signature: Signature to verify
        key: Secret key (uses config.SECRET_KEY if not provided)
    
    Returns:
        True if signature is valid
    """
    expected_signature = generate_hmac_signature(data, key)
    return secrets.compare_digest(signature, expected_signature)


def sanitize_text_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text input to prevent injection attacks.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    # Strip whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes and other control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text


def is_safe_url(url: str, allowed_hosts: Optional[list] = None) -> bool:
    """
    Check if a URL is safe for redirection.
    
    Args:
        url: URL to check
        allowed_hosts: List of allowed hosts (uses config.ALLOWED_HOSTS if not provided)
    
    Returns:
        True if URL is safe
    """
    if allowed_hosts is None:
        allowed_hosts = config.ALLOWED_HOSTS
    
    # Parse URL
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    # Check if host is in allowed list
    return parsed.hostname in allowed_hosts if parsed.hostname else False


def rate_limit_key(identifier: str, action: str) -> str:
    """
    Generate a rate limiting key.
    
    Args:
        identifier: User/IP identifier
        action: Action being rate limited
    
    Returns:
        Rate limit key
    """
    return f"rate_limit:{action}:{identifier}" 