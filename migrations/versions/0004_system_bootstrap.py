"""Add one-time initial administrator bootstrap marker.

Revision ID: 0004_system_bootstrap
Revises: 0003_rbac_identity_access
"""
import sqlalchemy as sa
from alembic import op

revision = "0004_system_bootstrap"
down_revision = "0003_rbac_identity_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_bootstrap",
        sa.Column("bootstrap_key", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "bootstrap_key = 'initial-admin'",
            name="ck_system_bootstrap_key",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("bootstrap_key"),
    )


def downgrade() -> None:
    op.drop_table("system_bootstrap")
