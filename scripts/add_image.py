#!/usr/bin/env python3
"""
Script to add images to Ricky database with security validation.
Includes progress tracking and batch processing capabilities.
"""

import sys
import os
import shutil
from pathlib import Path
from typing import List, Tuple
import click
import magic

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import config
from src.utils.logger import logger
from src.utils.security import (
    validate_image_file, generate_secure_filename, 
    calculate_file_hash, secure_path_join, sanitize_text_input
)
from src.models import get_db_session, Image


class ImageAdder:
    """Add images to database with progress tracking."""
    
    def __init__(self):
        """Initialize image adder."""
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        self.skipped = 0
    
    def _print_progress(self, message: str, status: str = "INFO"):
        """Print progress message with status."""
        symbols = {
            "INFO": "ℹ",
            "SUCCESS": "✓",
            "ERROR": "✗",
            "WARNING": "⚠",
            "PROCESSING": "⟳"
        }
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")
    
    def add_single_image(
        self, 
        image_path: Path, 
        description: str,
        skip_existing: bool = True
    ) -> Tuple[bool, str]:
        """
        Add a single image to the database.
        
        Args:
            image_path: Path to the image file
            description: Description for the image
            skip_existing: Skip if image already exists
        
        Returns:
            Tuple of (success, message)
        """
        try:
            self._print_progress(f"Processing: {image_path.name}", "PROCESSING")
            
            # Validate image file
            is_valid, error_msg = validate_image_file(
                image_path, 
                config.MAX_IMAGE_SIZE_BYTES
            )
            
            if not is_valid:
                return False, f"Validation failed: {error_msg}"
            
            # Calculate file hash
            file_hash = calculate_file_hash(image_path)
            
            with get_db_session() as session:
                # Check if image already exists
                existing = session.query(Image).filter_by(
                    file_hash=file_hash
                ).first()
                
                if existing:
                    if skip_existing:
                        return False, "Image already exists (same hash)"
                    else:
                        # Update description if different
                        if existing.description != description:
                            existing.description = sanitize_text_input(description)
                            session.commit()
                            return True, "Updated existing image description"
                        return False, "Image already exists with same description"
                
                # Generate secure filename
                secure_filename = generate_secure_filename(image_path.name)
                
                # Ensure unique filename
                counter = 0
                base_name = secure_filename
                while (config.IMAGES_DIR / secure_filename).exists():
                    counter += 1
                    name_parts = base_name.rsplit('.', 1)
                    if len(name_parts) == 2:
                        secure_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        secure_filename = f"{base_name}_{counter}"
                
                # Copy image to secure location
                destination = secure_path_join(config.IMAGES_DIR, secure_filename)
                shutil.copy2(image_path, destination)
                
                # Set secure permissions
                destination.chmod(0o600)  # Owner read/write only
                
                # Get file info
                file_stat = destination.stat()
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(str(destination))
                
                # Create database entry
                new_image = Image(
                    filename=secure_filename,
                    file_hash=file_hash,
                    file_size=file_stat.st_size,
                    mime_type=mime_type,
                    description=sanitize_text_input(description),
                    is_active=True,
                    is_sent=False
                )
                
                session.add(new_image)
                session.commit()
                
                return True, f"Added successfully as {secure_filename}"
                
        except Exception as e:
            logger.error(f"Error adding image {image_path}: {e}")
            return False, f"Error: {str(e)}"
    
    def add_batch(
        self, 
        image_paths: List[Path], 
        descriptions: List[str],
        skip_existing: bool = True
    ):
        """
        Add multiple images in batch.
        
        Args:
            image_paths: List of image paths
            descriptions: List of descriptions (must match image_paths length)
            skip_existing: Skip existing images
        """
        if len(image_paths) != len(descriptions):
            raise ValueError("Number of images must match number of descriptions")
        
        total = len(image_paths)
        print(f"\n=== Adding {total} images ===\n")
        
        for i, (path, desc) in enumerate(zip(image_paths, descriptions), 1):
            print(f"\n[{i}/{total}] {path.name}")
            
            success, message = self.add_single_image(path, desc, skip_existing)
            self.processed += 1
            
            if success:
                self.succeeded += 1
                self._print_progress(message, "SUCCESS")
            else:
                if "already exists" in message:
                    self.skipped += 1
                    self._print_progress(message, "WARNING")
                else:
                    self.failed += 1
                    self._print_progress(message, "ERROR")
        
        # Print summary
        print(f"\n=== Summary ===")
        print(f"Total processed: {self.processed}")
        print(f"✓ Succeeded: {self.succeeded}")
        print(f"⚠ Skipped: {self.skipped}")
        print(f"✗ Failed: {self.failed}")


@click.command()
@click.option(
    '--image', '-i',
    type=click.Path(exists=True, path_type=Path),
    help='Path to image file'
)
@click.option(
    '--description', '-d',
    help='Description for the image'
)
@click.option(
    '--directory', '-D',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help='Directory containing images to add'
)
@click.option(
    '--descriptions-file', '-f',
    type=click.Path(exists=True, path_type=Path),
    help='File containing descriptions (one per line, matching directory order)'
)
@click.option(
    '--skip-existing/--update-existing',
    default=True,
    help='Skip or update existing images'
)
def main(image, description, directory, descriptions_file, skip_existing):
    """Add images to Ricky database."""
    adder = ImageAdder()
    
    try:
        if image and description:
            # Single image mode
            success, message = adder.add_single_image(
                image, description, skip_existing
            )
            if success:
                adder._print_progress(message, "SUCCESS")
            else:
                adder._print_progress(message, "ERROR")
                sys.exit(1)
        
        elif directory:
            # Batch mode
            # Get all image files
            image_extensions = {f".{ext}" for ext in config.ALLOWED_IMAGE_EXTENSIONS}
            image_files = sorted([
                f for f in directory.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ])
            
            if not image_files:
                print(f"No image files found in {directory}")
                sys.exit(1)
            
            # Get descriptions
            descriptions = []
            if descriptions_file:
                with open(descriptions_file, 'r') as f:
                    descriptions = [line.strip() for line in f if line.strip()]
                
                if len(descriptions) != len(image_files):
                    print(f"Error: Found {len(image_files)} images but {len(descriptions)} descriptions")
                    print("\nImages found:")
                    for img in image_files:
                        print(f"  - {img.name}")
                    sys.exit(1)
            else:
                # Prompt for descriptions
                print(f"Found {len(image_files)} images. Please provide descriptions:\n")
                for img in image_files:
                    desc = click.prompt(f"Description for {img.name}")
                    descriptions.append(desc)
            
            # Add images
            adder.add_batch(image_files, descriptions, skip_existing)
        
        else:
            # Interactive mode
            while True:
                print("\n=== Add Image (Ctrl+C to exit) ===")
                
                image_path = click.prompt("Image path", type=click.Path(exists=True, path_type=Path))
                description = click.prompt("Description")
                
                success, message = adder.add_single_image(
                    Path(image_path), description, skip_existing
                )
                
                if success:
                    adder._print_progress(message, "SUCCESS")
                else:
                    adder._print_progress(message, "ERROR")
                
                if not click.confirm("\nAdd another image?"):
                    break
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        logger.error(f"Add image error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 