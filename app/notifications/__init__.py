"""Email notifications module."""

from app.notifications.notifications import send_job_completion_email, send_welcome_email
from app.notifications.service import EmailService, EmailServiceError, get_email_service

__all__ = [
    # Service
    "EmailService",
    "EmailServiceError",
    "get_email_service",
    # Notification helpers
    "send_job_completion_email",
    "send_welcome_email",
]
