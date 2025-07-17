"""
Pushbullet service for sending push notifications with images.
"""

import requests
from pathlib import Path
from typing import Tuple, Optional

from ..utils.config import config
from ..utils.logger import logger, security_logger
from ..utils.security import validate_image_file


class PushbulletService:
    """
    Service for sending push notifications with images via Pushbullet.
    """
    API_URL = "https://api.pushbullet.com/v2"

    def __init__(self):
        """Initialize Pushbullet service with configuration."""
        self.api_key = config.PUSHBULLET_API_KEY
        if not self.api_key:
            raise ValueError("PUSHBULLET_API_KEY is not set in the configuration.")

    def _send_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Helper to send authenticated requests to the Pushbullet API."""
        headers = {
            "Access-Token": self.api_key,
            "Content-Type": "application/json"
        }
        url = f"{self.API_URL}/{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()  # Will raise an exception for 4xx/5xx errors
        return response

    def _upload_file(self, image_path: Path) -> Optional[dict]:
        """
        Uploads a file to Pushbullet and returns the file details.

        Args:
            image_path: Path to the image file.

        Returns:
            A dictionary with file details from Pushbullet API or None on failure.
        """
        try:
            # 1. Request an upload URL
            file_name = image_path.name
            with open(image_path, "rb") as f:
                mime_type = "image/jpeg"  # Adjust if you have other types
                upload_req_data = {
                    "file_name": file_name,
                    "file_type": mime_type,
                }
                upload_req = self._send_request("post", "upload-request", json=upload_req_data)
                upload_data = upload_req.json()

                # 2. Upload the file to the provided URL
                with open(image_path, "rb") as f_upload:
                    files = {"file": f_upload}
                    upload_response = requests.post(
                        upload_data["upload_url"], data=upload_data["data"], files=files
                    )
                    upload_response.raise_for_status()
                
                return upload_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Pushbullet file upload failed: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Pushbullet upload: {e}", exc_info=True)
            return None

    def send_image_message(
        self,
        image_path: Path,
        description: str,
        image_id: int
    ) -> Tuple[bool, str]:
        """
        Send an image with a description via Pushbullet.

        Args:
            image_path: Path to the image file.
            description: Text description to send with the image.
            image_id: Database ID of the image for logging.

        Returns:
            A tuple of (success, message or error_message).
        """
        try:
            # Validate image file
            is_valid, error_msg = validate_image_file(
                image_path, config.MAX_IMAGE_SIZE_BYTES
            )
            if not is_valid:
                security_logger.log_security_event(
                    "invalid_image_send_attempt",
                    {"image_id": image_id, "error": error_msg, "service": "pushbullet"}
                )
                return False, f"Image validation failed: {error_msg}"

            # Upload the file to get file_url and file_type
            upload_details = self._upload_file(image_path)
            if not upload_details:
                return False, "Failed to upload image to Pushbullet."

            # Send the push notification with the uploaded file
            push_data = {
                "type": "file",
                "title": "Ricky: New Image",
                "body": description,
                "file_name": upload_details["file_name"],
                "file_type": upload_details["file_type"],
                "file_url": upload_details["file_url"],
            }
            response = self._send_request("post", "pushes", json=push_data)
            
            push_iden = response.json().get("iden", "N/A")
            logger.info(
                f"Pushbullet message sent successfully: {push_iden}",
                extra={"image_id": image_id, "push_iden": push_iden}
            )
            security_logger.log_message_sent(
                image_id=image_id,
                success=True,
                error="",
                service="pushbullet"
            )
            return True, f"Pushbullet notification sent: {push_iden}"

        except requests.exceptions.RequestException as e:
            error_message = f"Pushbullet API error: {e.response.text if e.response else e}"
            logger.error(error_message, exc_info=True)
            security_logger.log_message_sent(
                image_id=image_id,
                success=False,
                error=error_message,
                service="pushbullet"
            )
            return False, error_message
        except Exception as e:
            logger.error(f"Unexpected error in Pushbullet service: {e}", exc_info=True)
            security_logger.log_error(e, f"send_image_message for image {image_id} via Pushbullet")
            return False, f"An unexpected error occurred: {str(e)}"

    def verify_configuration(self) -> Tuple[bool, str]:
        """
        Verify Pushbullet API key by fetching user info.

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            self._send_request("get", "users/me")
            return True, "Pushbullet configuration verified successfully."
        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 401:
                return False, "Pushbullet API key is invalid."
            return False, f"Failed to connect to Pushbullet: {str(e)}"
        except Exception as e:
            return False, f"Configuration verification failed: {str(e)}" 