"""Integration tests for document processing workflow."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
class TestDocumentUploadWorkflow:
    """Test document upload and initial processing."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health endpoint is accessible."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_statement_creation_in_database(
        self,
        db_session: AsyncSession,
        sample_extraction_data: dict,
    ) -> None:
        """Test creating a financial statement in database."""
        from app.statements.models import Statement
        from app.statements.service import StatementService
        
        service = StatementService(db_session)
        
        # Create statement
        statement = await service.create_statement(
            statement_type=sample_extraction_data["statement_type"],
            company_name=sample_extraction_data["company_name"],
            fiscal_year=sample_extraction_data["fiscal_year"],
            raw_text=sample_extraction_data["raw_text"],
            structured_data=sample_extraction_data["structured_data"],
        )
        
        assert statement.id is not None
        assert statement.statement_type == "balance_sheet"
        assert statement.company_name == "Test Company Inc."
        assert statement.fiscal_year == 2024
