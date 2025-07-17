"""
Flask web application for Ricky.
Provides web interface for managing images and controlling the scheduler.
"""

import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from typing import Optional

from flask import (
    Flask, render_template, redirect, url_for, flash, request,
    jsonify, send_from_directory, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, 
    current_user
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

from ..utils.config import config
from ..utils.logger import logger, security_logger
from ..utils.security import (
    validate_image_file, generate_secure_filename,
    calculate_file_hash, secure_path_join, sanitize_text_input
)
from ..models import get_db_session, Image, User, init_db
from ..services import TwilioService, RandomScheduler
from .forms import (
    LoginForm, ImageUploadForm, ImageEditForm, TestMessageForm,
    ScheduleControlForm, SettingsForm, CreateUserForm, 
    ChangePasswordForm, BulkActionForm
)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='../../templates',
                static_folder='../../static')
    
    # Configure app
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_IMAGE_SIZE_BYTES
    app.config['UPLOAD_FOLDER'] = str(config.IMAGES_DIR)
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Add config to all templates
    @app.context_processor
    def inject_config():
        return dict(config=config)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        with get_db_session() as session:
            user = session.query(User).get(int(user_id))
            if user:
                # Expunge the user from the session to prevent DetachedInstanceError
                session.expunge(user)
            return user
    
    # Initialize database
    init_db()
    
    # Create scheduler instance (singleton)
    app.scheduler = None
    
    # Admin required decorator
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.is_admin:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    
    # Routes
    @app.route('/')
    @login_required
    def index():
        """Dashboard showing system status and statistics."""
        with get_db_session() as session:
            total_images = session.query(Image).count()
            active_images = session.query(Image).filter_by(is_active=True).count()
            sent_images = session.query(Image).filter_by(is_sent=True).count()
            
            # Get recent activity
            recent_images = session.query(Image).filter(
                Image.last_sent.isnot(None)
            ).order_by(Image.last_sent.desc()).limit(5).all()
            
            # Scheduler status
            scheduler_running = app.scheduler is not None and app.scheduler.scheduler.running
            next_send_time = None
            if scheduler_running:
                next_send_time = app.scheduler.get_next_scheduled_time()
            
            return render_template('dashboard.html',
                total_images=total_images,
                active_images=active_images,
                sent_images=sent_images,
                recent_images=recent_images,
                scheduler_running=scheduler_running,
                next_send_time=next_send_time
            )
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            with get_db_session() as session:
                user = session.query(User).filter_by(
                    username=form.username.data
                ).first()
                
                if user and not user.is_locked() and user.check_password(form.password.data):
                    user.record_login()
                    session.commit()
                    
                    login_user(user, remember=form.remember_me.data)
                    security_logger.log_auth_attempt(True, f"User {user.username} logged in")
                    
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('index')
                    
                    return redirect(next_page)
                else:
                    if user:
                        user.record_failed_login()
                        session.commit()
                        
                        if user.is_locked():
                            flash('Account locked due to too many failed attempts. Try again later.', 'error')
                        else:
                            flash('Invalid username or password', 'error')
                    else:
                        flash('Invalid username or password', 'error')
                    
                    security_logger.log_auth_attempt(False, f"Failed login for {form.username.data}")
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        """User logout."""
        username = current_user.username
        logout_user()
        security_logger.log_auth_attempt(True, f"User {username} logged out")
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    
    @app.route('/images')
    @login_required
    def images():
        """List all images with filtering and pagination."""
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        with get_db_session() as session:
            query = session.query(Image)
            
            # Apply filters
            status_filter = request.args.get('status')
            if status_filter == 'active':
                query = query.filter_by(is_active=True)
            elif status_filter == 'inactive':
                query = query.filter_by(is_active=False)
            elif status_filter == 'sent':
                query = query.filter_by(is_sent=True)
            elif status_filter == 'unsent':
                query = query.filter_by(is_sent=False)
            
            # Order by created date
            query = query.order_by(Image.created_at.desc())
            
            # Paginate
            total = query.count()
            images = query.offset((page - 1) * per_page).limit(per_page).all()
            
            total_pages = (total + per_page - 1) // per_page
            
            return render_template('images.html',
                images=images,
                page=page,
                total_pages=total_pages,
                total=total,
                status_filter=status_filter
            )
    
    @app.route('/images/add', methods=['GET', 'POST'])
    @login_required
    def add_image():
        """Add new image."""
        form = ImageUploadForm()
        
        if form.validate_on_submit():
            file = form.image.data
            description = sanitize_text_input(form.description.data)
            
            # Save uploaded file temporarily
            temp_filename = secure_filename(file.filename)
            temp_path = Path(app.config['UPLOAD_FOLDER']) / f"temp_{temp_filename}"
            file.save(str(temp_path))
            
            try:
                # Validate image
                is_valid, error_msg = validate_image_file(
                    temp_path,
                    config.MAX_IMAGE_SIZE_BYTES
                )
                
                if not is_valid:
                    flash(f'Invalid image: {error_msg}', 'error')
                    return redirect(url_for('add_image'))
                
                # Calculate hash
                file_hash = calculate_file_hash(temp_path)
                
                with get_db_session() as session:
                    # Check if already exists
                    existing = session.query(Image).filter_by(
                        file_hash=file_hash
                    ).first()
                    
                    if existing:
                        flash('Image already exists in database', 'warning')
                        return redirect(url_for('images'))
                    
                    # Generate secure filename
                    secure_name = generate_secure_filename(file.filename)
                    final_path = secure_path_join(config.IMAGES_DIR, secure_name)
                    
                    # Move to final location
                    temp_path.rename(final_path)
                    final_path.chmod(0o600)
                    
                    # Create database entry
                    new_image = Image(
                        filename=secure_name,
                        file_hash=file_hash,
                        file_size=final_path.stat().st_size,
                        mime_type=file.content_type,
                        description=description,
                        is_active=True,
                        is_sent=False
                    )
                    
                    session.add(new_image)
                    session.commit()
                    
                    security_logger.log_image_access(new_image.id, "created")
                    flash('Image uploaded successfully!', 'success')
                    
                    return redirect(url_for('images'))
                    
            finally:
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()
        
        return render_template('add_image.html', form=form)
    
    @app.route('/images/<int:image_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_image(image_id):
        """Edit image details."""
        with get_db_session() as session:
            image = session.query(Image).get(image_id)
            if not image:
                abort(404)
            
            form = ImageEditForm(obj=image)
            
            if form.validate_on_submit():
                image.description = sanitize_text_input(form.description.data)
                image.is_active = form.is_active.data
                image.notes = sanitize_text_input(form.notes.data) if form.notes.data else None
                
                session.commit()
                security_logger.log_image_access(image_id, "edited")
                
                flash('Image updated successfully!', 'success')
                return redirect(url_for('images'))
            
            return render_template('edit_image.html', form=form, image=image)
    
    @app.route('/images/<int:image_id>/delete', methods=['POST'])
    @login_required
    def delete_image(image_id):
        """Delete an image."""
        with get_db_session() as session:
            image = session.query(Image).get(image_id)
            if not image:
                abort(404)
            
            filename = image.filename
            filepath = config.IMAGES_DIR / filename
            
            # Delete from database
            session.delete(image)
            session.commit()
            
            # Delete file
            if filepath.exists():
                filepath.unlink()
            
            security_logger.log_image_access(image_id, "deleted")
            flash('Image deleted successfully!', 'success')
            
        return redirect(url_for('images'))
    
    @app.route('/images/<int:image_id>/thumbnail')
    def image_thumbnail(image_id):
        """Serve image thumbnail."""
        with get_db_session() as session:
            image = session.query(Image).get(image_id)
            if not image:
                abort(404)
            
            # For now, serve the full image
            # In production, generate and cache thumbnails
            return send_from_directory(
                config.IMAGES_DIR,
                image.filename,
                mimetype=image.mime_type
            )
    
    @app.route('/images/<int:image_id>/<filename>')
    def image_by_filename(image_id, filename):
        """Serve image by ID and filename (for Twilio media URLs)."""
        # Log the incoming request
        logger.info(f"Image request: id={image_id}, filename={filename}, headers={dict(request.headers)}")
        
        with get_db_session() as session:
            image = session.query(Image).get(image_id)
            if not image:
                logger.error(f"Image {image_id} not found")
                abort(404)
            
            # Verify filename matches (security check)
            if image.filename != filename:
                logger.error(f"Filename mismatch: expected {image.filename}, got {filename}")
                abort(404)
            
            # Check if file exists
            file_path = config.IMAGES_DIR / image.filename
            if not file_path.exists():
                logger.error(f"Image file not found: {file_path}")
                abort(404)
            
            # Serve the image with appropriate headers
            response = send_from_directory(
                config.IMAGES_DIR,
                image.filename,
                mimetype=image.mime_type
            )
            
            # Add cache control headers
            response.headers['Cache-Control'] = 'public, max-age=3600'
            
            logger.info(f"Serving image: {image.filename} with mimetype: {image.mime_type}")
            return response
    
    @app.route('/scheduler', methods=['GET', 'POST'])
    @login_required
    def scheduler():
        """Scheduler control page."""
        form = ScheduleControlForm()
        
        if form.validate_on_submit():
            action = form.action.data
            
            if action == 'start':
                if not app.scheduler:
                    app.scheduler = RandomScheduler()
                    app.scheduler.start()
                    flash('Scheduler started successfully!', 'success')
                else:
                    flash('Scheduler is already running', 'info')
                    
            elif action == 'stop':
                if app.scheduler:
                    app.scheduler.stop()
                    app.scheduler = None
                    flash('Scheduler stopped successfully!', 'success')
                else:
                    flash('Scheduler is not running', 'info')
                    
            elif action == 'reschedule':
                if app.scheduler:
                    app.scheduler.force_reschedule()
                    flash('Rescheduled with new random interval!', 'success')
                else:
                    flash('Scheduler is not running', 'error')
            
            return redirect(url_for('scheduler'))
        
        # Get scheduler status
        scheduler_running = app.scheduler is not None and app.scheduler.scheduler.running
        next_send_time = None
        if scheduler_running:
            next_send_time = app.scheduler.get_next_scheduled_time()
        
        return render_template('scheduler.html',
            form=form,
            scheduler_running=scheduler_running,
            next_send_time=next_send_time
        )
    
    @app.route('/test-message', methods=['GET', 'POST'])
    @login_required
    def test_message():
        """Send test message."""
        form = TestMessageForm()
        
        # Populate image choices
        with get_db_session() as session:
            images = session.query(Image).filter_by(is_active=True).all()
            form.image_id.choices = [(img.id, f"{img.id}: {img.description[:50]}...") for img in images]
        
        if form.validate_on_submit():
            # Ensure the scheduler instance is created, which initializes the notification service
            scheduler_instance = RandomScheduler()
            
            success, message = scheduler_instance.send_test_message(form.image_id.data)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
            
            return redirect(url_for('test_message'))
        
        return render_template('test_message.html', form=form)
    
    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def settings():
        """Application settings (admin only)."""
        form = SettingsForm()
        
        if request.method == 'GET':
            # Populate form with current values
            form.min_interval_hours.data = config.MIN_INTERVAL_HOURS
            form.max_interval_hours.data = config.MAX_INTERVAL_HOURS
            form.recipient_phone.data = config.RECIPIENT_PHONE_NUMBER
        
        if form.validate_on_submit():
            # Update configuration
            # Note: In production, save these to a database or config file
            flash('Settings update requires application restart', 'warning')
            
            return redirect(url_for('settings'))
        
        return render_template('settings.html', form=form)
    
    @app.route('/users')
    @login_required
    @admin_required
    def users():
        """User management (admin only)."""
        with get_db_session() as session:
            users = session.query(User).order_by(User.created_at.desc()).all()
        
        return render_template('users.html', users=users)
    
    @app.route('/users/create', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def create_user():
        """Create new user (admin only)."""
        form = CreateUserForm()
        
        if form.validate_on_submit():
            with get_db_session() as session:
                # Check if username exists
                existing = session.query(User).filter_by(
                    username=form.username.data
                ).first()
                
                if existing:
                    flash('Username already exists', 'error')
                else:
                    user = User(
                        username=form.username.data,
                        is_admin=form.is_admin.data
                    )
                    user.set_password(form.password.data)
                    
                    session.add(user)
                    session.commit()
                    
                    flash('User created successfully!', 'success')
                    return redirect(url_for('users'))
        
        return render_template('create_user.html', form=form)
    
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """User profile and password change."""
        form = ChangePasswordForm()
        
        if form.validate_on_submit():
            with get_db_session() as session:
                user = session.query(User).get(current_user.id)
                
                if user.check_password(form.current_password.data):
                    user.set_password(form.new_password.data)
                    session.commit()
                    
                    flash('Password changed successfully!', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Current password is incorrect', 'error')
        
        return render_template('profile.html', form=form)
    
    @app.route('/api/stats')
    @login_required
    def api_stats():
        """API endpoint for live statistics."""
        with get_db_session() as session:
            stats = {
                'total_images': session.query(Image).count(),
                'active_images': session.query(Image).filter_by(is_active=True).count(),
                'sent_images': session.query(Image).filter_by(is_sent=True).count(),
                'scheduler_running': app.scheduler is not None and app.scheduler.scheduler.running,
                'next_send_time': None
            }
            
            if stats['scheduler_running']:
                next_time = app.scheduler.get_next_scheduled_time()
                if next_time:
                    stats['next_send_time'] = next_time.isoformat()
        
        return jsonify(stats)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        with get_db_session() as session:
            session.rollback()
        return render_template('500.html'), 500
    
    return app 