"""Tests for background tasks."""

import pytest

from app.jobs.tasks import (
    TASK_REGISTRY,
    batch_process,
    example_task,
    failing_task,
    generate_consolidation,
    long_running_task,
    process_extraction,
    register_task,
)


class TestTaskRegistry:
    """Test task registration system."""

    def test_task_registry_populated(self):
        """Test that task registry has registered tasks."""
        assert len(TASK_REGISTRY) > 0
        assert "example_task" in TASK_REGISTRY
        assert "long_running_task" in TASK_REGISTRY
        assert "failing_task" in TASK_REGISTRY

    def test_register_task_decorator(self):
        """Test task registration decorator."""

        @register_task("test_custom_task")
        async def custom_task():
            return {"result": "success"}

        assert "test_custom_task" in TASK_REGISTRY
        assert TASK_REGISTRY["test_custom_task"] == custom_task


class TestExampleTask:
    """Test example task."""

    @pytest.mark.asyncio
    async def test_example_task_default(self):
        """Test example task with default message."""
        result = await example_task()

        assert result["status"] == "success"
        assert result["message"] == "Hello"

    @pytest.mark.asyncio
    async def test_example_task_custom_message(self):
        """Test example task with custom message."""
        result = await example_task(message="Custom")

        assert result["status"] == "success"
        assert result["message"] == "Custom"


class TestLongRunningTask:
    """Test long running task."""

    @pytest.mark.asyncio
    async def test_long_running_task_default(self):
        """Test long running task with default duration."""
        result = await long_running_task(duration=0)  # 0 seconds for testing

        assert result["status"] == "completed"
        assert result["duration"] == 0

    @pytest.mark.asyncio
    async def test_long_running_task_custom_duration(self):
        """Test long running task with custom duration."""
        result = await long_running_task(duration=1)

        assert result["status"] == "completed"
        assert result["duration"] == 1


class TestFailingTask:
    """Test failing task."""

    @pytest.mark.asyncio
    async def test_failing_task_raises_error(self):
        """Test that failing task raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            await failing_task()

        assert "Task failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_failing_task_custom_message(self):
        """Test failing task with custom error message."""
        with pytest.raises(RuntimeError) as exc_info:
            await failing_task(error_message="Custom error")

        assert "Custom error" in str(exc_info.value)


class TestProcessExtraction:
    """Test extraction processing task."""

    @pytest.mark.asyncio
    async def test_process_extraction_basic(self):
        """Test basic extraction processing."""
        result = await process_extraction(file_path="/path/to/file.pdf")

        assert result["status"] == "completed"
        assert result["file_path"] == "/path/to/file.pdf"
        assert "extracted_items" in result

    @pytest.mark.asyncio
    async def test_process_extraction_with_options(self):
        """Test extraction with options."""
        options = {"format": "excel", "include_metadata": True}
        result = await process_extraction(file_path="/path/to/file.pdf", options=options)

        assert result["status"] == "completed"
        assert result["file_path"] == "/path/to/file.pdf"


class TestGenerateConsolidation:
    """Test consolidation generation task."""

    @pytest.mark.asyncio
    async def test_generate_consolidation_default(self):
        """Test consolidation generation with default format."""
        result = await generate_consolidation(statement_id=1)

        assert result["status"] == "completed"
        assert result["statement_id"] == 1
        assert result["format"] == "excel"
        assert "file_url" in result

    @pytest.mark.asyncio
    async def test_generate_consolidation_csv(self):
        """Test consolidation generation with CSV format."""
        result = await generate_consolidation(statement_id=2, export_format="csv")

        assert result["status"] == "completed"
        assert result["statement_id"] == 2
        assert result["format"] == "csv"
        assert ".csv" in result["file_url"]


class TestBatchProcess:
    """Test batch processing task."""

    @pytest.mark.asyncio
    async def test_batch_process_empty_list(self):
        """Test batch processing with empty list."""
        result = await batch_process(file_ids=[])

        assert result["status"] == "completed"
        assert result["processed"] == 0
        assert len(result["results"]) == 0

    @pytest.mark.asyncio
    async def test_batch_process_single_file(self):
        """Test batch processing with single file."""
        result = await batch_process(file_ids=[1])

        assert result["status"] == "completed"
        assert result["processed"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["file_id"] == 1

    @pytest.mark.asyncio
    async def test_batch_process_multiple_files(self):
        """Test batch processing with multiple files."""
        result = await batch_process(file_ids=[1, 2, 3])

        assert result["status"] == "completed"
        assert result["processed"] == 3
        assert len(result["results"]) == 3
        assert all(r["status"] == "processed" for r in result["results"])
