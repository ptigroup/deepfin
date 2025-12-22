"""add detection tables

Revision ID: d7fdd70aca5d
Revises: 
Create Date: 2025-12-22 15:19:31.732926

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7fdd70aca5d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="documentstatus"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create detection_results table
    op.create_table(
        "detection_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("table_count", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "DETECTED", "NO_TABLES", "FAILED", name="detectionstatus"),
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("bounding_boxes", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for better query performance
    op.create_index(
        op.f("ix_documents_status"), "documents", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_detection_results_document_id"),
        "detection_results",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_detection_results_status"),
        "detection_results",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_detection_results_status"), table_name="detection_results")
    op.drop_index(
        op.f("ix_detection_results_document_id"), table_name="detection_results"
    )
    op.drop_index(op.f("ix_documents_status"), table_name="documents")

    # Drop tables
    op.drop_table("detection_results")
    op.drop_table("documents")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS detectionstatus")
    op.execute("DROP TYPE IF EXISTS documentstatus")
