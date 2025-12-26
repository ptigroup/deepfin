# LLMWhisperer Financial Document Processing Methodology

## Core Pipeline Architecture
**LLMWhisperer extraction → Direct Raw Text Parsing → Structured output (JSON + Excel)**

### Primary Processing Components

1. **LLMWhisperer Client**
   - Primary PDF text extraction using `LLMWhispererClient()`
   - Preserves exact document structure and formatting
   - Returns raw pipe-separated table format maintaining original layout
   - Includes fallback caching system for existing raw text files

2. **Document Type Detection System**
   - **Automatic Detection**: Keyword-based analysis to identify statement type
   - **Schema Selection**: Maps detected type to appropriate Pydantic schema
   - **Confidence Scoring**: Provides reliability metric for detection accuracy

3. **Direct Raw Text Parsing Engine** (Primary Method)
   - **Context-Based Processing**: Section header tracking for hierarchical structure
   - **Indentation Intelligence**: Determines indent levels from section context
   - **100% Data Accuracy**: Bypasses LLM interpretation for table data
   - **Pattern Recognition**: Extracts exact values and account names from pipe-separated format

4. **Schema-Based Excel Export**
   - **Visual Indentation**: Applies spacing based on indent levels (`"    " * indent_level`)
   - **Multi-Schema Support**: Handles different field structures (`line_items`, `accounts`, `equity_rows`)
   - **Original Formatting**: Preserves exact account names and number formatting

### Implementation Pattern

```python
def extract_text_from_pdf(file_path):
    # Check for existing raw text first (caching)
    existing_text = check_existing_raw_text(file_path)
    if existing_text:
        return existing_text
    
    # Fresh extraction if needed
    llmw = LLMWhispererClient()
    result = llmw.whisper(file_path=file_path)
    return result["extracted_text"]

def parse_with_direct_parsing(raw_text_path, schema_class):
    # Direct parsing based on document type
    if schema_class.__name__ == "IncomeStatementSchema":
        return parse_income_statement_directly(raw_text_path)
    elif schema_class.__name__ == "BalanceSheetSchema":
        return parse_balance_sheet_directly(raw_text_path)
    # Context-based hierarchical structure preservation
    return structured_data
```

### Context-Based Indentation System

```python
def parse_table_data(raw_text, reporting_periods):
    current_section = None  # Track section context
    
    for row in table_rows:
        # Section headers set context for following items
        if is_section_header_account(account_name):
            current_section = account_name
            continue  # Skip headers, use for context only
        
        # Determine indentation from current section
        indent_level = determine_indent_level_with_context(account_name, current_section)
        parent_section = get_parent_section_with_context(account_name, current_section)
        
        # Reset context after total lines
        if is_total_line_that_resets_context(account_name):
            current_section = None
```

## Universal Document Processing Principles

### Input Document Types
- **ANY financial table format**: Balance sheets, income statements, cash flow statements, P&L reports, bank statements, trial balances, etc.
- **ANY table structure**: Multi-column, single-column, nested hierarchies, various date formats
- **ANY account naming**: Assets, Liabilities, Revenue, Expenses, or any other financial line items

### Critical Processing Rules

1. **NEVER hardcode document assumptions**
   - Do NOT assume specific account names (Revenue, Assets, etc.)
   - Do NOT assume specific table structures (3-column, 4-column, etc.)
   - Do NOT assume specific date formats (years, quarters, months, etc.)

2. **Preserve exact extracted content through direct parsing**
   - Use direct raw text parsing to maintain 100% accuracy
   - Extract column headers EXACTLY as they appear in LLMWhisperer output
   - Maintain account names with original spacing, punctuation, and capitalization
   - Keep numbers EXACTLY as formatted (including $, commas, parentheses, decimals)
   - Preserve hierarchical relationships through context-based indentation

3. **Direct Parsing Implementation Requirements**
   - Process pipe-separated table format: `| Account Name | Value1 | Value2 |`
   - Identify section headers by absence of numerical values
   - Track current section context for proper indentation assignment
   - Reset context after total lines to prevent incorrect grouping
   - Apply visual indentation in Excel output: `"    " * indent_level`

4. **Schema-Based Processing**
   - Automatically detect document type using keyword analysis
   - Select appropriate Pydantic schema for validation
   - Handle different field structures across schema types
   - Support multiple output formats (JSON + Excel) from single schema

### Output Requirements
- **JSON**: Structured data following detected Pydantic schema with metadata
- **Excel**: Formatted spreadsheet with visual indentation and original structure
- **Raw Text Cache**: Preserved LLMWhisperer output for debugging and reprocessing
- **Detection Logs**: Document type detection details and confidence scores

### Debugging and Error Resolution
- **Empty Excel Output**: Check schema field mapping (`line_items` vs `accounts` vs `equity_rows`)
- **Missing Indentation**: Verify section header detection and context tracking logic
- **Incorrect Categorization**: Expand keyword lists for account categorization
- **Context Not Resetting**: Ensure total line detection resets section context

This methodology implements a direct parsing approach that ensures 100% data accuracy while maintaining universal compatibility with any financial document format through intelligent context-based processing.