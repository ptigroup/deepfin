"""Tests for statements API routes."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.statements.models import LineItem, Statement, StatementType
from app.statements.service import StatementProcessingError

client = TestClient(app)


class TestStatementRoutes:
    """Tests for statement API routes."""

    @pytest.fixture
    def mock_statement(self):
        """Create a mock statement."""
        stmt = MagicMock(spec=Statement)
        stmt.id = 1
        stmt.statement_type = StatementType.INCOME_STATEMENT
        stmt.company_name = "Test Corp"
        stmt.period_start = "2024-01-01"
        stmt.period_end = "2024-12-31"
        stmt.currency = "USD"
        stmt.fiscal_year = 2024
        stmt.extra_metadata = None
        return stmt

    @patch("app.statements.routes.StatementService")
    def test_create_statement(self, mock_service_class):
        """Test POST /statements/ to create a statement."""
        # Mock service
        mock_service = AsyncMock()
        mock_service.create_statement.return_value = MagicMock(
            id=1,
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Test Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            fiscal_year=2024,
            currency="USD",
            extra_metadata=None,
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/statements/",
            json={
                "statement_type": "income_statement",
                "company_name": "Test Corp",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31",
                "fiscal_year": 2024,
                "currency": "USD",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Statement created successfully"

    @patch("app.statements.routes.StatementService")
    def test_get_statement(self, mock_service_class, mock_statement):
        """Test GET /statements/{id} to retrieve a statement."""
        mock_service = AsyncMock()
        mock_service.get_statement.return_value = mock_statement
        mock_service_class.return_value = mock_service

        response = client.get("/statements/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @patch("app.statements.routes.StatementService")
    def test_get_statement_not_found(self, mock_service_class):
        """Test GET /statements/{id} with non-existent statement."""
        mock_service = AsyncMock()
        mock_service.get_statement.return_value = None
        mock_service_class.return_value = mock_service

        response = client.get("/statements/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("app.statements.routes.StatementService")
    def test_get_statement_with_line_items(self, mock_service_class, mock_statement):
        """Test GET /statements/{id} with line items included."""
        mock_statement.line_items = []
        mock_service = AsyncMock()
        mock_service.get_statement.return_value = mock_statement
        mock_service_class.return_value = mock_service

        response = client.get("/statements/1?include_line_items=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @patch("app.statements.routes.StatementService")
    def test_list_statements(self, mock_service_class, mock_statement):
        """Test GET /statements/ to list statements."""
        mock_service = AsyncMock()
        mock_service.get_statements.return_value = [mock_statement, mock_statement]
        mock_service_class.return_value = mock_service

        response = client.get("/statements/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2

    @patch("app.statements.routes.StatementService")
    def test_list_statements_with_filters(self, mock_service_class, mock_statement):
        """Test GET /statements/ with query filters."""
        mock_service = AsyncMock()
        mock_service.get_statements.return_value = [mock_statement]
        mock_service_class.return_value = mock_service

        response = client.get(
            "/statements/?statement_type=income_statement&company_name=Test&fiscal_year=2024"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 1

    @patch("app.statements.routes.StatementService")
    def test_list_statements_with_pagination(self, mock_service_class):
        """Test GET /statements/ with pagination."""
        mock_service = AsyncMock()
        mock_service.get_statements.return_value = []
        mock_service_class.return_value = mock_service

        response = client.get("/statements/?limit=10&offset=20")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 0

    @patch("app.statements.routes.StatementService")
    def test_delete_statement(self, mock_service_class):
        """Test DELETE /statements/{id} to delete a statement."""
        mock_service = AsyncMock()
        mock_service.delete_statement.return_value = True
        mock_service_class.return_value = mock_service

        response = client.delete("/statements/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"].lower()

    @patch("app.statements.routes.StatementService")
    def test_delete_statement_not_found(self, mock_service_class):
        """Test DELETE /statements/{id} with non-existent statement."""
        mock_service = AsyncMock()
        mock_service.delete_statement.return_value = False
        mock_service_class.return_value = mock_service

        response = client.delete("/statements/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("app.statements.routes.StatementService")
    def test_add_line_item(self, mock_service_class):
        """Test POST /statements/{id}/line-items to add a line item."""
        mock_service = AsyncMock()
        mock_service.add_line_item.return_value = MagicMock(
            id=1,
            statement_id=1,
            line_item_name="Total Revenue",
            value=Decimal("1000000.00"),
            order=1,
            category="Revenue",
            indent_level=0,
            parent_id=None,
            notes=None,
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/statements/1/line-items",
            json={
                "statement_id": 1,  # Will be overridden by URL
                "line_item_name": "Total Revenue",
                "value": "1000000.00",
                "order": 1,
                "category": "Revenue",
                "indent_level": 0,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Line item added successfully"

    @patch("app.statements.routes.StatementService")
    def test_add_line_item_statement_not_found(self, mock_service_class):
        """Test POST /statements/{id}/line-items with non-existent statement."""
        mock_service = AsyncMock()
        mock_service.add_line_item.side_effect = StatementProcessingError("Statement 999 not found")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/statements/999/line-items",
            json={
                "statement_id": 999,
                "line_item_name": "Test",
                "value": "100.00",
                "order": 1,
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.statements.routes.StatementService")
    def test_get_line_items(self, mock_service_class):
        """Test GET /statements/{id}/line-items to get line items."""
        # Create properly configured mock line items
        mock_line_item_1 = MagicMock(spec=LineItem)
        mock_line_item_1.id = 1
        mock_line_item_1.statement_id = 1
        mock_line_item_1.line_item_name = "Total Revenue"
        mock_line_item_1.category = "Revenue"
        mock_line_item_1.value = Decimal("1000000.00")
        mock_line_item_1.indent_level = 0
        mock_line_item_1.order = 1
        mock_line_item_1.parent_id = None
        mock_line_item_1.notes = None

        mock_line_item_2 = MagicMock(spec=LineItem)
        mock_line_item_2.id = 2
        mock_line_item_2.statement_id = 1
        mock_line_item_2.line_item_name = "Product Revenue"
        mock_line_item_2.category = "Revenue"
        mock_line_item_2.value = Decimal("750000.00")
        mock_line_item_2.indent_level = 1
        mock_line_item_2.order = 2
        mock_line_item_2.parent_id = 1
        mock_line_item_2.notes = None

        mock_service = AsyncMock()
        mock_service.get_line_items.return_value = [mock_line_item_1, mock_line_item_2]
        mock_service_class.return_value = mock_service

        response = client.get("/statements/1/line-items")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2

    @patch("app.statements.routes.StatementService")
    def test_detect_statement_type(self, mock_service_class):
        """Test POST /statements/detect-type to detect statement type."""
        # Use MagicMock instead of AsyncMock since detect_statement_type is not async
        mock_service = MagicMock()
        mock_service.detect_statement_type.return_value = (
            StatementType.INCOME_STATEMENT,
            0.85,
        )
        mock_service_class.return_value = mock_service

        response = client.post("/statements/detect-type?text=Income Statement Revenue Net Income")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["statement_type"] == "income_statement"
        assert data["data"]["confidence"] == 0.85
