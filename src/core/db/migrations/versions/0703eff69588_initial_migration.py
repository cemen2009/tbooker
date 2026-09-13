"""initial migration

Revision ID: 0703eff69588
Revises: 
Create Date: 2026-09-13 17:06:55.140166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0703eff69588'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    
    op.create_table('cities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('country_code', sa.String(length=2), nullable=False, comment="ISO 3166-1 alpha-2 country code, e.g. 'UA', 'US'"),
    sa.Column('timezone', sa.String(length=50), nullable=False, comment="IANA timezone identifier, e.g. 'Europe/Kyiv'. Do not use fixed UTC offsets — they break under DST/political timezone shifts (e.g. Ukraine UTC+2/+3)."),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'country_code', name='uq_city_name_country_code')
    )
    op.create_table('restaurants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=125), nullable=False),
    sa.Column('description', sa.String(length=625), nullable=False),
    sa.Column('opens_at', sa.Time(), nullable=False),
    sa.Column('closes_at', sa.Time(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'active', 'deactivated', name='restaurantstatus'), server_default='pending', nullable=False),
    sa.Column('address', sa.String(length=255), nullable=False),
    sa.Column('city_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('name', 'city_id', name='uq_restaurant_name_city_id'),
    sa.UniqueConstraint('phone')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('first_name', sa.String(length=75), nullable=False),
    sa.Column('last_name', sa.String(length=90), nullable=False),
    sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
    sa.Column('status', sa.Enum('invited', 'active', 'inactive', name='userstatus'), nullable=False),
    sa.Column('city_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('tables',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('number', sa.String(length=32), nullable=False),
    sa.Column('status', sa.Enum('active', 'inactive', name='tablestatus'), nullable=False),
    sa.Column('capacity', sa.SmallInteger(), nullable=False),
    sa.Column('restaurant_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('capacity > 0', name='ck_table_capacity_is_positive'),
    sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('restaurant_id', 'number', name='uq_table_restaurant_number')
    )

    op.create_table('bookings',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('booking_date', sa.Date(), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('slot_count', sa.SmallInteger(), nullable=False),

    # removed because we implement time_range as a generated column below
    # sa.Column('time_range', postgresql.TSRANGE(), nullable=False, system=True),
    
    
    sa.Column('table_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['table_id'], ['tables.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.execute("""
        ALTER TABLE bookings
        ADD COLUMN time_range tsrange
        GENERATED ALWAYS AS (
            tsrange(
                (booking_date + start_time)::timestamp,
                (booking_date + start_time)::timestamp + (slot_count * interval '30 minutes')
            )
        ) STORED
    """)

    op.create_exclude_constraint(
        'ex_booking_no_overlap_per_table',
        'bookings',
        ('table_id', '='),
        ('time_range', '&&'),
        using='gist'
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table('bookings')
    op.execute("DROP EXTENSION IF EXISTS btree_gist")

    op.drop_table('tables')
    op.drop_table('users')
    op.drop_table('restaurants')
    op.drop_table('cities')
