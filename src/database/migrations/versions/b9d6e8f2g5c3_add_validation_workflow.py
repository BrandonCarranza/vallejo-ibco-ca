"""Add validation workflow models

Revision ID: b9d6e8f2g5c3
Revises: a8c5d7e1f4b2
Create Date: 2025-11-12 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9d6e8f2g5c3'
down_revision: Union[str, Sequence[str], None] = 'a8c5d7e1f4b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add validation workflow tables."""
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('entered_value', sa.String(length=255), nullable=True),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('fiscal_year_id', sa.Integer(), nullable=True),
        sa.Column('entered_by', sa.String(length=255), nullable=False),
        sa.Column('entered_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('flag_reason', sa.String(length=255), nullable=True),
        sa.Column('flag_details', sa.Text(), nullable=True),
        sa.Column('prior_year_value', sa.String(length=255), nullable=True),
        sa.Column('expected_value', sa.String(length=255), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('source_document_url', sa.String(length=500), nullable=True),
        sa.Column('source_document_page', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_queue_city_fy', 'validation_queue', ['city_id', 'fiscal_year'])
    op.create_index('ix_validation_queue_severity', 'validation_queue', ['severity'])
    op.create_index('ix_validation_queue_status', 'validation_queue', ['status'])

    # Create validation_records table
    op.create_table(
        'validation_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('queue_item_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('validated_by', sa.String(length=255), nullable=False),
        sa.Column('validated_at', sa.DateTime(), nullable=False),
        sa.Column('validation_notes', sa.Text(), nullable=False),
        sa.Column('confidence_adjustment', sa.Integer(), nullable=True),
        sa.Column('corrected_value', sa.String(length=255), nullable=True),
        sa.Column('correction_reason', sa.Text(), nullable=True),
        sa.Column('escalated_to', sa.String(length=255), nullable=True),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['queue_item_id'], ['validation_queue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_record_action', 'validation_records', ['action'])
    op.create_index('ix_validation_record_queue_item', 'validation_records', ['queue_item_id'])
    op.create_index('ix_validation_record_validator', 'validation_records', ['validated_by'])

    # Create anomaly_flags table
    op.create_table(
        'anomaly_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('queue_item_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('rule_description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('entered_value', sa.String(length=255), nullable=False),
        sa.Column('expected_value', sa.String(length=255), nullable=True),
        sa.Column('prior_year_value', sa.String(length=255), nullable=True),
        sa.Column('deviation_percent', sa.Integer(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('suggested_action', sa.String(length=20), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['queue_item_id'], ['validation_queue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_anomaly_flag_queue_item', 'anomaly_flags', ['queue_item_id'])
    op.create_index('ix_anomaly_flag_rule', 'anomaly_flags', ['rule_name'])
    op.create_index('ix_anomaly_flag_severity', 'anomaly_flags', ['severity'])

    # Create validation_rules table
    op.create_table(
        'validation_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('rule_description', sa.Text(), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=True),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('parameters', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('suggested_action', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_name')
    )
    op.create_index('ix_validation_rule_active', 'validation_rules', ['is_active'])


def downgrade() -> None:
    """Remove validation workflow tables."""
    op.drop_index('ix_validation_rule_active', table_name='validation_rules')
    op.drop_table('validation_rules')
    op.drop_index('ix_anomaly_flag_severity', table_name='anomaly_flags')
    op.drop_index('ix_anomaly_flag_rule', table_name='anomaly_flags')
    op.drop_index('ix_anomaly_flag_queue_item', table_name='anomaly_flags')
    op.drop_table('anomaly_flags')
    op.drop_index('ix_validation_record_validator', table_name='validation_records')
    op.drop_index('ix_validation_record_queue_item', table_name='validation_records')
    op.drop_index('ix_validation_record_action', table_name='validation_records')
    op.drop_table('validation_records')
    op.drop_index('ix_validation_queue_status', table_name='validation_queue')
    op.drop_index('ix_validation_queue_severity', table_name='validation_queue')
    op.drop_index('ix_validation_queue_city_fy', table_name='validation_queue')
    op.drop_table('validation_queue')
