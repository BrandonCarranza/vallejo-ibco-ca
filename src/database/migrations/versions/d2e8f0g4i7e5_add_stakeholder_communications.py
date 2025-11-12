"""Add stakeholder communication models

Revision ID: d2e8f0g4i7e5
Revises: c1d7e9f3h6d4
Create Date: 2025-11-12 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e8f0g4i7e5'
down_revision: Union[str, Sequence[str], None] = 'c1d7e9f3h6d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add stakeholder communication tables."""
    # Create subscribers table
    op.create_table(
        'subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('category', sa.Enum(
            'media', 'council', 'civil_society', 'researcher', 'public', 'other',
            name='subscribercategory'
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'active', 'unsubscribed', 'bounced', 'inactive',
            name='subscriberstatus'
        ), nullable=False),
        sa.Column('subscribed_to_quarterly_updates', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('subscribed_to_alerts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('subscribed_to_press_releases', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('city_id', sa.Integer(), nullable=True),
        sa.Column('subscription_date', sa.DateTime(), nullable=False),
        sa.Column('unsubscribe_date', sa.DateTime(), nullable=True),
        sa.Column('unsubscribe_token', sa.String(length=100), nullable=True),
        sa.Column('last_email_sent', sa.DateTime(), nullable=True),
        sa.Column('email_bounce_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_bounce_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('unsubscribe_token')
    )
    op.create_index('ix_subscribers_email', 'subscribers', ['email'])
    op.create_index('ix_subscribers_category', 'subscribers', ['category'])
    op.create_index('ix_subscribers_status', 'subscribers', ['status'])

    # Create alert_rules table
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.Enum(
            'risk_score_change', 'fiscal_cliff_change', 'pension_threshold',
            'new_data', 'quarterly_update', 'press_release', 'decision_outcome', 'custom',
            name='notificationtype'
        ), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=True),
        sa.Column('threshold_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('change_threshold', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('direction', sa.String(length=20), nullable=True),
        sa.Column('severity', sa.Enum(
            'info', 'warning', 'critical',
            name='alertseverity'
        ), nullable=False),
        sa.Column('message_template', sa.Text(), nullable=True),
        sa.Column('city_id', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cooldown_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('last_triggered_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_name')
    )
    op.create_index('ix_alert_rules_type', 'alert_rules', ['notification_type'])
    op.create_index('ix_alert_rules_enabled', 'alert_rules', ['is_enabled'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscriber_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.Enum(
            'risk_score_change', 'fiscal_cliff_change', 'pension_threshold',
            'new_data', 'quarterly_update', 'press_release', 'decision_outcome', 'custom',
            name='notificationtype'
        ), nullable=False),
        sa.Column('severity', sa.Enum(
            'info', 'warning', 'critical',
            name='alertseverity'
        ), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('message_html', sa.Text(), nullable=True),
        sa.Column('city_id', sa.Integer(), nullable=True),
        sa.Column('alert_rule_id', sa.Integer(), nullable=True),
        sa.Column('risk_score_id', sa.Integer(), nullable=True),
        sa.Column('decision_id', sa.Integer(), nullable=True),
        sa.Column('fiscal_year_id', sa.Integer(), nullable=True),
        sa.Column('trigger_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('previous_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.Enum(
            'pending', 'sent', 'failed', 'bounced',
            name='notificationstatus'
        ), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_error', sa.Text(), nullable=True),
        sa.Column('email_message_id', sa.String(length=255), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['subscriber_id'], ['subscribers.id'], ),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.ForeignKeyConstraint(['alert_rule_id'], ['alert_rules.id'], ),
        sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_subscriber', 'notifications', ['subscriber_id'])
    op.create_index('ix_notifications_type', 'notifications', ['notification_type'])
    op.create_index('ix_notifications_status', 'notifications', ['status'])
    op.create_index('ix_notifications_sent_date', 'notifications', ['sent_at'])


def downgrade() -> None:
    """Remove stakeholder communication tables."""
    op.drop_index('ix_notifications_sent_date', table_name='notifications')
    op.drop_index('ix_notifications_status', table_name='notifications')
    op.drop_index('ix_notifications_type', table_name='notifications')
    op.drop_index('ix_notifications_subscriber', table_name='notifications')
    op.drop_table('notifications')

    op.drop_index('ix_alert_rules_enabled', table_name='alert_rules')
    op.drop_index('ix_alert_rules_type', table_name='alert_rules')
    op.drop_table('alert_rules')

    op.drop_index('ix_subscribers_status', table_name='subscribers')
    op.drop_index('ix_subscribers_category', table_name='subscribers')
    op.drop_index('ix_subscribers_email', table_name='subscribers')
    op.drop_table('subscribers')

    # Drop enums (PostgreSQL)
    op.execute('DROP TYPE IF EXISTS notificationstatus')
    op.execute('DROP TYPE IF EXISTS notificationtype')
    op.execute('DROP TYPE IF EXISTS alertseverity')
    op.execute('DROP TYPE IF EXISTS subscriberstatus')
    op.execute('DROP TYPE IF EXISTS subscribercategory')
