"""Rename event_date field to event_datetime

Revision ID: 6c3bfcd82630
Revises: 584eb52c274e
Create Date: 2025-07-19 01:48:22.177158

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6c3bfcd82630"
down_revision: str | None = "584eb52c274e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("donor_days", "event_date", new_column_name="event_datetime")


def downgrade() -> None:
    op.alter_column("donor_days", "event_datetime", new_column_name="event_date")
