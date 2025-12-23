"""add statements tables

Revision ID: 51ede09ed895
Revises: d7fdd70aca5d
Create Date: 2025-12-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51ede09ed895'
down_revision = 'd7fdd70aca5d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create StatementType enum
    statement_type_enum = sa.Enum(
        "INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW",
        name="statementtype"
    )
    statement_type_enum.create(op.get_bind())

    # Create statements table
    op.create_table(
        "statements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("statement_type", statement_type_enum, nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("period_start", sa.String(length=10), nullable=False),
        sa.Column("period_end", sa.String(length=10), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("extra_metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("length(period_start) = 10", name="period_start_format"),
        sa.CheckConstraint("length(period_end) = 10", name="period_end_format"),
        sa.CheckConstraint("length(currency) = 3", name="currency_code_length"),
        sa.CheckConstraint("fiscal_year > 1900", name="fiscal_year_valid"),
    )

    # Create line_items table
    op.create_table(
        "line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("statement_id", sa.Integer(), nullable=False),
        sa.Column("line_item_name", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("value", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("indent_level", sa.Integer(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["statement_id"],
            ["statements.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["line_items.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("indent_level >= 0 AND indent_level <= 5", name="indent_level_range"),
        sa.CheckConstraint("order >= 0", name="order_non_negative"),
    )

    # Create indexes for better query performance
    op.create_index(
        op.f("ix_statements_statement_type"), "statements", ["statement_type"], unique=False
    )
    op.create_index(
        op.f("ix_statements_company_name"), "statements", ["company_name"], unique=False
    )
    op.create_index(
        op.f("ix_statements_fiscal_year"), "statements", ["fiscal_year"], unique=False
    )
    op.create_index(
        op.f("ix_line_items_statement_id"), "line_items", ["statement_id"], unique=False
    )
    op.create_index(
        op.f("ix_line_items_category"), "line_items", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_line_items_order"), "line_items", ["order"], unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_line_items_order"), table_name="line_items")
    op.drop_index(op.f("ix_line_items_category"), table_name="line_items")
    op.drop_index(op.f("ix_line_items_statement_id"), table_name="line_items")
    op.drop_index(op.f("ix_statements_fiscal_year"), table_name="statements")
    op.drop_index(op.f("ix_statements_company_name"), table_name="statements")
    op.drop_index(op.f("ix_statements_statement_type"), table_name="statements")

    # Drop tables
    op.drop_table("line_items")
    op.drop_table("statements")

    # Drop enum
    op.execute("DROP TYPE IF EXISTS statementtype")
