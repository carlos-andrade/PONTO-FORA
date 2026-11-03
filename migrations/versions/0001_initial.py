# PONTO-FORA — migração inicial do núcleo editorial
# Identificador: PF-MIG-0001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Criar pautas, auditoria, tarefas, idempotência e versões de artefactos.
# SHA-256 (conteúdo normalizado): PENDING
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference_code", sa.String(32), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("origin_url", sa.String(2048), nullable=True),
        sa.Column("topic", sa.String(120), nullable=True),
        sa.Column("target_audience", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(48), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("row_version >= 1", name="ck_assignments_row_version"),
        sa.CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')",
            name="ck_assignments_priority",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference_code"),
    )
    op.create_index("ix_assignments_status_updated", "assignments", ["status", "updated_at"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("actor_type", sa.String(24), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("previous_status", sa.String(48), nullable=True),
        sa.Column("new_status", sa.String(48), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_assignment_time", "audit_events", ["assignment_id", "occurred_at"])
    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("task_key", sa.String(240), nullable=False),
        sa.Column("task_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_key", name="uq_workflow_tasks_task_key"),
    )
    op.create_index(
        "ix_workflow_tasks_assignment_status", "workflow_tasks", ["assignment_id", "status"]
    )
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope", "idempotency_key", name="uq_idempotency_scope_key"),
    )
    op.create_table(
        "artifact_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_type", sa.String(80), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_uri", sa.String(2048), nullable=True),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_number >= 1", name="ck_artifact_version_number"),
        sa.CheckConstraint("length(content_sha256) = 64", name="ck_artifact_sha256_length"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id", "artifact_type", "version_number", name="uq_artifact_version"
        ),
    )
    op.create_index(
        "ix_artifacts_assignment_type", "artifact_versions", ["assignment_id", "artifact_type"]
    )

    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_audit_event_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'audit_events is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER trg_audit_events_append_only
            BEFORE UPDATE OR DELETE ON audit_events
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_event_mutation();
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_audit_events_append_only ON audit_events")
        op.execute("DROP FUNCTION IF EXISTS prevent_audit_event_mutation()")
    op.drop_index("ix_artifacts_assignment_type", table_name="artifact_versions")
    op.drop_table("artifact_versions")
    op.drop_table("idempotency_records")
    op.drop_index("ix_workflow_tasks_assignment_status", table_name="workflow_tasks")
    op.drop_table("workflow_tasks")
    op.drop_index("ix_audit_assignment_time", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_assignments_status_updated", table_name="assignments")
    op.drop_table("assignments")
