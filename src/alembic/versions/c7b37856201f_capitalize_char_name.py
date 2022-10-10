"""capitalize char name

Revision ID: c7b37856201f
Revises: 6222825ed1c8
Create Date: 2022-10-10 17:51:36.207909

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7b37856201f'
down_revision = '6222825ed1c8'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE character SET name = INITCAP(LOWER(name));")


def downgrade():
    pass
