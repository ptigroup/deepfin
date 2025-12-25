"""Consolidation module for multi-period financial data aggregation."""

from app.consolidation.exporter import ConsolidationExporter, ExcelExportError
from app.consolidation.models import ConsolidatedStatement, PeriodComparison
from app.consolidation.routes import router
from app.consolidation.service import ConsolidationService, ConsolidationServiceError

__all__ = [
    "ConsolidatedStatement",
    "PeriodComparison",
    "ConsolidationService",
    "ConsolidationServiceError",
    "ConsolidationExporter",
    "ExcelExportError",
    "router",
]
