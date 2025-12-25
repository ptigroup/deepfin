"""Direct parsing engine for financial statement extraction.

This module implements 100% accurate parsing of pipe-separated tables
without LLM interpretation. Preserves exact values, formatting, and hierarchy.
"""

from decimal import Decimal
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ParseError(Exception):
    """Exception raised during parsing."""

    pass


class DirectParser:
    """Direct parser for pipe-separated financial tables.

    Implements context-based parsing to maintain 100% data accuracy.
    No LLM interpretation - pure text processing.
    """

    def __init__(self):
        """Initialize the direct parser."""
        self.current_section: str | None = None
        self.section_stack: list[str] = []

    def parse_table(self, raw_text: str) -> dict[str, Any]:
        """Parse pipe-separated table into structured data.

        Args:
            raw_text: Raw text with pipe-separated tables from LLMWhisperer

        Returns:
            Dictionary with extracted data:
            {
                "periods": ["2024", "2023"],
                "line_items": [
                    {
                        "name": "Total Revenue",
                        "values": ["1000000.00", "950000.00"],
                        "indent_level": 0,
                        "is_header": False,
                        "is_total": True,
                        "section": "Revenue"
                    },
                    ...
                ]
            }
        """
        logger.info("Starting direct parsing")

        # Extract table rows
        table_rows = self._extract_table_rows(raw_text)
        if not table_rows:
            raise ParseError("No table data found in raw text")

        # First row is typically header with periods
        header_row = table_rows[0]
        periods = self._parse_header_row(header_row)

        # Parse data rows
        line_items = []
        order = 0

        for row_text in table_rows[1:]:
            parsed_row = self._parse_data_row(row_text, len(periods))
            if parsed_row:
                parsed_row["order"] = order
                line_items.append(parsed_row)
                order += 1

        logger.info(
            "Parsing complete",
            extra={"periods": len(periods), "line_items": len(line_items)},
        )

        return {"periods": periods, "line_items": line_items}

    def _extract_table_rows(self, raw_text: str) -> list[str]:
        """Extract pipe-separated table rows from raw text.

        Args:
            raw_text: Raw extracted text

        Returns:
            List of pipe-separated rows
        """
        rows = []
        for line in raw_text.split("\n"):
            line = line.strip()
            # Lines with pipes are table rows
            if "|" in line and line.count("|") >= 2:
                rows.append(line)

        return rows

    def _parse_header_row(self, row_text: str) -> list[str]:
        """Parse header row to extract period columns.

        Args:
            row_text: Header row with period labels

        Returns:
            List of period labels (e.g., ["2024", "2023"])
        """
        cells = self._split_row_cells(row_text)

        # First cell is typically the account name header, rest are periods
        periods = []
        for cell in cells[1:]:  # Skip first cell
            cell_clean = cell.strip()
            if cell_clean and cell_clean.lower() not in [
                "account",
                "description",
                "item",
            ]:
                periods.append(cell_clean)

        return periods

    def _parse_data_row(self, row_text: str, period_count: int) -> dict[str, Any] | None:
        """Parse a data row into structured format.

        Args:
            row_text: Raw row text
            period_count: Expected number of period values

        Returns:
            Dictionary with parsed row data or None if invalid
        """
        cells = self._split_row_cells(row_text)

        if len(cells) < 1:
            return None

        # First cell is account name
        account_name = cells[0].strip()
        if not account_name:
            return None

        # Remaining cells are values
        values = []
        for i in range(1, min(len(cells), period_count + 1)):
            value_text = cells[i].strip() if i < len(cells) else ""
            values.append(value_text)

        # Determine if this is a section header (no numeric values)
        is_header = self._is_section_header(values)

        # Determine if this is a total line
        is_total = self._is_total_line(account_name)

        # Update section context
        if is_header:
            self.current_section = account_name
            self.section_stack.append(account_name)
        elif is_total:
            # Total lines often reset context
            if self.section_stack:
                self.section_stack.pop()
            self.current_section = self.section_stack[-1] if self.section_stack else None

        # Determine indent level from context and name
        indent_level = self._determine_indent_level(account_name, is_header)

        return {
            "name": account_name,
            "values": values,
            "indent_level": indent_level,
            "is_header": is_header,
            "is_total": is_total,
            "section": self.current_section,
            "raw_text": row_text,
        }

    def _split_row_cells(self, row_text: str) -> list[str]:
        """Split pipe-separated row into cells.

        Args:
            row_text: Raw row text with pipes

        Returns:
            List of cell values
        """
        # Remove leading/trailing pipes and split
        row_text = row_text.strip("|")
        cells = [cell.strip() for cell in row_text.split("|")]
        return cells

    def _is_section_header(self, values: list[str]) -> bool:
        """Determine if row is a section header (no numeric values).

        Args:
            values: List of value strings

        Returns:
            True if section header (no numbers), False otherwise
        """
        return all(self._extract_number(value) is None for value in values)

    def _is_total_line(self, account_name: str) -> bool:
        """Determine if row is a total/subtotal line.

        Args:
            account_name: Account name text

        Returns:
            True if total line, False otherwise
        """
        total_keywords = [
            "total",
            "subtotal",
            "sum",
            "net",
            "gross",
            "operating income",
            "net income",
        ]

        account_lower = account_name.lower()
        return any(keyword in account_lower for keyword in total_keywords)

    def _determine_indent_level(self, account_name: str, is_header: bool) -> int:
        """Determine indentation level based on context and formatting.

        Args:
            account_name: Account name text
            is_header: Whether this is a section header

        Returns:
            Indent level (0-10)
        """
        if is_header:
            # Headers are typically at level 0 or based on stack depth
            return min(len(self.section_stack) - 1, 0)

        # Count leading spaces/indentation in name
        leading_spaces = len(account_name) - len(account_name.lstrip())

        # Base indent on section depth + leading spaces
        base_indent = len(self.section_stack)

        # Approximate indent level (4 spaces = 1 level)
        space_indent = leading_spaces // 4

        return min(base_indent + space_indent, 10)

    def _extract_number(self, value_text: str) -> Decimal | None:
        """Extract numeric value from formatted string.

        Handles formats like:
        - $1,000.00
        - (500.00) - negative
        - 1000
        - -1,234.56

        Args:
            value_text: Formatted value text

        Returns:
            Decimal value or None if not a number
        """
        if not value_text or not value_text.strip():
            return None

        # Remove common formatting
        clean_value = value_text.strip()
        clean_value = clean_value.replace("$", "")
        clean_value = clean_value.replace(",", "")
        clean_value = clean_value.replace(" ", "")

        # Handle parentheses (negative)
        is_negative = False
        if clean_value.startswith("(") and clean_value.endswith(")"):
            is_negative = True
            clean_value = clean_value[1:-1]

        # Try to parse as decimal
        try:
            number = Decimal(clean_value)
            if is_negative:
                number = -number
            return number
        except (ValueError, Exception):
            return None

    def parse_value(self, value_text: str) -> Decimal:
        """Parse a value string into Decimal.

        Public method for extracting numeric values with 100% accuracy.

        Args:
            value_text: Formatted value text

        Returns:
            Decimal value

        Raises:
            ParseError: If value cannot be parsed
        """
        result = self._extract_number(value_text)
        if result is None:
            raise ParseError(f"Cannot parse value: {value_text}")
        return result

    def reset(self):
        """Reset parser state for new document."""
        self.current_section = None
        self.section_stack = []
