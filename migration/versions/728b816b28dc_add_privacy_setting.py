"""Add privacy setting

Revision ID: 728b816b28dc
Revises: None
Create Date: 2017-09-04 13:19:15.465769

"""

# revision identifiers, used by Alembic.
revision = '728b816b28dc'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('tg_user', sa.Column('privacy', sa.Enum('always', 'auth', 'admin'), nullable=False, server_default='always'))

def downgrade():
    op.drop_column('tg_user', 'privacy')
