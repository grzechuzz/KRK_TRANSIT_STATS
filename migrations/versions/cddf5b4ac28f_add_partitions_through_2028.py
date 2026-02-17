"""add partitions through 2028

Revision ID: cddf5b4ac28f
Revises: 2c1e7e354ac4
Create Date: 2026-02-17 16:47:22.464837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cddf5b4ac28f'
down_revision: Union[str, Sequence[str], None] = '2c1e7e354ac4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PARTITIONS = [
    # Rest of 2026
    ("stop_events_2026_05", "2026-05-01", "2026-06-01"),
    ("stop_events_2026_06", "2026-06-01", "2026-07-01"),
    ("stop_events_2026_07", "2026-07-01", "2026-08-01"),
    ("stop_events_2026_08", "2026-08-01", "2026-09-01"),
    ("stop_events_2026_09", "2026-09-01", "2026-10-01"),
    ("stop_events_2026_10", "2026-10-01", "2026-11-01"),
    ("stop_events_2026_11", "2026-11-01", "2026-12-01"),
    ("stop_events_2026_12", "2026-12-01", "2027-01-01"),
    # 2027
    ("stop_events_2027_01", "2027-01-01", "2027-02-01"),
    ("stop_events_2027_02", "2027-02-01", "2027-03-01"),
    ("stop_events_2027_03", "2027-03-01", "2027-04-01"),
    ("stop_events_2027_04", "2027-04-01", "2027-05-01"),
    ("stop_events_2027_05", "2027-05-01", "2027-06-01"),
    ("stop_events_2027_06", "2027-06-01", "2027-07-01"),
    ("stop_events_2027_07", "2027-07-01", "2027-08-01"),
    ("stop_events_2027_08", "2027-08-01", "2027-09-01"),
    ("stop_events_2027_09", "2027-09-01", "2027-10-01"),
    ("stop_events_2027_10", "2027-10-01", "2027-11-01"),
    ("stop_events_2027_11", "2027-11-01", "2027-12-01"),
    ("stop_events_2027_12", "2027-12-01", "2028-01-01"),
    # 2028
    ("stop_events_2028_01", "2028-01-01", "2028-02-01"),
    ("stop_events_2028_02", "2028-02-01", "2028-03-01"),
    ("stop_events_2028_03", "2028-03-01", "2028-04-01"),
    ("stop_events_2028_04", "2028-04-01", "2028-05-01"),
    ("stop_events_2028_05", "2028-05-01", "2028-06-01"),
    ("stop_events_2028_06", "2028-06-01", "2028-07-01"),
    ("stop_events_2028_07", "2028-07-01", "2028-08-01"),
    ("stop_events_2028_08", "2028-08-01", "2028-09-01"),
    ("stop_events_2028_09", "2028-09-01", "2028-10-01"),
    ("stop_events_2028_10", "2028-10-01", "2028-11-01"),
    ("stop_events_2028_11", "2028-11-01", "2028-12-01"),
    ("stop_events_2028_12", "2028-12-01", "2029-01-01"),
]


def upgrade() -> None:
    for name, start, end in _NEW_PARTITIONS:
        op.execute(
            f"CREATE TABLE {name} PARTITION OF stop_events "
            f"FOR VALUES FROM ('{start}') TO ('{end}')"
        )


def downgrade() -> None:
    for name, _, _ in reversed(_NEW_PARTITIONS):
        op.execute(f"DROP TABLE IF EXISTS {name}")
