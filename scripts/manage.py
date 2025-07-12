#!/usr/bin/env python3
"""
Management CLI for Ricky application.
Provides commands for managing images, testing, and monitoring.
"""

import sys
from pathlib import Path
from datetime import datetime
import click

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import config
from src.utils.logger import logger
from src.models import get_db_session, Image, init_db
from src.services import TwilioService, RandomScheduler


@click.group()
def cli():
    """Ricky management commands."""
    pass


@cli.command()
def list_images():
    """List all images in the database."""
    try:
        init_db()
        with get_db_session() as session:
            images = session.query(Image).order_by(Image.created_at).all()
            
            if not images:
                print("No images found in database.")
                return
            
            print(f"\n{'ID':<5} {'Filename':<30} {'Sent':<6} {'Count':<6} {'Last Sent':<20} {'Description':<50}")
            print("-" * 120)
            
            for img in images:
                last_sent = img.last_sent.strftime("%Y-%m-%d %H:%M") if img.last_sent else "Never"
                desc = img.description[:47] + "..." if len(img.description) > 50 else img.description
                status = "Yes" if img.is_sent else "No"
                
                print(f"{img.id:<5} {img.filename:<30} {status:<6} {img.send_count:<6} {last_sent:<20} {desc:<50}")
            
            # Summary
            total = len(images)
            sent = sum(1 for img in images if img.is_sent)
            unsent = total - sent
            
            print(f"\nTotal: {total} | Sent: {sent} | Unsent: {unsent}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('image_id', type=int)
def send_test(image_id):
    """Send a test message with specified image."""
    try:
        init_db()
        scheduler = RandomScheduler()
        
        print(f"Sending test message with image ID {image_id}...")
        success, message = scheduler.send_test_message(image_id)
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@cli.command()
def verify_twilio():
    """Verify Twilio configuration."""
    try:
        print("Verifying Twilio configuration...")
        
        service = TwilioService()
        is_valid, message = service.verify_configuration()
        
        print(f"\nAccount SID: {config.TWILIO_ACCOUNT_SID[:10]}...")
        print(f"From Number: {config.TWILIO_PHONE_NUMBER}")
        print(f"To Number: {config.RECIPIENT_PHONE_NUMBER}")
        
        if is_valid:
            print(f"\n✓ {message}")
        else:
            print(f"\n✗ {message}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@cli.command()
def reset_sent_status():
    """Reset sent status for all images."""
    try:
        init_db()
        
        if not click.confirm("This will mark all images as unsent. Continue?"):
            return
        
        with get_db_session() as session:
            count = Image.reset_all_sent_status(session)
            print(f"✓ Reset {count} images to unsent status")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('image_id', type=int)
@click.option('--activate/--deactivate', default=True)
def toggle_image(image_id, activate):
    """Activate or deactivate an image."""
    try:
        init_db()
        
        with get_db_session() as session:
            image = session.query(Image).filter_by(id=image_id).first()
            
            if not image:
                print(f"Image with ID {image_id} not found")
                sys.exit(1)
            
            image.is_active = activate
            session.commit()
            
            status = "activated" if activate else "deactivated"
            print(f"✓ Image {image_id} ({image.filename}) {status}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@cli.command()
def stats():
    """Show statistics about the image database."""
    try:
        init_db()
        
        with get_db_session() as session:
            total = session.query(Image).count()
            active = session.query(Image).filter_by(is_active=True).count()
            sent = session.query(Image).filter_by(is_sent=True).count()
            
            # Get most and least sent images
            most_sent = session.query(Image).order_by(
                Image.send_count.desc()
            ).first()
            
            never_sent = session.query(Image).filter_by(
                send_count=0
            ).count()
            
            print("\n=== Ricky Statistics ===")
            print(f"Total images: {total}")
            print(f"Active images: {active}")
            print(f"Sent at least once: {sent}")
            print(f"Never sent: {never_sent}")
            
            if most_sent and most_sent.send_count > 0:
                print(f"\nMost sent image:")
                print(f"  - {most_sent.filename}")
                print(f"  - Sent {most_sent.send_count} times")
                print(f"  - Last sent: {most_sent.last_sent}")
            
            # Calculate average time between sends
            recent_sends = session.query(Image).filter(
                Image.last_sent.isnot(None)
            ).order_by(Image.last_sent.desc()).limit(10).all()
            
            if len(recent_sends) >= 2:
                time_diffs = []
                for i in range(len(recent_sends) - 1):
                    diff = recent_sends[i].last_sent - recent_sends[i+1].last_sent
                    time_diffs.append(diff.total_seconds() / 3600)  # Hours
                
                if time_diffs:
                    avg_hours = sum(time_diffs) / len(time_diffs)
                    print(f"\nAverage time between last {len(time_diffs)+1} sends: {avg_hours:.1f} hours")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@cli.command()
def check_schedule():
    """Check when the next message is scheduled."""
    try:
        init_db()
        scheduler = RandomScheduler()
        
        # Note: This creates a new scheduler instance, so it won't show
        # the actual running schedule. In production, you'd query the
        # job store directly.
        
        print("Checking schedule...")
        print("\nNote: This shows what would be scheduled if starting now.")
        print("The actual running scheduler may have a different schedule.")
        
        # Show configuration
        print(f"\nConfiguration:")
        print(f"  Min interval: {config.MIN_INTERVAL_HOURS} hours")
        print(f"  Max interval: {config.MAX_INTERVAL_HOURS} hours")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('image_id', type=int)
def delete_image(image_id):
    """Delete an image from the database."""
    try:
        init_db()
        
        with get_db_session() as session:
            image = session.query(Image).filter_by(id=image_id).first()
            
            if not image:
                print(f"Image with ID {image_id} not found")
                sys.exit(1)
            
            filename = image.filename
            filepath = config.IMAGES_DIR / filename
            
            if not click.confirm(f"Delete image {image_id} ({filename})?"):
                return
            
            # Delete from database
            session.delete(image)
            session.commit()
            
            # Delete file if exists
            if filepath.exists():
                filepath.unlink()
                print(f"✓ Deleted file: {filepath}")
            
            print(f"✓ Deleted image {image_id} from database")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli() 