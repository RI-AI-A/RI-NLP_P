"""Initial migration - Create NLP tables

Revision ID: 001
Revises: 
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create nlp_queries_log table
    op.create_table(
        'nlp_queries_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_role', sa.String(50), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('routed_endpoint', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_nlp_queries_log_conversation_id', 'nlp_queries_log', ['conversation_id'])
    op.create_index('ix_nlp_queries_log_intent', 'nlp_queries_log', ['intent'])
    op.create_index('ix_nlp_queries_log_created_at', 'nlp_queries_log', ['created_at'])
    
    # Create nlp_feedback table
    op.create_table(
        'nlp_feedback',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('query_id', UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['query_id'], ['nlp_queries_log.id'], ondelete='CASCADE'),
    )
    
    # Create index
    op.create_index('ix_nlp_feedback_query_id', 'nlp_feedback', ['query_id'])


def downgrade() -> None:
    op.drop_table('nlp_feedback')
    op.drop_table('nlp_queries_log')
