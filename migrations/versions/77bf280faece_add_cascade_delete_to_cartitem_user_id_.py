"""Add cascade delete to CartItem user_id foreign key

Revision ID: 77bf280faece
Revises: 3bd537eeaa7b
Create Date: 2025-08-10 19:02:56.485196

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77bf280faece'
down_revision = '3bd537eeaa7b'
branch_labels = None
depends_on = None


def upgrade():
    # Hernoem de oude tabel
    op.rename_table('cart_item', 'old_cart_item')

    # Maak nieuwe tabel met ON DELETE CASCADE
    op.create_table(
        'cart_item',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('item_id', sa.Integer, nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False, server_default='1')
    )

    # Kopieer data over
    op.execute('''
        INSERT INTO cart_item (id, user_id, item_type, item_id, quantity)
        SELECT id, user_id, item_type, item_id, quantity FROM old_cart_item
    ''')

    # Verwijder oude tabel
    op.drop_table('old_cart_item')

def downgrade():
    pass  # Optioneel om terug te draaien



    # ### end Alembic commands ###
