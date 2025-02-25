"""add two columns in notifications table

Revision ID: a86e2b9385f7
Revises: 2785f4a2f98c
Create Date: 2025-02-25 14:05:10.265273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a86e2b9385f7'
down_revision: Union[str, None] = '2785f4a2f98c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notifications', sa.Column('job_id', sa.Uuid(), nullable=True))
    op.add_column('notifications', sa.Column('application_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(None, 'notifications', 'jobs', ['job_id'], ['uid'])
    op.create_foreign_key(None, 'notifications', 'applications', ['application_id'], ['uid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'notifications', type_='foreignkey')
    op.drop_constraint(None, 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'application_id')
    op.drop_column('notifications', 'job_id')
    # ### end Alembic commands ###
