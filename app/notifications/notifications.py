"""Notification helpers for sending specific types of emails."""

from app.core.config import get_settings
from app.core.logging import get_logger
from app.notifications.service import get_email_service

logger = get_logger(__name__)
settings = get_settings()


async def send_job_completion_email(
    user_email: str,
    job_id: int,
    task_name: str,
    status: str,
    processing_time: float | None = None,
    result: str | None = None,
    error: str | None = None,
) -> bool:
    """Send job completion notification email.

    Args:
        user_email: Recipient email address
        job_id: Job ID
        task_name: Task name
        status: Job status (completed, failed, etc.)
        processing_time: Processing time in seconds
        result: Job result (if completed)
        error: Error message (if failed)

    Returns:
        True if email sent successfully, False otherwise

    Example:
        await send_job_completion_email(
            user_email="user@example.com",
            job_id=123,
            task_name="extract_pdf",
            status="completed",
            processing_time=45.2,
            result={"extraction_job_id": 456}
        )
    """
    email_service = get_email_service()

    subject = f"Job #{job_id} - {status.title()}"

    context = {
        "job_id": job_id,
        "task_name": task_name,
        "status": status,
        "processing_time": round(processing_time, 2) if processing_time else None,
        "result": result,
        "error": error,
        "app_name": settings.app_name,
        "app_url": "http://localhost:8123",  # TODO: Get from config
    }

    logger.info(
        "Sending job completion email",
        extra={
            "user_email": user_email,
            "job_id": job_id,
            "status": status,
        },
    )

    return await email_service.send_template_email(
        to_email=user_email,
        subject=subject,
        template_name="job_complete",
        **context,
    )


async def send_welcome_email(
    user_email: str,
    user_name: str | None = None,
) -> bool:
    """Send welcome email to new user.

    Args:
        user_email: User's email address
        user_name: User's name or username (optional)

    Returns:
        True if email sent successfully, False otherwise

    Example:
        await send_welcome_email(
            user_email="newuser@example.com",
            user_name="John Doe"
        )
    """
    email_service = get_email_service()

    subject = f"Welcome to {settings.app_name}!"

    # Use email as name if name not provided
    if not user_name:
        user_name = user_email.split("@")[0]

    context = {
        "user_name": user_name,
        "user_email": user_email,
        "app_name": settings.app_name,
        "app_url": "http://localhost:8123",  # TODO: Get from config
    }

    logger.info(
        "Sending welcome email",
        extra={"user_email": user_email},
    )

    return await email_service.send_template_email(
        to_email=user_email,
        subject=subject,
        template_name="welcome",
        **context,
    )
