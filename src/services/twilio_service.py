"""
Twilio service for sending SMS/MMS messages with security and reliability features.
"""

import time
import base64
import json
from pathlib import Path
from typing import Optional, Tuple
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import requests
import os

from ..utils.config import config
from ..utils.logger import logger, security_logger
from ..utils.security import validate_image_file, secure_path_join


class TwilioService:
    """
    Secure Twilio service for sending messages with images.
    Implements retry logic, error handling, and security features.
    """
    
    def __init__(self):
        """Initialize Twilio client with configuration."""
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.from_number = config.TWILIO_PHONE_NUMBER
        self.to_number = config.RECIPIENT_PHONE_NUMBER
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def send_image_message(
        self, 
        image_path: Path, 
        description: str,
        image_id: int
    ) -> Tuple[bool, str]:
        """
        Send an image with description via MMS.
        
        Args:
            image_path: Path to the image file
            description: Text description to send
            image_id: Database ID of the image (for logging)
        
        Returns:
            Tuple of (success, message_sid or error_message)
        """
        try:
            # Validate image file for security
            is_valid, error_msg = validate_image_file(
                image_path, 
                config.MAX_IMAGE_SIZE_BYTES
            )
            if not is_valid:
                security_logger.log_security_event(
                    "invalid_image_send_attempt",
                    {"image_id": image_id, "error": error_msg}
                )
                return False, f"Image validation failed: {error_msg}"
            
            # Secure the path
            secure_image_path = secure_path_join(config.IMAGES_DIR, image_path.name)
            
            # Upload image to temporary hosting (in production, use a CDN)
            media_url = self._get_media_url(image_id, image_path.name)
            if not media_url:
                return False, "Failed to prepare media URL"
            
            # Send message with retry logic
            for attempt in range(self.max_retries):
                try:
                    message = self.client.messages.create(
                        body=description[:1600],  # SMS limit
                        from_=self.from_number,
                        to=self.to_number,
                        media_url=[media_url]
                    )
                    
                    # Log successful send
                    security_logger.log_message_sent(
                        image_id=image_id,
                        success=True,
                        error=""
                    )
                    
                    logger.info(
                        f"Message sent successfully: {message.sid}",
                        extra={
                            "image_id": image_id,
                            "message_sid": message.sid,
                            "attempt": attempt + 1
                        }
                    )
                    
                    return True, message.sid
                    
                except TwilioException as e:
                    error_msg = str(e)
                    logger.warning(
                        f"Twilio error on attempt {attempt + 1}: {error_msg}",
                        extra={"image_id": image_id, "attempt": attempt + 1}
                    )
                    
                    # Check if error is retryable
                    if not self._is_retryable_error(e):
                        security_logger.log_message_sent(
                            image_id=image_id,
                            success=False,
                            error=error_msg
                        )
                        return False, f"Non-retryable error: {error_msg}"
                    
                    # Wait before retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
            
            # All retries exhausted
            security_logger.log_message_sent(
                image_id=image_id,
                success=False,
                error="Max retries exhausted"
            )
            return False, "Failed after maximum retry attempts"
            
        except Exception as e:
            security_logger.log_error(e, f"send_image_message for image {image_id}")
            return False, f"Unexpected error: {str(e)}"
    
    def _get_media_url(self, image_id: int, filename: str) -> Optional[str]:
        """
        Get publicly accessible URL for the image.
        
        In production, this should upload to a CDN or cloud storage.
        For development, we'll use a placeholder approach.
        
        Args:
            image_id: The database ID of the image
            filename: The filename of the image, for URL formatting
        
        Returns:
            Public URL or None if failed
        """
        # Get base URL from environment or use ngrok for local development
        base_url = os.environ.get('BASE_URL', 'https://2119dbe613bd.ngrok-free.app')
        
        # Generate the full image URL
        image_url = f"{base_url}/images/{image_id}/{filename}"
        logger.info(f"Generated media URL: {image_url}")
        return image_url
    
    def _is_retryable_error(self, error: TwilioException) -> bool:
        """
        Determine if a Twilio error is retryable.
        
        Args:
            error: Twilio exception
        
        Returns:
            True if error is retryable
        """
        # Get error code if available
        error_code = getattr(error, 'code', None)
        
        # Non-retryable error codes
        non_retryable_codes = {
            20003,  # Authentication error
            21211,  # Invalid 'To' phone number
            21212,  # Invalid 'From' phone number
            21606,  # 'To' phone number is not a valid mobile number
            21614,  # 'To' number is not a valid phone number
        }
        
        if error_code in non_retryable_codes:
            return False
        
        # Check for rate limiting
        if error_code == 20429:  # Too many requests
            return True
        
        # Default to retryable for unknown errors
        return True
    
    def verify_configuration(self) -> Tuple[bool, str]:
        """
        Verify Twilio configuration and account status.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Fetch account details
            account = self.client.api.accounts(self.account_sid).fetch()
            
            if account.status != 'active':
                return False, f"Account is not active: {account.status}"
            
            # Verify from number
            incoming_phone_numbers = self.client.incoming_phone_numbers.list(
                phone_number=self.from_number
            )
            
            if not incoming_phone_numbers:
                return False, f"Phone number {self.from_number} not found in account"
            
            return True, "Configuration verified successfully"
            
        except Exception as e:
            return False, f"Configuration verification failed: {str(e)}" 