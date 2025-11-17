"""Add three-tier CAFR data tracking: stated vs restated with tier classification

Revision ID: g4c9e1f5j8f6
Revises: d2e8f0g4i7e5
Create Date: 2025-11-17 12:00:00.000000

This migration adds critical data provenance tracking to distinguish:
1. Stated data (Tier 1: Financial Section - current year actuals)
2. Restated data (Tier 3: Statistical Section - historical comparisons)
3. Notes metadata (Tier 2: Notes to Financial Statements)

Enables detection of discrepancies between stated and restated values across
different CAFR publications.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g4c9e1f5j8f6'
down_revision: Union[str, None] = 'd2e8f0g4i7e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add stated/restated tracking to all financial data models.

    New fields added to: revenues, expenditures, fund_balances, pension_contributions
    """

    # ========================================================================
    # Add version tracking fields to REVENUES
    # ========================================================================
    print("Adding version tracking to revenues table...")

    op.add_column('revenues', sa.Column(
        'cafr_tier',
        sa.String(20),
        nullable=False,
        server_default='tier_1_financial',
        comment='CAFR section: tier_1_financial, tier_2_notes, tier_3_statistical'
    ))

    op.add_column('revenues', sa.Column(
        'data_version_type',
        sa.String(20),
        nullable=False,
        server_default='stated',
        comment='stated (primary) or restated (historical comparison)'
    ))

    op.add_column('revenues', sa.Column(
        'source_cafr_year',
        sa.Integer,
        nullable=True,
        comment='Which CAFR year reported this data (e.g., 2024 CAFR reports 2015-2024)'
    ))

    op.add_column('revenues', sa.Column(
        'is_primary_version',
        sa.Boolean,
        nullable=False,
        server_default='true',
        comment='True = stated data for analysis; False = restated for comparison only'
    ))

    op.add_column('revenues', sa.Column(
        'restatement_reason',
        sa.Text,
        nullable=True,
        comment='Why was this restated? (GASB change, reclassification, error correction)'
    ))

    op.add_column('revenues', sa.Column(
        'supersedes_version_id',
        sa.Integer,
        nullable=True,
        comment='Foreign key to previous version if this is a restatement'
    ))

    # Backfill source_cafr_year for existing data
    op.execute("""
        UPDATE revenues
        SET source_cafr_year = (
            SELECT year FROM fiscal_years
            WHERE fiscal_years.id = revenues.fiscal_year_id
        )
        WHERE source_cafr_year IS NULL
    """)

    # Now make source_cafr_year required
    op.alter_column('revenues', 'source_cafr_year', nullable=False)

    # Add foreign key for supersedes_version_id
    op.create_foreign_key(
        'fk_revenue_supersedes_version',
        'revenues', 'revenues',
        ['supersedes_version_id'], ['id']
    )

    # Add unique constraint: one version per fiscal_year + category + tier + source_cafr
    op.create_unique_constraint(
        'uq_revenue_version',
        'revenues',
        ['fiscal_year_id', 'category_id', 'cafr_tier', 'data_version_type', 'source_cafr_year']
    )

    # Add index for primary version lookups (critical for analytics queries)
    op.create_index(
        'ix_revenue_is_primary',
        'revenues',
        ['is_primary_version', 'fiscal_year_id']
    )

    # ========================================================================
    # Add version tracking fields to EXPENDITURES
    # ========================================================================
    print("Adding version tracking to expenditures table...")

    op.add_column('expenditures', sa.Column('cafr_tier', sa.String(20), nullable=False, server_default='tier_1_financial'))
    op.add_column('expenditures', sa.Column('data_version_type', sa.String(20), nullable=False, server_default='stated'))
    op.add_column('expenditures', sa.Column('source_cafr_year', sa.Integer, nullable=True))
    op.add_column('expenditures', sa.Column('is_primary_version', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('expenditures', sa.Column('restatement_reason', sa.Text, nullable=True))
    op.add_column('expenditures', sa.Column('supersedes_version_id', sa.Integer, nullable=True))

    op.execute("""
        UPDATE expenditures
        SET source_cafr_year = (
            SELECT year FROM fiscal_years
            WHERE fiscal_years.id = expenditures.fiscal_year_id
        )
        WHERE source_cafr_year IS NULL
    """)

    op.alter_column('expenditures', 'source_cafr_year', nullable=False)
    op.create_foreign_key('fk_expenditure_supersedes_version', 'expenditures', 'expenditures', ['supersedes_version_id'], ['id'])
    op.create_unique_constraint('uq_expenditure_version', 'expenditures', ['fiscal_year_id', 'category_id', 'cafr_tier', 'data_version_type', 'source_cafr_year'])
    op.create_index('ix_expenditure_is_primary', 'expenditures', ['is_primary_version', 'fiscal_year_id'])

    # ========================================================================
    # Add version tracking fields to FUND_BALANCES
    # ========================================================================
    print("Adding version tracking to fund_balances table...")

    op.add_column('fund_balances', sa.Column('cafr_tier', sa.String(20), nullable=False, server_default='tier_1_financial'))
    op.add_column('fund_balances', sa.Column('data_version_type', sa.String(20), nullable=False, server_default='stated'))
    op.add_column('fund_balances', sa.Column('source_cafr_year', sa.Integer, nullable=True))
    op.add_column('fund_balances', sa.Column('is_primary_version', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('fund_balances', sa.Column('restatement_reason', sa.Text, nullable=True))
    op.add_column('fund_balances', sa.Column('supersedes_version_id', sa.Integer, nullable=True))

    op.execute("""
        UPDATE fund_balances
        SET source_cafr_year = (
            SELECT year FROM fiscal_years
            WHERE fiscal_years.id = fund_balances.fiscal_year_id
        )
        WHERE source_cafr_year IS NULL
    """)

    op.alter_column('fund_balances', 'source_cafr_year', nullable=False)
    op.create_foreign_key('fk_fund_balance_supersedes_version', 'fund_balances', 'fund_balances', ['supersedes_version_id'], ['id'])
    op.create_unique_constraint('uq_fund_balance_version', 'fund_balances', ['fiscal_year_id', 'fund_type', 'cafr_tier', 'data_version_type', 'source_cafr_year'])
    op.create_index('ix_fund_balance_is_primary', 'fund_balances', ['is_primary_version', 'fiscal_year_id'])

    # ========================================================================
    # Add version tracking fields to PENSION_CONTRIBUTIONS
    # ========================================================================
    print("Adding version tracking to pension_contributions table...")

    op.add_column('pension_contributions', sa.Column('cafr_tier', sa.String(20), nullable=False, server_default='tier_1_financial'))
    op.add_column('pension_contributions', sa.Column('data_version_type', sa.String(20), nullable=False, server_default='stated'))
    op.add_column('pension_contributions', sa.Column('source_cafr_year', sa.Integer, nullable=True))
    op.add_column('pension_contributions', sa.Column('is_primary_version', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('pension_contributions', sa.Column('restatement_reason', sa.Text, nullable=True))
    op.add_column('pension_contributions', sa.Column('supersedes_version_id', sa.Integer, nullable=True))

    op.execute("""
        UPDATE pension_contributions
        SET source_cafr_year = (
            SELECT year FROM fiscal_years
            WHERE fiscal_years.id = pension_contributions.fiscal_year_id
        )
        WHERE source_cafr_year IS NULL
    """)

    op.alter_column('pension_contributions', 'source_cafr_year', nullable=False)
    op.create_foreign_key('fk_pension_contribution_supersedes_version', 'pension_contributions', 'pension_contributions', ['supersedes_version_id'], ['id'])
    op.create_unique_constraint('uq_pension_contribution_version', 'pension_contributions', ['fiscal_year_id', 'plan_id', 'cafr_tier', 'data_version_type', 'source_cafr_year'])
    op.create_index('ix_pension_contribution_is_primary', 'pension_contributions', ['is_primary_version', 'fiscal_year_id'])

    # ========================================================================
    # Create RESTATEMENT_DISCREPANCIES table
    # ========================================================================
    print("Creating restatement_discrepancies table...")

    op.create_table(
        'restatement_discrepancies',
        sa.Column('id', sa.Integer, primary_key=True),

        # What data changed?
        sa.Column('table_name', sa.String(100), nullable=False,
                  comment='revenues, expenditures, fund_balances, pension_contributions'),
        sa.Column('fiscal_year_id', sa.Integer, sa.ForeignKey('fiscal_years.id'), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False,
                  comment='actual_amount, total_fund_balance, etc.'),

        # Stated version (original - ground truth)
        sa.Column('stated_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('stated_source_cafr_year', sa.Integer, nullable=False,
                  comment='Year of CAFR that originally stated this value'),
        sa.Column('stated_record_id', sa.Integer, nullable=False,
                  comment='ID in source table (revenues.id, etc.)'),

        # Restated version (revised in later CAFR)
        sa.Column('restated_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('restated_source_cafr_year', sa.Integer, nullable=False,
                  comment='Year of CAFR that restated this value'),
        sa.Column('restated_record_id', sa.Integer, nullable=False,
                  comment='ID in source table (revenues.id, etc.)'),

        # Discrepancy metrics
        sa.Column('absolute_difference', sa.Numeric(15, 4), nullable=False,
                  comment='restated_value - stated_value'),
        sa.Column('percent_difference', sa.Numeric(8, 4), nullable=True,
                  comment='(restated - stated) / stated * 100'),

        # Why did this change?
        sa.Column('restatement_reason', sa.Text, nullable=True,
                  comment='GASB standard change, reclassification, error correction, etc.'),
        sa.Column('restatement_category', sa.String(50), nullable=True,
                  comment='GASB_Change, Reclassification, Error_Correction, Fund_Transfer, Other'),

        # Severity assessment (automated)
        sa.Column('severity', sa.String(20), nullable=False, server_default='Minor',
                  comment='Minor (<1%), Moderate (1-5%), Major (5-10%), Critical (>10%)'),

        # Manual review workflow
        sa.Column('requires_review', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('reviewed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('reviewed_date', sa.DateTime, nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),

        # Audit trail
        sa.Column('detected_date', sa.DateTime, nullable=False, server_default=sa.func.now(),
                  comment='When discrepancy was automatically detected'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Indexes for efficient querying
    op.create_index('ix_restatement_discrepancy_fiscal_year', 'restatement_discrepancies', ['fiscal_year_id'])
    op.create_index('ix_restatement_discrepancy_severity', 'restatement_discrepancies', ['severity'])
    op.create_index('ix_restatement_discrepancy_reviewed', 'restatement_discrepancies', ['reviewed'])
    op.create_index('ix_restatement_discrepancy_table', 'restatement_discrepancies', ['table_name', 'fiscal_year_id'])

    # Unique constraint to prevent duplicate discrepancy records
    op.create_unique_constraint(
        'uq_restatement_discrepancy',
        'restatement_discrepancies',
        ['table_name', 'fiscal_year_id', 'field_name', 'stated_source_cafr_year', 'restated_source_cafr_year']
    )

    print("✅ Migration complete: Three-tier CAFR tracking enabled")


def downgrade() -> None:
    """
    Remove stated/restated tracking.

    WARNING: This will delete restatement history!
    """
    print("⚠️ WARNING: Dropping restatement tracking tables and columns")

    # Drop restatement_discrepancies table
    op.drop_table('restatement_discrepancies')

    # Remove version tracking from revenues
    op.drop_constraint('uq_revenue_version', 'revenues')
    op.drop_constraint('fk_revenue_supersedes_version', 'revenues')
    op.drop_index('ix_revenue_is_primary', 'revenues')
    op.drop_column('revenues', 'supersedes_version_id')
    op.drop_column('revenues', 'restatement_reason')
    op.drop_column('revenues', 'is_primary_version')
    op.drop_column('revenues', 'source_cafr_year')
    op.drop_column('revenues', 'data_version_type')
    op.drop_column('revenues', 'cafr_tier')

    # Remove version tracking from expenditures
    op.drop_constraint('uq_expenditure_version', 'expenditures')
    op.drop_constraint('fk_expenditure_supersedes_version', 'expenditures')
    op.drop_index('ix_expenditure_is_primary', 'expenditures')
    op.drop_column('expenditures', 'supersedes_version_id')
    op.drop_column('expenditures', 'restatement_reason')
    op.drop_column('expenditures', 'is_primary_version')
    op.drop_column('expenditures', 'source_cafr_year')
    op.drop_column('expenditures', 'data_version_type')
    op.drop_column('expenditures', 'cafr_tier')

    # Remove version tracking from fund_balances
    op.drop_constraint('uq_fund_balance_version', 'fund_balances')
    op.drop_constraint('fk_fund_balance_supersedes_version', 'fund_balances')
    op.drop_index('ix_fund_balance_is_primary', 'fund_balances')
    op.drop_column('fund_balances', 'supersedes_version_id')
    op.drop_column('fund_balances', 'restatement_reason')
    op.drop_column('fund_balances', 'is_primary_version')
    op.drop_column('fund_balances', 'source_cafr_year')
    op.drop_column('fund_balances', 'data_version_type')
    op.drop_column('fund_balances', 'cafr_tier')

    # Remove version tracking from pension_contributions
    op.drop_constraint('uq_pension_contribution_version', 'pension_contributions')
    op.drop_constraint('fk_pension_contribution_supersedes_version', 'pension_contributions')
    op.drop_index('ix_pension_contribution_is_primary', 'pension_contributions')
    op.drop_column('pension_contributions', 'supersedes_version_id')
    op.drop_column('pension_contributions', 'restatement_reason')
    op.drop_column('pension_contributions', 'is_primary_version')
    op.drop_column('pension_contributions', 'source_cafr_year')
    op.drop_column('pension_contributions', 'data_version_type')
    op.drop_column('pension_contributions', 'cafr_tier')

    print("✅ Downgrade complete: Version tracking removed")
