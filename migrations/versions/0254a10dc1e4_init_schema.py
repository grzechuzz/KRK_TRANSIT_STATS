"""init schema

Revision ID: 0254a10dc1e4
Revises: 
Create Date: 2025-12-22 02:47:32.762391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0254a10dc1e4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('gtfs_meta',
    sa.Column('id', sa.SmallInteger(), nullable=False),
    sa.Column('current_hash', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('stop_events',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('line_number', sa.Text(), nullable=False),
    sa.Column('stop_name', sa.Text(), nullable=False),
    sa.Column('stop_sequence', sa.Integer(), nullable=False),
    sa.Column('direction_id', sa.SmallInteger(), nullable=True),
    sa.Column('planned_time', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('event_time', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('delay_seconds', sa.Integer(), nullable=False),
    sa.Column('vehicle_label', sa.Text(), nullable=True),
    sa.Column('is_estimated', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('headsign', sa.Text(), nullable=True),
    sa.Column('service_date', sa.Date(), nullable=False),
    sa.Column('trip_id', sa.Text(), nullable=False),
    sa.Column('stop_id', sa.Text(), nullable=False),
    sa.Column('static_hash', sa.Text(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        "current_routes",
        sa.Column("route_id", sa.Text(), nullable=False),
        sa.Column("route_short_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("route_id")
    )

    op.create_table(
        "current_stops",
        sa.Column("stop_id", sa.Text(), nullable=False),
        sa.Column("stop_name", sa.Text(), nullable=False),
        sa.Column("stop_code", sa.Text(), nullable=True),
        sa.Column("stop_desc", sa.Text(), nullable=True),
        sa.Column("stop_lat", sa.Double(), nullable=True),
        sa.Column("stop_lon", sa.Double(), nullable=True),
        sa.PrimaryKeyConstraint("stop_id")
    )

    op.create_table(
        "current_trips",
        sa.Column("trip_id", sa.Text(), nullable=False),
        sa.Column("route_id", sa.Text(), nullable=False),
        sa.Column("direction_id", sa.SmallInteger(), nullable=True),
        sa.Column("headsign", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("trip_id"),
        sa.ForeignKeyConstraint(["route_id"], ["current_routes.route_id"])
    )

    op.create_table(
        "current_stop_times",
        sa.Column("trip_id", sa.Text(), nullable=False),
        sa.Column("stop_sequence", sa.Integer(), nullable=False),
        sa.Column("stop_id", sa.Text(), nullable=False),
        sa.Column("arrival_seconds", sa.Integer(), nullable=False),
        sa.Column("departure_seconds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("trip_id", "stop_sequence"),
        sa.ForeignKeyConstraint(["stop_id"], ["current_stops.stop_id"])
    )

    op.create_index("idx_stop_events_line_time", "stop_events", ["line_number", "event_time"])
    op.create_index("idx_stop_events_stop_time", "stop_events", ["stop_id", "event_time"])
    op.create_index("idx_stop_events_trip_date", "stop_events", ["trip_id", "service_date"])
    op.create_unique_constraint("uq_stop_events_trip_date_seq", "stop_events", ["trip_id", "service_date", "stop_sequence"])



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_stop_events_trip_date_seq", "stop_events", type_="unique")
    op.drop_index("idx_stop_events_trip_date", table_name="stop_events")
    op.drop_index("idx_stop_events_stop_time", table_name="stop_events")
    op.drop_index("idx_stop_events_line_time", table_name="stop_events")

    op.drop_table('stop_events')

    op.drop_table("current_stop_times")
    op.drop_table("current_trips")
    op.drop_table("current_stops")
    op.drop_table("current_routes")

    op.drop_table("gtfs_meta")
