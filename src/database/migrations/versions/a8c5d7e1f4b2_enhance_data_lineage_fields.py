"""Enhance data lineage fields

Revision ID: a8c5d7e1f4b2
Revises: f3b7c8d9e2a1
Create Date: 2025-11-12 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8c5d7e1f4b2'
down_revision: Union[str, Sequence[str], None] = 'f3b7c8d9e2a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enhanced lineage tracking fields."""
    # Add new fields to data_lineage table
    op.add_column('data_lineage', sa.Column('validation_notes', sa.Text(), nullable=True))
    op.add_column('data_lineage', sa.Column('confidence_score', sa.Integer(), nullable=True))
    op.add_column('data_lineage', sa.Column('source_document_table_name', sa.String(length=255), nullable=True))
    op.add_column('data_lineage', sa.Column('source_document_line_item', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove enhanced lineage tracking fields."""
    op.drop_column('data_lineage', 'source_document_line_item')
    op.drop_column('data_lineage', 'source_document_table_name')
    op.drop_column('data_lineage', 'confidence_score')
    op.drop_column('data_lineage', 'validation_notes')
