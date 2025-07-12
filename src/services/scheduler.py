"""
Random scheduler service for unpredictable message timing.
Implements cryptographically secure randomness to ensure true surprises.
"""

import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Tuple
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from ..utils.config import config
from ..utils.logger import logger
from ..models import Image, get_db_session
from .twilio_service import TwilioService


class RandomScheduler:
    """
    Scheduler that sends messages at truly random intervals.
    Uses cryptographically secure randomness to prevent any patterns.
    """
    
    def __init__(self):
        """Initialize the random scheduler."""
        self.twilio_service = TwilioService()
        
        # Configure job stores and executors
        jobstores = {
            'default': SQLAlchemyJobStore(url=config.DATABASE_URL)
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=1)
        }
        
        # Create scheduler with persistence
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 3600  # 1 hour grace period
            }
        )
        
        # Interval configuration (in seconds)
        self.min_interval_seconds = config.MIN_INTERVAL_HOURS * 3600
        self.max_interval_seconds = config.MAX_INTERVAL_HOURS * 3600
        
        # Job ID for tracking
        self.job_id = "ricky_random_sender"
    
    def start(self):
        """Start the scheduler and schedule the first job."""
        try:
            # Start scheduler
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            
            # Check if job already exists (from previous run)
            existing_job = self.scheduler.get_job(self.job_id)
            if not existing_job:
                # Schedule first job
                self._schedule_next_send()
                logger.info("Initial job scheduled")
            else:
                logger.info(f"Existing job found, next run at: {existing_job.next_run_time}")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler gracefully."""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def _get_truly_random_interval(self) -> int:
        """
        Generate a truly random interval using cryptographically secure randomness.
        
        Returns:
            Random interval in seconds
        """
        # Calculate range
        interval_range = self.max_interval_seconds - self.min_interval_seconds
        
        # Use secrets module for cryptographically secure randomness
        # This prevents any predictable patterns
        random_offset = secrets.randbelow(interval_range + 1)
        
        # Add random offset to minimum interval
        interval = self.min_interval_seconds + random_offset
        
        # Add micro-randomness (0-3600 seconds) to prevent hourly patterns
        micro_random = secrets.randbelow(3601)
        interval += micro_random
        
        # Ensure we don't exceed maximum
        interval = min(interval, self.max_interval_seconds)
        
        logger.info(f"Generated random interval: {interval} seconds ({interval/3600:.2f} hours)")
        
        return interval
    
    def _send_random_image(self):
        """Send a random image and schedule the next send."""
        try:
            with get_db_session() as session:
                # Get random unsent image
                image = Image.get_random_unsent(session)
                
                # If no unsent images, reset all and try again
                if not image:
                    logger.info("All images sent, resetting status")
                    reset_count = Image.reset_all_sent_status(session)
                    logger.info(f"Reset {reset_count} images to unsent status")
                    
                    # Try again after reset
                    image = Image.get_random_unsent(session)
                
                if not image:
                    logger.error("No images available to send")
                    return
                
                # Build image path
                image_path = config.IMAGES_DIR / image.filename
                
                # Send the image
                success, result = self.twilio_service.send_image_message(
                    image_path=image_path,
                    description=image.description,
                    image_id=image.id
                )
                
                if success:
                    # Mark image as sent
                    image.mark_as_sent()
                    session.commit()
                    
                    logger.info(
                        f"Successfully sent image {image.id}: {image.filename}",
                        extra={
                            "image_id": image.id,
                            "message_sid": result,
                            "send_count": image.send_count
                        }
                    )
                else:
                    logger.error(
                        f"Failed to send image {image.id}: {result}",
                        extra={"image_id": image.id, "error": result}
                    )
        
        except Exception as e:
            logger.error(f"Error in send_random_image: {e}")
        
        finally:
            # Always schedule next send
            self._schedule_next_send()
    
    def _schedule_next_send(self):
        """Schedule the next random send."""
        try:
            # Get truly random interval
            interval_seconds = self._get_truly_random_interval()
            
            # Calculate next run time
            next_run_time = datetime.now() + timedelta(seconds=interval_seconds)
            
            # Remove existing job if any
            existing_job = self.scheduler.get_job(self.job_id)
            if existing_job:
                self.scheduler.remove_job(self.job_id)
            
            # Schedule new job
            self.scheduler.add_job(
                func=self._send_random_image,
                trigger="date",
                run_date=next_run_time,
                id=self.job_id,
                replace_existing=True,
                misfire_grace_time=3600
            )
            
            logger.info(
                f"Next message scheduled for: {next_run_time} "
                f"({interval_seconds/3600:.2f} hours from now)"
            )
            
        except Exception as e:
            logger.error(f"Error scheduling next send: {e}")
            # Try again in minimum interval
            self.scheduler.add_job(
                func=self._send_random_image,
                trigger="date",
                run_date=datetime.now() + timedelta(seconds=self.min_interval_seconds),
                id=self.job_id,
                replace_existing=True
            )
    
    def send_test_message(self, image_id: int) -> Tuple[bool, str]:
        """
        Send a test message immediately (bypassing schedule).
        
        Args:
            image_id: ID of image to send
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_session() as session:
                image = session.query(Image).filter_by(id=image_id).first()
                
                if not image:
                    return False, f"Image with ID {image_id} not found"
                
                # Build image path
                image_path = config.IMAGES_DIR / image.filename
                
                # Send the image
                success, result = self.twilio_service.send_image_message(
                    image_path=image_path,
                    description=image.description,
                    image_id=image.id
                )
                
                if success:
                    return True, f"Test message sent successfully: {result}"
                else:
                    return False, f"Failed to send test message: {result}"
                
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False, f"Error: {str(e)}"
    
    def get_next_scheduled_time(self) -> Optional[datetime]:
        """Get the next scheduled send time."""
        job = self.scheduler.get_job(self.job_id)
        return job.next_run_time if job else None
    
    def force_reschedule(self):
        """Force a reschedule with new random interval."""
        logger.info("Forcing reschedule with new random interval")
        self._schedule_next_send() 