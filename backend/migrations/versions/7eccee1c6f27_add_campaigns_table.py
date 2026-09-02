"""Add campaigns table

Revision ID: 7eccee1c6f27
Revises: e736837f5a06
Create Date: 2026-08-31T15:32:33.154977

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '7eccee1c6f27'
down_revision: Union[str, None] = 'e736837f5a06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('merchant_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('objective', sa.String(length=500), nullable=False),
        sa.Column('campaign_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('target_persona_id', sa.Uuid(), nullable=True),
        sa.Column('target_product_id', sa.Uuid(), nullable=True),
        sa.Column('trigger_signal', sa.String(length=100), nullable=False),
        sa.Column('trigger_evidence', sa.JSON(), nullable=False),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_persona_id'], ['buyer_personas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaigns_id'), 'campaigns', ['id'], unique=False)
    op.create_index(op.f('ix_campaigns_merchant_id'), 'campaigns', ['merchant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_campaigns_merchant_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_id'), table_name='campaigns')
    op.drop_table('campaigns')
