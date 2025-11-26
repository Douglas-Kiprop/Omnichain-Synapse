"""Revamp strategy models: normalized conditions, logic_tree, status enum"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4
import json

# revision identifiers, used by Alembic.
revision = "b6c2f51c9b1e"
down_revision = '20251125_create_strategies'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # 1) Create enum type for strategies.status
    strategy_status_enum = sa.Enum("active", "paused", "archived", "error", name="strategy_status")
    strategy_status_enum.create(bind, checkfirst=True)

    # 2) Create new tables
    op.create_table(
        "strategy_conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("type", sa.String(), nullable=False, index=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "strategy_trigger_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("triggered_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("message", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
    )

    # 3) Add new columns to strategies
    op.add_column("strategies", sa.Column("logic_tree", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("strategies", sa.Column("condition_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("strategies", sa.Column("schedule", sa.String(), nullable=False, server_default="1m"))
    op.add_column("strategies", sa.Column("assets", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    # Ensure notification_preferences has a default (column already exists in prior schema)
    op.alter_column("strategies", "notification_preferences", server_default=sa.text("'{}'::jsonb"), existing_type=postgresql.JSONB(astext_type=sa.Text()))
    op.add_column("strategies", sa.Column("required_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("strategies", sa.Column("last_run_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("strategies", sa.Column("last_triggered_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("strategies", sa.Column("trigger_count", sa.Integer(), nullable=False, server_default="0"))

    # 4) Convert status from VARCHAR to strategy_status enum
    op.alter_column("strategies", "status", existing_type=sa.String(), existing_nullable=False, server_default=None)

    # Map any legacy values; old schema may include 'triggered' -> map to 'active'
    op.execute("UPDATE strategies SET status = 'active' WHERE status = 'triggered'")
    op.execute("ALTER TABLE strategies ALTER COLUMN status TYPE strategy_status USING status::strategy_status")

    # Set a new default value for the status column after type conversion
    op.alter_column("strategies", "status", existing_type=strategy_status_enum, existing_nullable=False, server_default=sa.text("'active'::strategy_status"))

    # 5) Migrate existing 'conditions' JSONB and 'frequency' to normalized tables and new fields
    #   - For each strategy:
    #       * create condition rows using best-effort type inference
    #       * set logic_tree to AND of all condition refs
    #       * set condition_ids to list of new UUIDs
    #       * derive assets from payloads where applicable
    conn = bind
    rows = conn.execute(sa.text("SELECT id, conditions, frequency FROM strategies")).fetchall()
    for row in rows:
        strategy_id = row[0]
        conditions = row[1]
        frequency = row[2]

        new_cond_ids = []
        assets = set()

        if isinstance(conditions, list):
            for cond in conditions:
                cid = str(uuid4())
                new_cond_ids.append(cid)

                # best-effort type inference
                inferred_type = cond.get("type")
                if not inferred_type:
                    if "indicator" in cond:
                        inferred_type = "technical_indicator"
                    elif "direction" in cond or "target_price" in cond or "price" in cond:
                        inferred_type = "price_alert"
                    else:
                        inferred_type = "legacy"

                payload = cond
                asset = payload.get("asset")
                if asset:
                    assets.add(asset)

                # Insert normalized conditions (use CAST for psycopg2-safe parameter casting)
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO strategy_conditions (id, strategy_id, type, payload, label, enabled)
                        VALUES (CAST(:id AS uuid), CAST(:sid AS uuid), :type, CAST(:payload AS jsonb), :label, :enabled)
                        """
                    ),
                    {
                        "id": cid,
                        "sid": str(strategy_id),
                        "type": inferred_type,
                        "payload": json.dumps(payload),
                        "label": cond.get("label"),
                        "enabled": True if cond.get("enabled", True) else False,
                    },
                )

        # Build logic_tree as AND of all refs
        logic_tree = {"operator": "AND", "conditions": [{"ref": cid} for cid in new_cond_ids]}
        conn.execute(
            sa.text(
                """
                UPDATE strategies
                SET logic_tree = CAST(:logic_tree AS jsonb),
                    condition_ids = CAST(:condition_ids AS jsonb),
                    schedule = COALESCE(:schedule, schedule),
                    assets = CAST(:assets AS jsonb)
                WHERE id = CAST(:sid AS uuid)
                """
            ),
            {
                "logic_tree": json.dumps(logic_tree),
                "condition_ids": json.dumps(new_cond_ids),
                "schedule": frequency if frequency else None,
                "assets": json.dumps(list(assets)),
                "sid": str(strategy_id),
            },
        )

    # 6) Drop old columns no longer used
    # Note: notification_preferences stays; conditions/frequency removed
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_column("conditions")
        batch_op.drop_column("frequency")

    # 7) Create index for common queries
    op.create_index("ix_strategies_user_status", "strategies", ["user_id", "status"])


def downgrade():
    bind = op.get_bind()

    # 1) Re-add legacy columns
    op.add_column("strategies", sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("strategies", sa.Column("frequency", sa.String(), nullable=False, server_default="1m"))

    # 2) Attempt to fold normalized conditions back into legacy 'conditions' list (best-effort)
    conn = bind
    rows = conn.execute(sa.text("SELECT id FROM strategies")).fetchall()
    for row in rows:
        sid = row[0]
        cond_rows = conn.execute(
            sa.text("SELECT payload FROM strategy_conditions WHERE strategy_id = CAST(:sid AS uuid)"),
            {"sid": str(sid)},
        ).fetchall()
        payloads = [r[0] for r in cond_rows] if cond_rows else []
        conn.execute(
            sa.text("UPDATE strategies SET conditions = :payloads::jsonb, frequency = schedule WHERE id = :sid::uuid"),
            {"payloads": json.dumps(payloads), "sid": str(sid)},
        )

    # 3) Drop new index
    op.drop_index("ix_strategies_user_status", table_name="strategies")

    # 4) Drop new columns
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_column("logic_tree")
        batch_op.drop_column("condition_ids")
        batch_op.drop_column("schedule")
        batch_op.drop_column("assets")
        batch_op.drop_column("required_data")
        batch_op.drop_column("last_run_at")
        batch_op.drop_column("last_triggered_at")
        batch_op.drop_column("trigger_count")

    # 5) Convert status back to VARCHAR and drop enum type
    op.execute("ALTER TABLE strategies ALTER COLUMN status TYPE VARCHAR USING status::text")
    strategy_status_enum = sa.Enum("active", "paused", "archived", "error", name="strategy_status")
    strategy_status_enum.drop(bind, checkfirst=True)

    # 6) Drop normalized tables
    op.drop_table("strategy_trigger_logs")
    op.drop_table("strategy_conditions")