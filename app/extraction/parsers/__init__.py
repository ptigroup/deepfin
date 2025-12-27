"""
Direct parsers for financial statements.

These parsers extract data directly from LLMWhisperer's pipe-separated output
without LLM interpretation, ensuring 100% data accuracy.

Ported from brownfield/parsers for hybrid architecture.
"""

from .income_statement_parser import parse_income_statement_directly

__all__ = ["parse_income_statement_directly"]
