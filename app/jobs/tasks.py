"""Task definitions for background jobs."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# Task registry: task_name -> async function
TASK_REGISTRY: dict[str, Callable[..., Awaitable[Any]]] = {}


def register_task(name: str):
    """Decorator to register a task.

    Args:
        name: Task name

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """Register task function.

        Args:
            func: Async function to register

        Returns:
            Original function
        """
        TASK_REGISTRY[name] = func
        logger.debug("Registered task", extra={"task_name": name})
        return func

    return decorator


@register_task("example_task")
async def example_task(message: str = "Hello") -> dict[str, str]:
    """Example task for testing.

    Args:
        message: Message to return

    Returns:
        Task result
    """
    logger.info("Running example task", extra={"message": message})
    await asyncio.sleep(1)  # Simulate work
    return {"status": "success", "message": message}


@register_task("long_running_task")
async def long_running_task(duration: int = 5) -> dict[str, Any]:
    """Long running task for testing.

    Args:
        duration: How long to run (seconds)

    Returns:
        Task result
    """
    logger.info("Running long task", extra={"duration": duration})
    await asyncio.sleep(duration)
    return {"status": "completed", "duration": duration}


@register_task("failing_task")
async def failing_task(error_message: str = "Task failed") -> dict:
    """Task that always fails (for testing).

    Args:
        error_message: Error message to raise

    Raises:
        RuntimeError: Always raised
    """
    logger.info("Running failing task")
    raise RuntimeError(error_message)


@register_task("process_extraction")
async def process_extraction(file_path: str, options: dict | None = None) -> dict:
    """Process document extraction (placeholder).

    Args:
        file_path: Path to file to extract
        options: Optional extraction options

    Returns:
        Extraction results
    """
    logger.info(
        "Processing extraction",
        extra={"file_path": file_path, "options": options},
    )

    # TODO: Integrate with extraction service
    await asyncio.sleep(2)  # Simulate work

    return {
        "status": "completed",
        "file_path": file_path,
        "extracted_items": 10,
    }


@register_task("generate_consolidation")
async def generate_consolidation(
    statement_id: int,
    export_format: str = "excel",
) -> dict:
    """Generate consolidation export (placeholder).

    Args:
        statement_id: Consolidated statement ID
        export_format: Export format (excel, csv, pdf)

    Returns:
        Export results
    """
    logger.info(
        "Generating consolidation",
        extra={"statement_id": statement_id, "format": export_format},
    )

    # TODO: Integrate with consolidation service
    await asyncio.sleep(3)  # Simulate work

    return {
        "status": "completed",
        "statement_id": statement_id,
        "format": export_format,
        "file_url": f"/exports/consolidation_{statement_id}.{export_format}",
    }


@register_task("batch_process")
async def batch_process(file_ids: list[int]) -> dict:
    """Process multiple files in batch (placeholder).

    Args:
        file_ids: List of file IDs to process

    Returns:
        Batch processing results
    """
    logger.info("Running batch process", extra={"file_count": len(file_ids)})

    results = []
    for file_id in file_ids:
        await asyncio.sleep(0.5)  # Simulate work
        results.append({"file_id": file_id, "status": "processed"})

    return {
        "status": "completed",
        "processed": len(file_ids),
        "results": results,
    }
