"""initial schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


order_status = postgresql.ENUM(
    "NEW", "ASSIGNED", "PICKED_UP", "DELIVERED", "PROBLEM", "CANCELED", name="order_status"
)
order_priority = postgresql.ENUM("VIP", "URGENT", "NORMAL", name="order_priority")
reason_type = postgresql.ENUM("PROBLEM", "CANCELED", name="reason_type")
batch_status = postgresql.ENUM("ACTIVE", "COMPLETED", name="batch_status")

order_status_ref = postgresql.ENUM(
    "NEW",
    "ASSIGNED",
    "PICKED_UP",
    "DELIVERED",
    "PROBLEM",
    "CANCELED",
    name="order_status",
    create_type=False,
)
order_priority_ref = postgresql.ENUM(
    "VIP",
    "URGENT",
    "NORMAL",
    name="order_priority",
    create_type=False,
)
reason_type_ref = postgresql.ENUM(
    "PROBLEM",
    "CANCELED",
    name="reason_type",
    create_type=False,
)
batch_status_ref = postgresql.ENUM(
    "ACTIVE",
    "COMPLETED",
    name="batch_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    order_status.create(bind, checkfirst=True)
    order_priority.create(bind, checkfirst=True)
    reason_type.create(bind, checkfirst=True)
    batch_status.create(bind, checkfirst=True)

    op.create_table(
        "couriers",
        sa.Column("tg_user_id", sa.BigInteger(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "pickup_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address_text", sa.String(length=500), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("base_eta_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "problem_reasons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("type", reason_type_ref, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("courier_id", sa.BigInteger(), sa.ForeignKey("couriers.tg_user_id"), nullable=False),
        sa.Column("status", batch_status_ref, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "courier_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("courier_id", sa.BigInteger(), sa.ForeignKey("couriers.tg_user_id"), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_phone", sa.String(length=32), nullable=False),
        sa.Column("recipient_name", sa.String(length=255), nullable=False),
        sa.Column("recipient_phone", sa.String(length=32), nullable=False),
        sa.Column("delivery_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("address_text", sa.String(length=500), nullable=False),
        sa.Column("entrance", sa.String(length=32), nullable=True),
        sa.Column("floor", sa.String(length=32), nullable=True),
        sa.Column("apartment", sa.String(length=32), nullable=True),
        sa.Column("intercom_code", sa.String(length=32), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("pickup_point_id", sa.Integer(), sa.ForeignKey("pickup_points.id"), nullable=False),
        sa.Column("status", order_status_ref, nullable=False, server_default="NEW"),
        sa.Column("priority", order_priority_ref, nullable=False, server_default="NORMAL"),
        sa.Column("assigned_courier_id", sa.BigInteger(), sa.ForeignKey("couriers.tg_user_id"), nullable=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("batches.id"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("picked_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("eta_minutes", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("problem_reason", sa.Text(), nullable=True),
        sa.Column("canceled_reason", sa.Text(), nullable=True),
        sa.Column("proof_photo_file_id", sa.String(length=255), nullable=True),
        sa.Column("proof_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index("ix_orders_order_number", "orders", ["order_number"])
    op.create_index("ix_orders_customer_phone", "orders", ["customer_phone"])
    op.create_index("ix_orders_recipient_phone", "orders", ["recipient_phone"])
    op.create_index("ix_orders_address_text", "orders", ["address_text"])
    op.create_index("ix_orders_delivery_window_end", "orders", ["delivery_window_end"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_priority", "orders", ["priority"])
    op.create_index("ix_orders_assigned_courier_id", "orders", ["assigned_courier_id"])
    op.create_index("ix_orders_batch_id", "orders", ["batch_id"])

    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("old_status", order_status_ref, nullable=True),
        sa.Column("new_status", order_status_ref, nullable=False),
        sa.Column("actor_tg_user_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_order_status_history_order_id", "order_status_history", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_order_status_history_order_id", table_name="order_status_history")
    op.drop_table("order_status_history")
    op.drop_index("ix_orders_batch_id", table_name="orders")
    op.drop_index("ix_orders_assigned_courier_id", table_name="orders")
    op.drop_index("ix_orders_priority", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_delivery_window_end", table_name="orders")
    op.drop_index("ix_orders_address_text", table_name="orders")
    op.drop_index("ix_orders_recipient_phone", table_name="orders")
    op.drop_index("ix_orders_customer_phone", table_name="orders")
    op.drop_index("ix_orders_order_number", table_name="orders")
    op.drop_table("orders")
    op.drop_table("courier_locations")
    op.drop_table("batches")
    op.drop_table("problem_reasons")
    op.drop_table("pickup_points")
    op.drop_table("couriers")

    bind = op.get_bind()
    batch_status.drop(bind, checkfirst=True)
    reason_type.drop(bind, checkfirst=True)
    order_priority.drop(bind, checkfirst=True)
    order_status.drop(bind, checkfirst=True)
