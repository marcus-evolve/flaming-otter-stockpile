"""
Main entry point for Ricky application.
Handles initialization, signal handling, and graceful shutdown.
"""

import signal
import sys
import time
from pathlib import Path

from utils.config import config, ConfigurationError
from utils.logger import logger
from models import init_db
from services import RandomScheduler


class RickyApp:
    """Main application class for Ricky."""
    
    def __init__(self):
        """Initialize the application."""
        self.scheduler = None
        self.running = False
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
        if self.scheduler:
            self.scheduler.stop()
        
        sys.exit(0)
    
    def _verify_configuration(self):
        """Verify all configuration and dependencies."""
        logger.info("Verifying configuration...")
        
        # Check required directories exist
        required_dirs = [config.DATA_DIR, config.IMAGES_DIR, config.LOGS_DIR]
        for directory in required_dirs:
            if not directory.exists():
                logger.error(f"Required directory not found: {directory}")
                raise ConfigurationError(f"Directory {directory} does not exist")
        
        # Verify at least one image exists
        image_files = list(config.IMAGES_DIR.glob("*"))
        if not image_files:
            logger.warning("No images found in images directory")
        
        logger.info("Configuration verified successfully")
    
    def run(self):
        """Run the main application."""
        try:
            logger.info("Starting Ricky application...")
            
            # Verify configuration
            self._verify_configuration()
            
            # Initialize database
            logger.info("Initializing database...")
            init_db()
            
            # Create and start scheduler
            logger.info("Starting scheduler...")
            self.scheduler = RandomScheduler()
            
            # Verify Twilio configuration
            is_valid, message = self.scheduler.twilio_service.verify_configuration()
            if not is_valid:
                logger.error(f"Twilio configuration error: {message}")
                raise ConfigurationError(f"Twilio error: {message}")
            
            logger.info("Twilio configuration verified")
            
            # Start the scheduler
            self.scheduler.start()
            
            # Log next scheduled time
            next_time = self.scheduler.get_next_scheduled_time()
            if next_time:
                logger.info(f"Next message scheduled for: {next_time}")
            
            # Mark as running
            self.running = True
            
            logger.info("Ricky is running! Press Ctrl+C to stop.")
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            sys.exit(1)
        
        finally:
            # Ensure scheduler is stopped
            if self.scheduler:
                self.scheduler.stop()
            
            logger.info("Ricky application stopped")


def main():
    """Main entry point."""
    app = RickyApp()
    app.run()


if __name__ == "__main__":
    main() 