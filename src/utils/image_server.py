"""
Simple image server for Twilio media files.
Runs on a separate port to bypass ngrok restrictions.
"""

import os
from pathlib import Path
from flask import Flask, send_from_directory, abort

# Get the images directory from the main config
IMAGES_DIR = Path(__file__).parent.parent.parent / "data" / "images"

app = Flask(__name__)

@app.route('/media/<path:filename>')
def serve_image(filename):
    """Serve image files directly."""
    try:
        # Security check - ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename:
            abort(403)
        
        # Check if file exists
        file_path = IMAGES_DIR / filename
        if not file_path.exists():
            abort(404)
        
        # Serve the file
        return send_from_directory(IMAGES_DIR, filename)
    except Exception as e:
        print(f"Error serving image: {e}")
        abort(500)

if __name__ == '__main__':
    print(f"Starting image server on port 5001")
    print(f"Images directory: {IMAGES_DIR}")
    # Run on a different port that's not behind ngrok
    app.run(host='0.0.0.0', port=5001, debug=False) 