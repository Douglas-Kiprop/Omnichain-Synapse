from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251125_create_strategies"
down_revision = "41c0f6fe878d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "strategies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("notification_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_strategies_user_status", "strategies", ["user_id", "status"])
    op.create_unique_constraint("uq_strategies_user_name", "strategies", ["user_id", "name"])


def downgrade():
    op.drop_constraint("uq_strategies_user_name", "strategies", type_="unique")
    op.drop_index("idx_strategies_user_status", table_name="strategies")
    op.drop_table("strategies")