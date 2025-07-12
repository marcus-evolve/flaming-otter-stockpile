"""
Forms for the Ricky web application.
Implements secure form handling with CSRF protection.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, TextAreaField, BooleanField, 
    IntegerField, SubmitField, SelectField
)
from wtforms.validators import (
    DataRequired, Length, EqualTo, ValidationError, 
    NumberRange, Optional
)


class LoginForm(FlaskForm):
    """Login form with security features."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=128)
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ImageUploadForm(FlaskForm):
    """Form for uploading new images."""
    image = FileField('Image File', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=1, max=1000)
    ])
    submit = SubmitField('Upload Image')


class ImageEditForm(FlaskForm):
    """Form for editing image descriptions."""
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=1, max=1000)
    ])
    is_active = BooleanField('Active')
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=500)
    ])
    submit = SubmitField('Update Image')


class TestMessageForm(FlaskForm):
    """Form for sending test messages."""
    image_id = SelectField('Select Image', coerce=int, validators=[
        DataRequired()
    ])
    submit = SubmitField('Send Test Message')


class ScheduleControlForm(FlaskForm):
    """Form for controlling the scheduler."""
    action = SelectField('Action', choices=[
        ('start', 'Start Scheduler'),
        ('stop', 'Stop Scheduler'),
        ('reschedule', 'Force Reschedule')
    ], validators=[DataRequired()])
    submit = SubmitField('Execute')


class SettingsForm(FlaskForm):
    """Form for updating application settings."""
    min_interval_hours = IntegerField('Minimum Interval (hours)', validators=[
        DataRequired(),
        NumberRange(min=1, max=168)  # 1 hour to 1 week
    ])
    max_interval_hours = IntegerField('Maximum Interval (hours)', validators=[
        DataRequired(),
        NumberRange(min=2, max=720)  # 2 hours to 30 days
    ])
    recipient_phone = StringField('Recipient Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=20)
    ])
    submit = SubmitField('Update Settings')
    
    def validate_max_interval_hours(self, field):
        """Ensure max interval is greater than min interval."""
        if field.data <= self.min_interval_hours.data:
            raise ValidationError('Maximum interval must be greater than minimum interval')


class CreateUserForm(FlaskForm):
    """Form for creating new users (admin only)."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=128)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    is_admin = BooleanField('Administrator')
    submit = SubmitField('Create User')


class ChangePasswordForm(FlaskForm):
    """Form for changing user password."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired()
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, max=128)
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')


class BulkActionForm(FlaskForm):
    """Form for bulk actions on images."""
    action = SelectField('Action', choices=[
        ('activate', 'Activate Selected'),
        ('deactivate', 'Deactivate Selected'),
        ('reset_sent', 'Reset Sent Status'),
        ('delete', 'Delete Selected')
    ], validators=[DataRequired()])
    confirm = BooleanField('I understand this action cannot be undone', validators=[
        DataRequired()
    ])
    submit = SubmitField('Execute Bulk Action') 