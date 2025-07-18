"""Add donor model

Revision ID: 6628055cd052
Revises:
Create Date: 2025-07-18 15:43:04.939559

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6628055cd052"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=255), nullable=False),
        sa.Column("donor_type", sa.Enum("STUDENT", "EMPLOYEE", "EXTERNAL", name="donortype"), nullable=False),
        sa.Column("student_group", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donors")),
    )


def downgrade() -> None:
    op.drop_table("donors")
