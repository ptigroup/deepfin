"""rename_order_to_display_order

Revision ID: cd67a2114fdf
Revises: 20251226_0800
Create Date: 2025-12-26 15:16:38.527815

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd67a2114fdf'
down_revision = '20251226_0800'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename order column to display_order."""
    # Rename order to display_order in line_items table
    op.alter_column('line_items', 'order', new_column_name='display_order')

    # Rename order to display_order in extracted_line_items table
    op.alter_column('extracted_line_items', 'order', new_column_name='display_order')

    # Drop old CHECK constraints
    op.drop_constraint('order_non_negative', 'line_items', type_='check')
    op.drop_constraint('order_non_negative', 'extracted_line_items', type_='check')

    # Create new CHECK constraints with updated column name
    op.create_check_constraint('display_order_non_negative', 'line_items', 'display_order >= 0')
    op.create_check_constraint('display_order_non_negative', 'extracted_line_items', 'display_order >= 0')


def downgrade() -> None:
    """Rename display_order column back to order."""
    # Drop new CHECK constraints
    op.drop_constraint('display_order_non_negative', 'line_items', type_='check')
    op.drop_constraint('display_order_non_negative', 'extracted_line_items', type_='check')

    # Rename display_order back to order in line_items table
    op.alter_column('line_items', 'display_order', new_column_name='order')

    # Rename display_order back to order in extracted_line_items table
    op.alter_column('extracted_line_items', 'display_order', new_column_name='order')

    # Recreate old CHECK constraints
    op.create_check_constraint('order_non_negative', 'line_items', 'order >= 0')
    op.create_check_constraint('order_non_negative', 'extracted_line_items', 'order >= 0')
