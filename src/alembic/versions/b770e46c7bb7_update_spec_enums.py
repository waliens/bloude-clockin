"""update spec enums

Revision ID: b770e46c7bb7
Revises: 1df78b5885ed
Create Date: 2022-09-30 20:42:20.038026

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b770e46c7bb7'
down_revision = '1df78b5885ed'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE specenum ADD VALUE 'DK_UNHOLY'")
    op.execute("ALTER TYPE specenum ADD VALUE 'DK_FROST'")
    op.execute("ALTER TYPE specenum ADD VALUE 'PRIEST_HOLY'")
    op.execute("ALTER TYPE specenum ADD VALUE 'PRIEST_DISC'")


def downgrade():
    pass
