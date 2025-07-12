#!/usr/bin/env python3
"""
Main entry point for the Ricky web application.
Run this to start the web interface.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web.app import create_app
from src.utils.config import config
from src.utils.logger import logger


def main():
    """Run the Flask web application."""
    app = create_app()
    
    # Development server settings
    debug = config.is_development()
    host = '127.0.0.1'
    port = 5000
    
    logger.info(f"Starting Ricky web app on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    print(f"\n{'='*50}")
    print(f"Ricky Web Interface")
    print(f"{'='*50}")
    print(f"URL: http://{host}:{port}")
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"Debug: {debug}")
    print(f"\nPress CTRL+C to stop")
    print(f"{'='*50}\n")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        logger.info("Web server stopped")


if __name__ == '__main__':
    main() 