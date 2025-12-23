"""create-targets

Revision ID: 20240629093204
Revises: 20240620131951
Create Date: 2024-06-29 09:32:07.680181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240629093204"
down_revision = "20240620131951"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "targets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("key_result_id", sa.BigInteger(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("tenant_id_str", sa.String(), nullable=True),
        sa.Column("tenant_group_id_str", sa.String(), nullable=True),
        sa.Column("pv_tenant_id", sa.String(), nullable=False),
        sa.Column("pv_created_by", sa.String(), nullable=False),
        sa.Column("pv_last_updated_by", sa.String(), nullable=True),
        sa.Column("app_created_by", sa.String(), nullable=True),
        sa.Column("app_last_updated_by", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["key_result_id"],
            ["key_results.id"],
            name="targets_key_result_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_targets_key_result_id"), "targets", ["key_result_id"], unique=False
    )
    op.create_index(
        op.f("ix_targets_pv_tenant_id"), "targets", ["pv_tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_targets_tenant_group_id_str"),
        "targets",
        ["tenant_group_id_str"],
        unique=False,
    )
    op.create_index(
        op.f("ix_targets_tenant_id_str"), "targets", ["tenant_id_str"], unique=False
    )
    op.execute(
        """
            CREATE TRIGGER platforma_set_timestamp_trigger
            BEFORE UPDATE ON targets
            FOR EACH ROW
            EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
            ALTER TABLE targets ENABLE TRIGGER platforma_set_timestamp_trigger;
        """
    )
    op.add_column(
        "progress_points", sa.Column("target_id", sa.BigInteger(), nullable=True)
    )
    op.create_index(
        op.f("ix_progress_points_target_id"),
        "progress_points",
        ["target_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_progress_points_target_id"), table_name="progress_points")
    op.drop_column("progress_points", "target_id")
    op.execute("DROP TRIGGER IF EXISTS platforma_set_timestamp_trigger ON targets")
    op.drop_index(op.f("ix_targets_tenant_id_str"), table_name="targets")
    op.drop_index(op.f("ix_targets_tenant_group_id_str"), table_name="targets")
    op.drop_index(op.f("ix_targets_pv_tenant_id"), table_name="targets")
    op.drop_index(op.f("ix_targets_key_result_id"), table_name="targets")
    op.drop_table("targets")
