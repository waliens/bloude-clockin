"""add recipes tables

Revision ID: 9bb8af50400e
Revises: 0a811bca3942
Create Date: 2022-08-31 15:48:05.454885

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9bb8af50400e'
down_revision = '0a811bca3942'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('recipe',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name_en', sa.String(length=255), nullable=True),
    sa.Column('name_fr', sa.String(length=255), nullable=True),
    sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('profession', sa.Enum('LEATHERWORKING', 'TAILORING', 'ENGINEERING', 'BLACKSMITHING', 'COOKING', 'ALCHEMY', 'FIRST_AID', 'ENCHANTING', 'FISHING', 'JEWELCRAFTING', 'INSCRIPTION', 'MINING', 'HERBALISM', 'SKINNING', name='professionenum'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_recipe',
    sa.Column('id_recipe', sa.Integer(), nullable=False),
    sa.Column('id_character', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_character'], ['character.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['id_recipe'], ['recipe.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id_recipe', 'id_character')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_recipe')
    op.drop_table('recipe')
    # ### end Alembic commands ###
