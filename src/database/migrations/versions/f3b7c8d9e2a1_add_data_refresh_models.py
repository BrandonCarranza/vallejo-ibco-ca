"""Add data refresh models

Revision ID: f3b7c8d9e2a1
Revises: ea4a6621450b
Create Date: 2025-11-12 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3b7c8d9e2a1'
down_revision: Union[str, Sequence[str], None] = 'ea4a6621450b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add data refresh orchestration tables."""
    # Create refresh_checks table
    op.create_table(
        'refresh_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=False),
        sa.Column('check_frequency', sa.String(length=20), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=False),
        sa.Column('new_document_found', sa.Boolean(), nullable=False),
        sa.Column('document_url', sa.String(length=500), nullable=True),
        sa.Column('document_title', sa.String(length=255), nullable=True),
        sa.Column('fiscal_year', sa.Integer(), nullable=True),
        sa.Column('source_url_checked', sa.String(length=500), nullable=False),
        sa.Column('scraping_method', sa.String(length=100), nullable=True),
        sa.Column('scraping_success', sa.Boolean(), nullable=False),
        sa.Column('scraping_error', sa.Text(), nullable=True),
        sa.Column('notification_needed', sa.Boolean(), nullable=False),
        sa.Column('notification_sent', sa.Boolean(), nullable=False),
        sa.Column('notification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('check_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_check_city_type', 'refresh_checks', ['city_id', 'check_type'])
    op.create_index('ix_refresh_check_performed_at', 'refresh_checks', ['performed_at'])

    # Create refresh_notifications table
    op.create_table(
        'refresh_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('sent_to', sa.String(length=255), nullable=False),
        sa.Column('document_url', sa.String(length=500), nullable=False),
        sa.Column('document_title', sa.String(length=255), nullable=True),
        sa.Column('estimated_entry_time', sa.Integer(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=255), nullable=True),
        sa.Column('data_entry_started', sa.Boolean(), nullable=False),
        sa.Column('data_entry_started_at', sa.DateTime(), nullable=True),
        sa.Column('data_entry_completed', sa.Boolean(), nullable=False),
        sa.Column('data_entry_completed_at', sa.DateTime(), nullable=True),
        sa.Column('data_entry_completed_by', sa.String(length=255), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=False),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_notification_city_fy', 'refresh_notifications', ['city_id', 'fiscal_year'])
    op.create_index('ix_refresh_notification_sent_at', 'refresh_notifications', ['sent_at'])

    # Create refresh_operations table
    op.create_table(
        'refresh_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('fiscal_year_id', sa.Integer(), nullable=True),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('data_entry_started_at', sa.DateTime(), nullable=True),
        sa.Column('data_entry_completed_at', sa.DateTime(), nullable=True),
        sa.Column('data_entered_by', sa.String(length=255), nullable=True),
        sa.Column('validation_started_at', sa.DateTime(), nullable=True),
        sa.Column('validation_completed_at', sa.DateTime(), nullable=True),
        sa.Column('validation_passed', sa.Boolean(), nullable=True),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('risk_calculation_started_at', sa.DateTime(), nullable=True),
        sa.Column('risk_calculation_completed_at', sa.DateTime(), nullable=True),
        sa.Column('risk_calculation_success', sa.Boolean(), nullable=True),
        sa.Column('previous_risk_score', sa.Integer(), nullable=True),
        sa.Column('new_risk_score', sa.Integer(), nullable=True),
        sa.Column('projection_started_at', sa.DateTime(), nullable=True),
        sa.Column('projection_completed_at', sa.DateTime(), nullable=True),
        sa.Column('projection_success', sa.Boolean(), nullable=True),
        sa.Column('previous_fiscal_cliff_year', sa.Integer(), nullable=True),
        sa.Column('new_fiscal_cliff_year', sa.Integer(), nullable=True),
        sa.Column('report_generated', sa.Boolean(), nullable=False),
        sa.Column('report_generated_at', sa.DateTime(), nullable=True),
        sa.Column('report_url', sa.String(length=500), nullable=True),
        sa.Column('report_sent_to_stakeholders', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_operation_city_fy', 'refresh_operations', ['city_id', 'fiscal_year'])
    op.create_index('ix_refresh_operation_started_at', 'refresh_operations', ['started_at'])

    # Create data_refresh_schedules table
    op.create_table(
        'data_refresh_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=False),
        sa.Column('check_frequency', sa.String(length=20), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=True),
        sa.Column('expected_publication_months', sa.String(length=100), nullable=True),
        sa.Column('expected_publication_day', sa.Integer(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=False),
        sa.Column('source_check_method', sa.String(length=50), nullable=False),
        sa.Column('send_notifications', sa.Boolean(), nullable=False),
        sa.Column('notification_recipients', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_check_at', sa.DateTime(), nullable=True),
        sa.Column('next_check_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_schedule_city_type', 'data_refresh_schedules', ['city_id', 'check_type'])


def downgrade() -> None:
    """Remove data refresh orchestration tables."""
    op.drop_index('ix_refresh_schedule_city_type', table_name='data_refresh_schedules')
    op.drop_table('data_refresh_schedules')

    op.drop_index('ix_refresh_operation_started_at', table_name='refresh_operations')
    op.drop_index('ix_refresh_operation_city_fy', table_name='refresh_operations')
    op.drop_table('refresh_operations')

    op.drop_index('ix_refresh_notification_sent_at', table_name='refresh_notifications')
    op.drop_index('ix_refresh_notification_city_fy', table_name='refresh_notifications')
    op.drop_table('refresh_notifications')

    op.drop_index('ix_refresh_check_performed_at', table_name='refresh_checks')
    op.drop_index('ix_refresh_check_city_type', table_name='refresh_checks')
    op.drop_table('refresh_checks')
