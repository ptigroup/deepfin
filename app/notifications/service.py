"""Email notification service."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Configure Jinja2 environment for email templates
TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailServiceError(Exception):
    """Email service errors."""

    pass


class EmailService:
    """Service for sending email notifications.

    Handles:
    - SMTP connection and email sending
    - HTML and plain text email rendering
    - Jinja2 template rendering
    - Email queueing (future)
    """

    def __init__(self):
        """Initialize email service."""
        self.enabled = settings.email_enabled
        self.from_email = settings.email_from

        if not self.enabled:
            logger.info("Email service disabled (email_enabled=False)")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text email body (optional, falls back to stripping HTML)

        Returns:
            True if email sent successfully, False otherwise

        Raises:
            EmailServiceError: If email sending fails critically
        """
        if not self.enabled:
            logger.debug(
                "Email not sent (disabled)",
                extra={
                    "to": to_email,
                    "subject": subject,
                },
            )
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            # Add plain text version
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)

            # Add HTML version
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Send email via SMTP
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()

                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)

                server.send_message(message)

            logger.info(
                "Email sent successfully",
                extra={
                    "to": to_email,
                    "subject": subject,
                },
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to send email",
                extra={
                    "to": to_email,
                    "subject": subject,
                    "error": str(e),
                },
                exc_info=True,
            )
            # Don't raise exception - email failures shouldn't break the app
            return False

    def render_template(self, template_name: str, **context) -> tuple[str, str]:
        """Render email template with context.

        Args:
            template_name: Template filename (without extension)
            **context: Template variables

        Returns:
            Tuple of (html_body, text_body)

        Raises:
            EmailServiceError: If template rendering fails

        Example:
            html, text = email_service.render_template(
                "job_complete",
                user_name="John",
                job_id=123
            )
        """
        try:
            # Render HTML version
            html_template = jinja_env.get_template(f"{template_name}.html")
            html_body = html_template.render(**context)

            # Render text version (fallback to simple text if doesn't exist)
            try:
                text_template = jinja_env.get_template(f"{template_name}.txt")
                text_body = text_template.render(**context)
            except Exception:
                # If text template doesn't exist, create simple text version
                text_body = self._html_to_text(html_body)

            return html_body, text_body

        except Exception as e:
            logger.error(
                "Failed to render email template",
                extra={
                    "template": template_name,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EmailServiceError(f"Failed to render template: {str(e)}") from e

    async def send_template_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        **context,
    ) -> bool:
        """Render template and send email.

        Convenience method that combines template rendering and sending.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            template_name: Template filename (without extension)
            **context: Template variables

        Returns:
            True if email sent successfully, False otherwise

        Example:
            await email_service.send_template_email(
                to_email="user@example.com",
                subject="Job Complete",
                template_name="job_complete",
                user_name="John",
                job_id=123
            )
        """
        try:
            html_body, text_body = self.render_template(template_name, **context)
            return await self.send_email(to_email, subject, html_body, text_body)

        except EmailServiceError as e:
            logger.error(
                "Failed to send template email",
                extra={
                    "to": to_email,
                    "subject": subject,
                    "template": template_name,
                    "error": str(e),
                },
            )
            return False

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Convert HTML to plain text (simple version).

        Args:
            html: HTML string

        Returns:
            Plain text version (HTML tags stripped)
        """
        # Simple HTML to text conversion
        # For production, consider using html2text library
        import re

        text = re.sub("<head.*?>.*?</head>", "", html, flags=re.DOTALL)
        text = re.sub("<style.*?>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub("<script.*?>.*?</script>", "", text, flags=re.DOTALL)
        text = re.sub("<[^<]+?>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


# Global email service instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get global email service instance.

    Returns:
        Email service singleton
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
