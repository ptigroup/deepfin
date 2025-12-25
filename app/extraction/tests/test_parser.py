"""Tests for direct parsing engine."""

from decimal import Decimal

import pytest

from app.extraction.parser import DirectParser, ParseError


class TestDirectParser:
    """Tests for DirectParser."""

    def test_parse_simple_table(self):
        """Test parsing a simple pipe-separated table."""
        raw_text = """
| Account | 2024 | 2023 |
| Total Revenue | 1,000,000 | 950,000 |
| Cost of Goods Sold | (600,000) | (570,000) |
| Gross Profit | 400,000 | 380,000 |
"""
        parser = DirectParser()
        result = parser.parse_table(raw_text)

        assert "periods" in result
        assert "line_items" in result
        assert len(result["periods"]) == 2
        assert result["periods"] == ["2024", "2023"]
        assert len(result["line_items"]) == 3

    def test_parse_header_row(self):
        """Test parsing header row with period labels."""
        parser = DirectParser()
        header = "| Account Name | FY 2024 | FY 2023 | FY 2022 |"

        periods = parser._parse_header_row(header)

        assert len(periods) == 3
        assert periods == ["FY 2024", "FY 2023", "FY 2022"]

    def test_parse_value_formats(self):
        """Test parsing various value formats."""
        parser = DirectParser()

        # Test different formats
        assert parser.parse_value("1,000.00") == Decimal("1000.00")
        assert parser.parse_value("$1,234.56") == Decimal("1234.56")
        assert parser.parse_value("(500.00)") == Decimal("-500.00")
        assert parser.parse_value("-1,000") == Decimal("-1000")
        assert parser.parse_value("123") == Decimal("123")

    def test_parse_value_error(self):
        """Test parsing invalid values raises error."""
        parser = DirectParser()

        with pytest.raises(ParseError):
            parser.parse_value("not a number")

        with pytest.raises(ParseError):
            parser.parse_value("")

    def test_identify_section_headers(self):
        """Test identifying section headers (no numeric values)."""
        parser = DirectParser()

        # Section headers have no numeric values
        assert parser._is_section_header(["Revenue", "", ""])
        assert parser._is_section_header(["Operating Expenses", "", ""])

        # Data rows have numeric values
        assert not parser._is_section_header(["Total Revenue", "1000", "900"])
        assert not parser._is_section_header(["", "500.00", "450.00"])

    def test_identify_total_lines(self):
        """Test identifying total/subtotal lines."""
        parser = DirectParser()

        # Total keywords
        assert parser._is_total_line("Total Revenue")
        assert parser._is_total_line("Subtotal Operating Expenses")
        assert parser._is_total_line("Net Income")
        assert parser._is_total_line("Gross Profit")

        # Not total lines
        assert not parser._is_total_line("Product Revenue")
        assert not parser._is_total_line("Salaries")

    def test_hierarchical_parsing(self):
        """Test parsing with hierarchical structure."""
        raw_text = """
| Account | 2024 |
| Revenue | |
|   Product Revenue | 750,000 |
|   Service Revenue | 250,000 |
| Total Revenue | 1,000,000 |
"""
        parser = DirectParser()
        result = parser.parse_table(raw_text)

        line_items = result["line_items"]

        # Check section header
        revenue_section = line_items[0]
        assert revenue_section["name"] == "Revenue"
        assert revenue_section["is_header"] is True
        assert revenue_section["section"] == "Revenue"

        # Check child items have section context
        product_item = line_items[1]
        assert product_item["section"] == "Revenue"
        assert product_item["is_header"] is False

    def test_indentation_levels(self):
        """Test indentation level determination."""
        raw_text = """
| Account | 2024 |
| Revenue | |
|   Product Revenue | 750,000 |
|     Hardware | 500,000 |
|     Software | 250,000 |
|   Service Revenue | 250,000 |
"""
        parser = DirectParser()
        result = parser.parse_table(raw_text)

        line_items = result["line_items"]

        # Revenue header should be level 0
        assert line_items[0]["indent_level"] >= 0

        # Product Revenue should be indented
        assert line_items[1]["indent_level"] > line_items[0]["indent_level"]

    def test_reset_context(self):
        """Test parser context reset."""
        parser = DirectParser()

        # Set some context
        parser.current_section = "Test Section"
        parser.section_stack = ["Section1", "Section2"]

        # Reset
        parser.reset()

        assert parser.current_section is None
        assert parser.section_stack == []

    def test_parse_negative_values(self):
        """Test parsing negative values in parentheses."""
        parser = DirectParser()

        # Parentheses indicate negative
        assert parser.parse_value("(1,000.00)") == Decimal("-1000.00")
        assert parser.parse_value("($500)") == Decimal("-500")
        assert parser.parse_value("(123.45)") == Decimal("-123.45")

    def test_parse_empty_values(self):
        """Test handling empty or whitespace values."""
        parser = DirectParser()

        # Empty values should return None
        assert parser._extract_number("") is None
        assert parser._extract_number("   ") is None
        assert parser._extract_number("-") is None

    def test_extract_number_with_formatting(self):
        """Test extracting numbers with various formatting."""
        parser = DirectParser()

        # Various formats
        assert parser._extract_number("$1,234,567.89") == Decimal("1234567.89")
        assert parser._extract_number("  500.00  ") == Decimal("500.00")
        assert parser._extract_number("1,000") == Decimal("1000")
        assert parser._extract_number("($1,000.00)") == Decimal("-1000.00")

    def test_parse_table_preserves_order(self):
        """Test that parsing preserves row order."""
        raw_text = """
| Account | 2024 |
| First Item | 100 |
| Second Item | 200 |
| Third Item | 300 |
"""
        parser = DirectParser()
        result = parser.parse_table(raw_text)

        line_items = result["line_items"]

        assert line_items[0]["order"] == 0
        assert line_items[1]["order"] == 1
        assert line_items[2]["order"] == 2
        assert line_items[0]["name"] == "First Item"
        assert line_items[2]["name"] == "Third Item"

    def test_parse_table_with_no_data(self):
        """Test parsing empty or invalid table raises error."""
        parser = DirectParser()

        # No pipe-separated data
        with pytest.raises(ParseError):
            parser.parse_table("This is not a table")

        # Empty string
        with pytest.raises(ParseError):
            parser.parse_table("")

    def test_parse_multi_period_table(self):
        """Test parsing table with multiple periods."""
        raw_text = """
| Account | Q4 2024 | Q3 2024 | Q2 2024 | Q1 2024 |
| Revenue | 300,000 | 250,000 | 275,000 | 175,000 |
"""
        parser = DirectParser()
        result = parser.parse_table(raw_text)

        assert len(result["periods"]) == 4
        assert result["periods"][0] == "Q4 2024"
        assert result["periods"][3] == "Q1 2024"

        # Values should include all periods
        assert len(result["line_items"][0]["values"]) == 4

    def test_parse_preserves_raw_text(self):
        """Test that raw text is preserved for each row."""
        raw_text = """
| Account | 2024 |
| Revenue | 1,000,000 |
"""
        parser = DirectParser()
        result = parser.parse_table(raw_text)

        line_item = result["line_items"][0]
        assert "raw_text" in line_item
        assert "Revenue" in line_item["raw_text"]
        assert "1,000,000" in line_item["raw_text"]
