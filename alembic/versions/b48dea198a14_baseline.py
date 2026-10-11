"""baseline

Revision ID: b48dea198a14
Revises: 
Create Date: 2026-10-08 00:45:28.113833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'b48dea198a14'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # tags is kept on purpose: the drop_index/drop_table lines were removed.
    op.alter_column('tasks', 'title',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.String(length=300),
               existing_nullable=False)
    op.alter_column('users', 'name',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=200),
               existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # create_table/create_index for tags were removed too, because
    # upgrade() no longer drops tags, so there is nothing to recreate.
    op.alter_column('users', 'name',
               existing_type=sa.String(length=200),
               type_=mysql.VARCHAR(length=100),
               existing_nullable=False)
    op.alter_column('tasks', 'title',
               existing_type=sa.String(length=300),
               type_=mysql.VARCHAR(length=255),
               existing_nullable=False)