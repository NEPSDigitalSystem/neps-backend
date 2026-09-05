"""Add v3 expanded schema fields

Revision ID: add_v3_expanded_schema
Revises: b2396d7fdcf4
Create Date: 2026-09-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_v3_expanded_schema'
down_revision = 'b2396d7fdcf4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add socio-economic fields to participants table
    op.add_column('participants', sa.Column('employment_status', sa.String(), nullable=True, schema='neps_core'))
    op.add_column('participants', sa.Column('food_security', sa.String(), nullable=True, schema='neps_core'))
    op.add_column('participants', sa.Column('healthcare_access', sa.String(), nullable=True, schema='neps_core'))
    op.add_column('participants', sa.Column('socioeconomic_status', sa.String(), nullable=True, schema='neps_core'))
    
    # Add ML score fields to survey_responses table
    op.add_column('survey_responses', sa.Column('mood_score', sa.Float(), nullable=True, schema='neps_core'))
    op.add_column('survey_responses', sa.Column('sleep_quality_score', sa.Float(), nullable=True, schema='neps_core'))
    op.add_column('survey_responses', sa.Column('fatigue_score', sa.Float(), nullable=True, schema='neps_core'))
    op.add_column('survey_responses', sa.Column('attendance_score', sa.Float(), nullable=True, schema='neps_core'))
    op.add_column('survey_responses', sa.Column('coping_score', sa.Float(), nullable=True, schema='neps_core'))
    op.add_column('survey_responses', sa.Column('substance_abuse_score', sa.Float(), nullable=True, schema='neps_core'))
    op.add_column('survey_responses', sa.Column('suicidality_score', sa.Float(), nullable=True, schema='neps_core'))


def downgrade() -> None:
    # Remove ML score fields from survey_responses table
    op.drop_column('survey_responses', 'suicidality_score', schema='neps_core')
    op.drop_column('survey_responses', 'substance_abuse_score', schema='neps_core')
    op.drop_column('survey_responses', 'coping_score', schema='neps_core')
    op.drop_column('survey_responses', 'attendance_score', schema='neps_core')
    op.drop_column('survey_responses', 'fatigue_score', schema='neps_core')
    op.drop_column('survey_responses', 'sleep_quality_score', schema='neps_core')
    op.drop_column('survey_responses', 'mood_score', schema='neps_core')
    
    # Remove socio-economic fields from participants table
    op.drop_column('participants', 'socioeconomic_status', schema='neps_core')
    op.drop_column('participants', 'healthcare_access', schema='neps_core')
    op.drop_column('participants', 'food_security', schema='neps_core')
    op.drop_column('participants', 'employment_status', schema='neps_core')
