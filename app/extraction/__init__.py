"""Financial data extraction module.

This module provides models and schemas for extracting financial data from PDFs.
It serves as an intermediate layer between raw PDF text and permanent statement records.

The extraction workflow:
1. Create ExtractionJob to track the processing
2. Extract text using LLMWhisperer
3. Parse text into ExtractedStatement and ExtractedLineItem records
4. Validate and convert to permanent Statement records

Models:
- ExtractionJob: Tracks PDF processing jobs
- ExtractedStatement: Intermediate extracted statement data
- ExtractedLineItem: Individual extracted line items with hierarchy

Schemas:
- Complex validation rules for financial data
- Hierarchical structure support
- Date and currency validation
"""

from app.extraction.models import (
    ExtractedLineItem,
    ExtractedStatement,
    ExtractionJob,
    ExtractionStatus,
    StatementType,
)

__all__ = [
    "ExtractionJob",
    "ExtractedStatement",
    "ExtractedLineItem",
    "ExtractionStatus",
    "StatementType",
]
