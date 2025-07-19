"""Add donor day model

Revision ID: 6868acae0bfc
Revises: 8724dd06e971
Create Date: 2025-07-19 00:59:52.734719

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6868acae0bfc"
down_revision: str | None = "8724dd06e971"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donor_days",
        sa.Column("event_date", sa.DateTime(), nullable=False),
        sa.Column("organizer_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organizer_id"], ["organizers.id"], name=op.f("fk_donor_days_organizer_id_organizers")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donor_days")),
    )
    op.create_index(op.f("ix_donor_days_id"), "donor_days", ["id"], unique=False)
    op.create_index(op.f("ix_organizers_id"), "organizers", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_organizers_id"), table_name="organizers")
    op.drop_index(op.f("ix_donor_days_id"), table_name="donor_days")
    op.drop_table("donor_days")
