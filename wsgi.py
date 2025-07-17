"""
WSGI entry point for Railway deployment.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and create the Flask app
from src.web.app import create_app

app = create_app()

if __name__ == "__main__":
    # For local testing
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 