"""Tests for notification helpers."""

from unittest.mock import AsyncMock, patch

import pytest


class TestJobCompletionEmail:
    """Test job completion notification email."""

    @pytest.mark.asyncio
    async def test_send_job_completion_email_success(self):
        """Test sending job completion email for successful job."""
        from app.notifications.notifications import send_job_completion_email

        with patch("app.notifications.notifications.get_email_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_template_email.return_value = True
            mock_get.return_value = mock_service

            result = await send_job_completion_email(
                user_email="user@example.com",
                job_id=123,
                task_name="extract_pdf",
                status="completed",
                processing_time=45.7,
                result='{"status": "success"}',
            )

            assert result is True
            mock_service.send_template_email.assert_called_once()
            call_kwargs = mock_service.send_template_email.call_args.kwargs

            assert call_kwargs["to_email"] == "user@example.com"
            assert "Job #123" in call_kwargs["subject"]
            assert call_kwargs["template_name"] == "job_complete"
            assert call_kwargs["job_id"] == 123
            assert call_kwargs["status"] == "completed"
            assert call_kwargs["processing_time"] == 45.7

    @pytest.mark.asyncio
    async def test_send_job_completion_email_failed(self):
        """Test sending job completion email for failed job."""
        from app.notifications.notifications import send_job_completion_email

        with patch("app.notifications.notifications.get_email_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_template_email.return_value = True
            mock_get.return_value = mock_service

            result = await send_job_completion_email(
                user_email="user@example.com",
                job_id=456,
                task_name="process_extraction",
                status="failed",
                error="File not found",
            )

            assert result is True
            call_kwargs = mock_service.send_template_email.call_args.kwargs

            assert call_kwargs["status"] == "failed"
            assert call_kwargs["error"] == "File not found"
            assert call_kwargs["result"] is None

    @pytest.mark.asyncio
    async def test_send_job_completion_email_rounds_time(self):
        """Test processing time is rounded to 2 decimal places."""
        from app.notifications.notifications import send_job_completion_email

        with patch("app.notifications.notifications.get_email_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_template_email.return_value = True
            mock_get.return_value = mock_service

            await send_job_completion_email(
                user_email="user@example.com",
                job_id=789,
                task_name="test_task",
                status="completed",
                processing_time=123.456789,
            )

            call_kwargs = mock_service.send_template_email.call_args.kwargs
            assert call_kwargs["processing_time"] == 123.46


class TestWelcomeEmail:
    """Test welcome email."""

    @pytest.mark.asyncio
    async def test_send_welcome_email_with_name(self):
        """Test sending welcome email with user name."""
        from app.notifications.notifications import send_welcome_email

        with patch("app.notifications.notifications.get_email_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_template_email.return_value = True
            mock_get.return_value = mock_service

            result = await send_welcome_email(
                user_email="newuser@example.com",
                user_name="John Doe",
            )

            assert result is True
            mock_service.send_template_email.assert_called_once()
            call_kwargs = mock_service.send_template_email.call_args.kwargs

            assert call_kwargs["to_email"] == "newuser@example.com"
            assert "Welcome" in call_kwargs["subject"]
            assert call_kwargs["template_name"] == "welcome"
            assert call_kwargs["user_name"] == "John Doe"
            assert call_kwargs["user_email"] == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_send_welcome_email_without_name(self):
        """Test welcome email uses email prefix as name if name not provided."""
        from app.notifications.notifications import send_welcome_email

        with patch("app.notifications.notifications.get_email_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_template_email.return_value = True
            mock_get.return_value = mock_service

            result = await send_welcome_email(
                user_email="johndoe@example.com",
            )

            assert result is True
            call_kwargs = mock_service.send_template_email.call_args.kwargs

            # Should use email prefix as name
            assert call_kwargs["user_name"] == "johndoe"

    @pytest.mark.asyncio
    async def test_send_welcome_email_failure(self):
        """Test welcome email returns False on failure."""
        from app.notifications.notifications import send_welcome_email

        with patch("app.notifications.notifications.get_email_service") as mock_get:
            mock_service = AsyncMock()
            mock_service.send_template_email.return_value = False
            mock_get.return_value = mock_service

            result = await send_welcome_email(
                user_email="test@example.com",
            )

            assert result is False
