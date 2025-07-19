"""Add donation model

Revision ID: 584eb52c274e
Revises: 6868acae0bfc
Create Date: 2025-07-19 01:17:44.788716

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "584eb52c274e"
down_revision: str | None = "6868acae0bfc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("donor_id", sa.Integer(), nullable=False),
        sa.Column("organizer_id", sa.Integer(), nullable=False),
        sa.Column("donor_day_id", sa.Integer(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["donor_day_id"], ["donor_days.id"], name=op.f("fk_donations_donor_day_id_donor_days")),
        sa.ForeignKeyConstraint(["donor_id"], ["donors.id"], name=op.f("fk_donations_donor_id_donors")),
        sa.ForeignKeyConstraint(["organizer_id"], ["organizers.id"], name=op.f("fk_donations_organizer_id_organizers")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donations")),
    )


def downgrade() -> None:
    op.drop_table("donations")
