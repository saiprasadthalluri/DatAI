"""Add auth fields to users table.

Revision ID: 002
Revises: 001
Create Date: 2025-12-05

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('firebase_uid', sa.String(128), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_users_firebase_uid', 'users', ['firebase_uid'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_firebase_uid', 'users')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'firebase_uid')

