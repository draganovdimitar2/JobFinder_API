"""Rename first_name and last_name to firstName and lastName

Revision ID: af9541f64548
Revises: 937d0802b0e8
Create Date: 2024-12-23 12:12:31.523826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'af9541f64548'
down_revision: Union[str, None] = '937d0802b0e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('firstName', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('lastName', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('last_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('first_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('users', 'lastName')
    op.drop_column('users', 'firstName')
    # ### end Alembic commands ###
