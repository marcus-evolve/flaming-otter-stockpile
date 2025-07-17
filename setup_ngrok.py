#!/usr/bin/env python3
"""
Setup script for ngrok with authentication.
This resolves the 403 Forbidden error when Twilio tries to access images.
"""

import subprocess
import sys
import os


def setup_ngrok():
    """Guide user through ngrok setup with authentication."""
    print("=" * 60)
    print("NGROK SETUP FOR TWILIO INTEGRATION")
    print("=" * 60)
    print("\nThe 403 Forbidden error occurs because ngrok's free tier")
    print("blocks non-browser requests. To fix this, you need to:")
    print("\n1. Create a free ngrok account at https://ngrok.com/signup")
    print("2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")
    print("3. Run: ngrok config add-authtoken YOUR_TOKEN")
    print("4. Restart ngrok: ngrok http 5000")
    print("\nThis will remove the restrictions and allow Twilio to access your images.")
    
    response = input("\nHave you created an ngrok account? (y/n): ")
    if response.lower() != 'y':
        print("\nPlease create an account at https://ngrok.com/signup")
        print("Then run this script again.")
        return
    
    token = input("\nEnter your ngrok authtoken: ").strip()
    if not token:
        print("Error: No token provided")
        return
    
    try:
        # Configure ngrok with the authtoken
        result = subprocess.run(['ngrok', 'config', 'add-authtoken', token], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✓ Ngrok configured successfully!")
            print("\nNow you can run: ngrok http 5000")
            print("The 403 Forbidden error should be resolved.")
        else:
            print(f"\nError configuring ngrok: {result.stderr}")
    except FileNotFoundError:
        print("\nError: ngrok not found. Please install it first:")
        print("- Download from: https://ngrok.com/download")
        print("- Or use: brew install ngrok (on macOS)")
    except Exception as e:
        print(f"\nError: {e}")


def update_twilio_url():
    """Update the Twilio service with the new ngrok URL."""
    print("\n" + "=" * 60)
    print("UPDATE TWILIO SERVICE URL")
    print("=" * 60)
    
    url = input("\nEnter your new ngrok URL (e.g., https://abc123.ngrok-free.app): ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    # Update the Twilio service file
    twilio_service_path = os.path.join(os.path.dirname(__file__), 
                                      'src', 'services', 'twilio_service.py')
    
    try:
        with open(twilio_service_path, 'r') as f:
            content = f.read()
        
        # Find and replace the ngrok URL
        import re
        pattern = r'ngrok_url = "https://[^"]+"'
        replacement = f'ngrok_url = "{url}"'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(twilio_service_path, 'w') as f:
                f.write(new_content)
            print(f"\n✓ Updated Twilio service with new URL: {url}")
            print("\nRestart your Flask application to use the new URL.")
        else:
            print("\nError: Could not find ngrok URL in Twilio service file")
    except Exception as e:
        print(f"\nError updating file: {e}")


if __name__ == "__main__":
    print("This script helps you set up ngrok to work with Twilio.\n")
    print("1. Setup ngrok with authentication")
    print("2. Update Twilio service URL")
    print("3. Exit")
    
    choice = input("\nSelect an option (1-3): ")
    
    if choice == '1':
        setup_ngrok()
    elif choice == '2':
        update_twilio_url()
    elif choice == '3':
        sys.exit(0)
    else:
        print("Invalid choice") 