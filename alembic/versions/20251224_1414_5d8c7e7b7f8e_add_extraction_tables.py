"""add extraction tables

Revision ID: 5d8c7e7b7f8e
Revises: 51ede09ed895
Create Date: 2025-12-24 14:14:15.452894

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '5d8c7e7b7f8e'
down_revision = '51ede09ed895'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extraction_jobs table
    op.create_table(
        'extraction_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='extractionstatus'), nullable=False),
        sa.Column('statement_type', sa.Enum('income_statement', 'balance_sheet', 'cash_flow', 'unknown', name='statementtype'), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('period_start', sa.String(length=10), nullable=True),
        sa.Column('period_end', sa.String(length=10), nullable=True),
        sa.Column('fiscal_year', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_time', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='confidence_range'),
        sa.CheckConstraint('processing_time IS NULL OR processing_time >= 0', name='processing_time_positive'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash')
    )
    op.create_index(op.f('ix_extraction_jobs_file_hash'), 'extraction_jobs', ['file_hash'], unique=True)
    op.create_index(op.f('ix_extraction_jobs_status'), 'extraction_jobs', ['status'], unique=False)

    # Create extracted_statements table
    op.create_table(
        'extracted_statements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('extraction_job_id', sa.Integer(), nullable=False),
        sa.Column('statement_type', sa.Enum('income_statement', 'balance_sheet', 'cash_flow', 'unknown', name='statementtype'), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('period_start', sa.String(length=10), nullable=False),
        sa.Column('period_end', sa.String(length=10), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('total_line_items', sa.Integer(), nullable=False),
        sa.Column('has_errors', sa.Boolean(), nullable=False),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('extraction_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('length(period_start) = 10', name='extracted_period_start_format'),
        sa.CheckConstraint('length(period_end) = 10', name='extracted_period_end_format'),
        sa.CheckConstraint('length(currency) = 3', name='extracted_currency_length'),
        sa.CheckConstraint('fiscal_year > 1900', name='extracted_fiscal_year_valid'),
        sa.CheckConstraint('total_line_items >= 0', name='extracted_total_line_items_positive'),
        sa.ForeignKeyConstraint(['extraction_job_id'], ['extraction_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_extracted_statements_extraction_job_id'), 'extracted_statements', ['extraction_job_id'], unique=False)
    op.create_index(op.f('ix_extracted_statements_fiscal_year'), 'extracted_statements', ['fiscal_year'], unique=False)
    op.create_index(op.f('ix_extracted_statements_statement_type'), 'extracted_statements', ['statement_type'], unique=False)

    # Create extracted_line_items table
    op.create_table(
        'extracted_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('extracted_statement_id', sa.Integer(), nullable=False),
        sa.Column('line_item_name', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('value', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('indent_level', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(length=200), nullable=True),
        sa.Column('is_header', sa.Boolean(), nullable=False),
        sa.Column('is_total', sa.Boolean(), nullable=False),
        sa.Column('is_calculated', sa.Boolean(), nullable=False),
        sa.Column('formula', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('validation_warnings', sa.Text(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('indent_level >= 0 AND indent_level <= 10', name='indent_level_range'),
        sa.CheckConstraint('order >= 0', name='order_non_negative'),
        sa.ForeignKeyConstraint(['extracted_statement_id'], ['extracted_statements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['extracted_line_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_extracted_line_items_category'), 'extracted_line_items', ['category'], unique=False)
    op.create_index(op.f('ix_extracted_line_items_extracted_statement_id'), 'extracted_line_items', ['extracted_statement_id'], unique=False)
    op.create_index(op.f('ix_extracted_line_items_order'), 'extracted_line_items', ['order'], unique=False)
    op.create_index(op.f('ix_extracted_line_items_section'), 'extracted_line_items', ['section'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_extracted_line_items_section'), table_name='extracted_line_items')
    op.drop_index(op.f('ix_extracted_line_items_order'), table_name='extracted_line_items')
    op.drop_index(op.f('ix_extracted_line_items_extracted_statement_id'), table_name='extracted_line_items')
    op.drop_index(op.f('ix_extracted_line_items_category'), table_name='extracted_line_items')
    op.drop_table('extracted_line_items')

    op.drop_index(op.f('ix_extracted_statements_statement_type'), table_name='extracted_statements')
    op.drop_index(op.f('ix_extracted_statements_fiscal_year'), table_name='extracted_statements')
    op.drop_index(op.f('ix_extracted_statements_extraction_job_id'), table_name='extracted_statements')
    op.drop_table('extracted_statements')

    op.drop_index(op.f('ix_extraction_jobs_status'), table_name='extraction_jobs')
    op.drop_index(op.f('ix_extraction_jobs_file_hash'), table_name='extraction_jobs')
    op.drop_table('extraction_jobs')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS statementtype')
    op.execute('DROP TYPE IF EXISTS extractionstatus')
