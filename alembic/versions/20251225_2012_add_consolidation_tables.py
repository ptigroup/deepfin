"""add_consolidation_tables

Revision ID: 20251225_2012
Revises: 20251223_0000_51ede09ed895
Create Date: 2025-12-25 20:12:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251225_2012"
down_revision: Union[str, None] = "5d8c7e7b7f8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create consolidated_statements and period_comparisons tables."""
    # Create consolidated_statements table
    op.create_table(
        "consolidated_statements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("start_period", sa.String(), nullable=False),
        sa.Column("end_period", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("period_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_line_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create period_comparisons table
    op.create_table(
        "period_comparisons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consolidated_statement_id", sa.Integer(), nullable=False),
        sa.Column("line_item_name", sa.String(), nullable=False),
        sa.Column("current_period", sa.String(), nullable=False),
        sa.Column("previous_period", sa.String(), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("previous_value", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("change_amount", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("change_percentage", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("is_favorable", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["consolidated_statement_id"],
            ["consolidated_statements.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for foreign key
    op.create_index(
        op.f("ix_period_comparisons_consolidated_statement_id"),
        "period_comparisons",
        ["consolidated_statement_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop consolidated_statements and period_comparisons tables."""
    op.drop_index(
        op.f("ix_period_comparisons_consolidated_statement_id"),
        table_name="period_comparisons",
    )
    op.drop_table("period_comparisons")
    op.drop_table("consolidated_statements")
