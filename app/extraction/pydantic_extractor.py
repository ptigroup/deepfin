"""Pydantic AI-based financial data extractor.

This module uses Pydantic AI to extract structured financial data from LLMWhisperer
raw text output. Replaces the DirectParser which expected pipe-separated format.

Benefits over DirectParser:
- Works with any text format (space-preserved, pipe-separated, etc.)
- Type-safe extraction with Pydantic validation
- Automatic retry and error handling
- No fragile regex/parsing code
"""

import os
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.core.logging import get_logger

logger = get_logger(__name__)


# Simplified schemas for Pydantic AI extraction
class FinancialLineItem(BaseModel):
    """A single line item in a financial statement."""

    account_name: str = Field(
        description="Account name exactly as shown, preserving all spacing and formatting"
    )
    values: list[str] = Field(
        description="Values for each period, in order, exactly as shown with $ and commas"
    )
    indent_level: int = Field(
        default=0, description="Indentation level (0=main item, 1-5=sub-items)"
    )


class FinancialStatement(BaseModel):
    """Complete financial statement extraction."""

    company_name: str = Field(description="Company name from the document")
    statement_type: str = Field(
        description="Type: income_statement, balance_sheet, cash_flow, comprehensive_income, or shareholders_equity"
    )
    fiscal_year: str | None = Field(
        None, description="Primary fiscal year if mentioned (e.g., '2020')"
    )
    currency: str = Field(default="USD", description="Currency code (default USD)")
    periods: list[str] = Field(
        description="Column headers for time periods (e.g., 'January 26, 2020', 'January 27, 2019')"
    )
    line_items: list[FinancialLineItem] = Field(
        description="All financial line items with their values"
    )


class PydanticExtractor:
    """Extract financial data using Pydantic AI."""

    def __init__(self):
        """Initialize the Pydantic AI extractor."""
        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Create Pydantic AI agent
        self.agent = Agent(
            "openai:gpt-4o-mini",
            output_type=FinancialStatement,
            system_prompt="""You are a financial data extraction expert.

Your task: Extract financial statement data from raw text.

CRITICAL RULES:
1. Preserve exact account names including ALL spacing and indentation
2. Preserve exact values including $ signs, commas, parentheses, decimals
3. Detect indentation level (0=top level, 1-5=nested items)
4. Extract column headers exactly as shown for periods
5. Identify statement type automatically
6. Extract company name and fiscal year

Example:
Raw text:
    Revenue                                    $  10,918    $  11,716
        Cost of revenue                            4,150        4,545
    Gross profit                                   6,768        7,171

Extract as:
- Account: "Revenue", values: ["$  10,918", "$  11,716"], indent: 0
- Account: "    Cost of revenue", values: ["4,150", "4,545"], indent: 1
- Account: "Gross profit", values: ["6,768", "7,171"], indent: 0

Do NOT:
- Modify account names or remove spacing
- Reformat numbers or remove symbols
- Make assumptions about data structure
""",
        )

        logger.info("PydanticExtractor initialized with gpt-4o-mini")

    def extract_from_text(self, raw_text: str) -> dict[str, Any]:
        """Extract structured financial data from raw LLMWhisperer text.

        Args:
            raw_text: Raw extracted text from LLMWhisperer

        Returns:
            Dictionary with extracted financial statement data

        Raises:
            Exception: If extraction fails after retries
        """
        logger.info(
            "Starting Pydantic AI extraction", extra={"text_length": len(raw_text)}
        )

        try:
            # Run the agent synchronously
            result = self.agent.run_sync(
                f"Extract financial statement data from this text:\n\n{raw_text}"
            )

            # Get the validated data
            financial_data = result.output

            logger.info(
                "Extraction successful",
                extra={
                    "company": financial_data.company_name,
                    "type": financial_data.statement_type,
                    "periods": len(financial_data.periods),
                    "line_items": len(financial_data.line_items),
                },
            )

            # Return as dictionary
            return financial_data.model_dump()

        except Exception as e:
            logger.error(
                "Extraction failed", extra={"error": str(e)}, exc_info=True
            )
            raise


def extract_financial_data(raw_text: str) -> dict[str, Any]:
    """Convenience function to extract financial data.

    Args:
        raw_text: Raw extracted text from LLMWhisperer

    Returns:
        Dictionary with extracted financial statement data
    """
    extractor = PydanticExtractor()
    return extractor.extract_from_text(raw_text)
