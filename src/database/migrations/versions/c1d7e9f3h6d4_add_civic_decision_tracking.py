"""Add civic decision tracking models

Revision ID: c1d7e9f3h6d4
Revises: b9d6e8f2g5c3
Create Date: 2025-11-12 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d7e9f3h6d4'
down_revision: Union[str, Sequence[str], None] = 'b9d6e8f2g5c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add civic decision tracking tables."""
    # Create decisions table
    op.create_table(
        'decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('decision_date', sa.Date(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum(
            'budget', 'tax', 'bond', 'labor', 'service', 'infrastructure',
            'pension', 'policy', 'emergency', 'other',
            name='decisioncategory'
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'proposed', 'approved', 'rejected', 'pending_outcome',
            'outcome_tracked', 'cancelled',
            name='decisionstatus'
        ), nullable=False),
        sa.Column('vote_type', sa.Enum(
            'council', 'ballot', 'referendum', 'emergency',
            name='votetype'
        ), nullable=True),
        sa.Column('vote_count_yes', sa.Integer(), nullable=True),
        sa.Column('vote_count_no', sa.Integer(), nullable=True),
        sa.Column('vote_count_abstain', sa.Integer(), nullable=True),
        sa.Column('ballot_measure_id', sa.String(length=50), nullable=True),
        sa.Column('ballot_measure_text', sa.Text(), nullable=True),
        sa.Column('predicted_annual_impact', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('predicted_one_time_impact', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('predicted_impact_start_year', sa.Integer(), nullable=True),
        sa.Column('predicted_impact_duration_years', sa.Integer(), nullable=True),
        sa.Column('prediction_notes', sa.Text(), nullable=True),
        sa.Column('prediction_confidence', sa.String(length=20), nullable=True),
        sa.Column('predicted_by', sa.String(length=255), nullable=True),
        sa.Column('prediction_date', sa.Date(), nullable=True),
        sa.Column('primary_fiscal_year_id', sa.Integer(), nullable=True),
        sa.Column('source_document_url', sa.String(length=500), nullable=True),
        sa.Column('source_document_id', sa.Integer(), nullable=True),
        sa.Column('external_reference_url', sa.String(length=500), nullable=True),
        sa.Column('council_meeting_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.ForeignKeyConstraint(['primary_fiscal_year_id'], ['fiscal_years.id'], ),
        sa.ForeignKeyConstraint(['source_document_id'], ['source_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decisions_city_date', 'decisions', ['city_id', 'decision_date'])
    op.create_index('ix_decisions_category', 'decisions', ['category'])
    op.create_index('ix_decisions_status', 'decisions', ['status'])

    # Create votes table
    op.create_table(
        'votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('decision_id', sa.Integer(), nullable=False),
        sa.Column('voter_name', sa.String(length=255), nullable=False),
        sa.Column('voter_title', sa.String(length=100), nullable=True),
        sa.Column('voter_district', sa.String(length=50), nullable=True),
        sa.Column('vote', sa.String(length=20), nullable=False),
        sa.Column('vote_date', sa.Date(), nullable=False),
        sa.Column('vote_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['decision_id'], ['decisions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_votes_decision', 'votes', ['decision_id'])
    op.create_index('ix_votes_voter', 'votes', ['voter_name'])

    # Create outcomes table
    op.create_table(
        'outcomes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('decision_id', sa.Integer(), nullable=False),
        sa.Column('outcome_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum(
            'pending', 'partial', 'final', 'revised',
            name='outcomestatus'
        ), nullable=False),
        sa.Column('actual_annual_impact', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('actual_one_time_impact', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('fiscal_year_id', sa.Integer(), nullable=True),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('variance_explanation', sa.Text(), nullable=True),
        sa.Column('accuracy_percent', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('absolute_variance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('data_source', sa.String(length=255), nullable=True),
        sa.Column('source_document_id', sa.Integer(), nullable=True),
        sa.Column('measured_by', sa.String(length=255), nullable=True),
        sa.Column('measurement_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['decision_id'], ['decisions.id'], ),
        sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ),
        sa.ForeignKeyConstraint(['source_document_id'], ['source_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_outcomes_decision', 'outcomes', ['decision_id'])
    op.create_index('ix_outcomes_date', 'outcomes', ['outcome_date'])
    op.create_index('ix_outcomes_status', 'outcomes', ['status'])


def downgrade() -> None:
    """Remove civic decision tracking tables."""
    op.drop_index('ix_outcomes_status', table_name='outcomes')
    op.drop_index('ix_outcomes_date', table_name='outcomes')
    op.drop_index('ix_outcomes_decision', table_name='outcomes')
    op.drop_table('outcomes')

    op.drop_index('ix_votes_voter', table_name='votes')
    op.drop_index('ix_votes_decision', table_name='votes')
    op.drop_table('votes')

    op.drop_index('ix_decisions_status', table_name='decisions')
    op.drop_index('ix_decisions_category', table_name='decisions')
    op.drop_index('ix_decisions_city_date', table_name='decisions')
    op.drop_table('decisions')

    # Drop enums (PostgreSQL)
    op.execute('DROP TYPE IF EXISTS outcomestatus')
    op.execute('DROP TYPE IF EXISTS votetype')
    op.execute('DROP TYPE IF EXISTS decisionstatus')
    op.execute('DROP TYPE IF EXISTS decisioncategory')
