# PONTO-FORA — migração de persistência das execuções dos agentes
# Identificador: PF-MIG-AGENT-EXECUTIONS-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Registo imutável de envelopes de execução, pareceres e mapeamentos editoriais.
# SHA-256 (conteúdo normalizado): ec13eaeef26586bd211a87b2b11cb6991131b714bfe82c2ee2ff79e374b934f6
# Commit de referência (base documental): ec13eaeef26586bd211a87b2b11cb6991131b714bfe82c2ee2ff79e374b934f6

"""Persist immutable agent execution envelopes.

Revision ID: 0005_agent_execution_records
Revises: 0004_system_bootstrap
"""
import sqlalchemy as sa
from alembic import op

revision = "0005_agent_execution_records"
down_revision = "0004_system_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.String(length=32), nullable=False),
        sa.Column("agent_version", sa.String(length=40), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("artifact_id", sa.String(length=160), nullable=False),
        sa.Column("artifact_version", sa.String(length=40), nullable=False),
        sa.Column("output_artifact_id", sa.String(length=160), nullable=False),
        sa.Column("output_version", sa.String(length=40), nullable=False),
        sa.Column("execution_status", sa.String(length=16), nullable=False),
        sa.Column("editorial_opinion", sa.String(length=120), nullable=False),
        sa.Column("mapped_target_status", sa.String(length=48), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "execution_status IN ('SUCCESS','FAILED','RETRYABLE')",
            name="ck_agent_execution_status",
        ),
        sa.CheckConstraint(
            "length(request_sha256) = 64",
            name="ck_agent_execution_sha256",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["assignments.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id", name="uq_agent_execution_id"),
    )
    op.create_index(
        "ix_agent_execution_assignment_created",
        "agent_executions",
        ["assignment_id", "created_at"],
    )
    op.create_index(
        "ix_agent_execution_agent_status",
        "agent_executions",
        ["agent_id", "execution_status"],
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_agent_execution_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'agent_executions is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER trg_agent_executions_append_only
            BEFORE UPDATE OR DELETE ON agent_executions
            FOR EACH ROW EXECUTE FUNCTION prevent_agent_execution_mutation();
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS trg_agent_executions_append_only ON agent_executions"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_agent_execution_mutation()")
    op.drop_index("ix_agent_execution_agent_status", table_name="agent_executions")
    op.drop_index("ix_agent_execution_assignment_created", table_name="agent_executions")
    op.drop_table("agent_executions")
