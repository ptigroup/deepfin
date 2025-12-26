"""Tests for email service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.notifications.service import EmailService, EmailServiceError


class TestEmailService:
    """Test email service."""

    def test_init_disabled(self):
        """Test email service initializes when disabled."""
        with patch("app.notifications.service.settings") as mock_settings:
            mock_settings.email_enabled = False
            mock_settings.email_from = "test@example.com"

            service = EmailService()

            assert service.enabled is False
            assert service.from_email == "test@example.com"

    def test_init_enabled(self):
        """Test email service initializes when enabled."""
        with patch("app.notifications.service.settings") as mock_settings:
            mock_settings.email_enabled = True
            mock_settings.email_from = "noreply@example.com"

            service = EmailService()

            assert service.enabled is True
            assert service.from_email == "noreply@example.com"

    @pytest.mark.asyncio
    async def test_send_email_disabled(self):
        """Test sending email when service is disabled."""
        with patch("app.notifications.service.settings") as mock_settings:
            mock_settings.email_enabled = False
            mock_settings.email_from = "test@example.com"

            service = EmailService()

            result = await service.send_email(
                to_email="recipient@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending."""
        with patch("app.notifications.service.settings") as mock_settings:
            mock_settings.email_enabled = True
            mock_settings.email_from = "sender@example.com"
            mock_settings.smtp_host = "smtp.example.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_user = "user"
            mock_settings.smtp_password = "pass"

            service = EmailService()

            with patch("app.notifications.service.smtplib.SMTP") as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_server

                result = await service.send_email(
                    to_email="recipient@example.com",
                    subject="Test Subject",
                    html_body="<p>Test HTML</p>",
                    text_body="Test Text",
                )

                assert result is True
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once_with("user", "pass")
                mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_failure(self):
        """Test email sending handles errors gracefully."""
        with patch("app.notifications.service.settings") as mock_settings:
            mock_settings.email_enabled = True
            mock_settings.email_from = "sender@example.com"
            mock_settings.smtp_host = "smtp.example.com"
            mock_settings.smtp_port = 587

            service = EmailService()

            with patch("app.notifications.service.smtplib.SMTP") as mock_smtp:
                mock_smtp.side_effect = Exception("SMTP connection failed")

                result = await service.send_email(
                    to_email="recipient@example.com",
                    subject="Test",
                    html_body="<p>Test</p>",
                )

                assert result is False  # Should not raise, just return False

    def test_render_template_success(self):
        """Test template rendering with existing templates."""
        service = EmailService()

        html, text = service.render_template(
            "job_complete",
            job_id=123,
            task_name="test_task",
            status="completed",
            app_name="Test App",
            app_url="http://localhost",
        )

        assert "Job ID" in html or "123" in html
        assert "completed" in html.lower()
        assert "123" in text
        assert "completed" in text.lower()

    def test_render_template_missing(self):
        """Test rendering non-existent template raises error."""
        service = EmailService()

        with pytest.raises(EmailServiceError, match="Failed to render template"):
            service.render_template("nonexistent_template")

    def test_html_to_text(self):
        """Test HTML to text conversion."""
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Hello</h1>
                <p>This is a <strong>test</strong></p>
                <script>alert('test');</script>
            </body>
        </html>
        """

        text = EmailService._html_to_text(html)

        assert "Hello" in text
        assert "This is a test" in text
        assert "<" not in text
        assert ">" not in text
        assert "script" not in text

    @pytest.mark.asyncio
    async def test_send_template_email_success(self):
        """Test sending templated email."""
        with patch("app.notifications.service.settings") as mock_settings:
            mock_settings.email_enabled = True
            mock_settings.email_from = "sender@example.com"
            mock_settings.smtp_host = "smtp.example.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_user = None
            mock_settings.smtp_password = None

            service = EmailService()

            with patch("app.notifications.service.smtplib.SMTP") as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_server

                result = await service.send_template_email(
                    to_email="user@example.com",
                    subject="Job Complete",
                    template_name="job_complete",
                    job_id=456,
                    task_name="extract_pdf",
                    status="completed",
                    app_name="Test App",
                    app_url="http://localhost",
                )

                assert result is True
                mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_template_email_bad_template(self):
        """Test sending email with bad template returns False."""
        with patch("app.notifications.service.settings") as mock_settings:
            mock_settings.email_enabled = True

            service = EmailService()

            result = await service.send_template_email(
                to_email="user@example.com",
                subject="Test",
                template_name="bad_template_name_that_doesnt_exist",
            )

            assert result is False


class TestGetEmailService:
    """Test email service singleton."""

    def test_get_email_service_singleton(self):
        """Test get_email_service returns same instance."""
        from app.notifications.service import get_email_service

        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2

    def test_get_email_service_returns_instance(self):
        """Test get_email_service returns EmailService instance."""
        from app.notifications.service import get_email_service

        service = get_email_service()

        assert isinstance(service, EmailService)
