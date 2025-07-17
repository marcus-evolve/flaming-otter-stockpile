from threading import Lock
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from ..models import get_db_session, Image
from ..utils.config import config
from ..utils.logger import logger, security_logger
from .twilio_service import TwilioService
from .pushbullet_service import PushbulletService


class RandomScheduler:
    """
    Manages scheduling of sending images at random intervals.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RandomScheduler, cls).__new__(cls)
                    cls._instance.scheduler = BackgroundScheduler(
                        timezone='UTC',
                        job_defaults={'misfire_grace_time': 3600}
                    )
                    # Select and initialize the notification service
                    if config.NOTIFICATION_SERVICE == "pushbullet":
                        cls._instance.notification_service = PushbulletService()
                    else:  # Default to Twilio
                        cls._instance.notification_service = TwilioService()
                    
                    cls._instance.is_running = False
        return cls._instance

    def start(self):
        if not self.is_running:
            self.schedule_next_job()
            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler started.")

    def schedule_next_job(self):
        """Schedules the next job to send an image."""
        # This method needs to be implemented based on how you want to schedule jobs.
        # For example, you might want to schedule a job to send an image at a random interval.
        # For now, we'll just add a placeholder.
        logger.info("Scheduling next job...")
        # Example: Schedule a job to send an image after a random interval
        # self.scheduler.add_job(
        #     self.send_random_image,
        #     'interval',
        #     minutes=random.randint(1, 10), # Send every 1-10 minutes
        #     id=f'send_random_image_{uuid.uuid4()}'
        # )

    def send_random_image(self):
        """Sends a random image from the database."""
        with get_db_session() as session:
            image_to_send = session.query(Image).filter(
                Image.is_sent == False, # Only send images that haven't been sent yet
                Image.is_test == False # Exclude test images
            ).order_by(Image.last_sent).first()

            if not image_to_send:
                logger.info("No images to send. Waiting for next scheduled job.")
                return

            image_to_send.is_sent = True
            image_to_send.last_sent = datetime.utcnow()
            session.commit()

            image_path = config.IMAGES_DIR / image_to_send.filename
            
            # Use the initialized notification service to send the image
            success, message_id = self.notification_service.send_image_message(
                image_path=image_path,
                description=image_to_send.description,
                image_id=image_to_send.id
            )

            if success:
                logger.info(f"Image {image_to_send.id} sent successfully. Message ID: {message_id}")
            else:
                logger.error(f"Failed to send image {image_to_send.id}. Error: {message_id}")

    def send_test_message(self, image_id: int) -> tuple[bool, str]:
        """Sends a test message for a specific image."""
        with get_db_session() as session:
            image = session.query(Image).get(image_id)
            if not image:
                return False, "Image not found"

            image_path = config.IMAGES_DIR / image.filename
            
            # Use the notification service to send the test message
            success, message = self.notification_service.send_image_message(
                image_path=image_path,
                description=f"Test: {image.description}",
                image_id=image.id
            )
            
            if success:
                return True, f"Test message sent successfully. Details: {message}"
            else:
                return False, f"Failed to send test message. Error: {message}"

    def get_next_scheduled_time(self) -> Optional[datetime]:
        """Gets the next scheduled job's run time."""
        # This method needs to be implemented based on how you want to check scheduled jobs.
        # For example, you might want to return the next scheduled job's run time.
        # For now, we'll just return a placeholder.
        return None 