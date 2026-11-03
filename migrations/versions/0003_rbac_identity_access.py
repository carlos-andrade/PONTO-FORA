"""Persist internal identities, RBAC catalog, grants and authorization audit.

Revision ID: 0003_rbac_identity_access
Revises: 0002_evidence_domain
"""
import uuid

import sqlalchemy as sa
from alembic import op

revision = "0003_rbac_identity_access"
down_revision = "0002_evidence_domain"
branch_labels = None
depends_on = None

ROLE_DESCRIPTIONS = {
    "PLATFORM_ADMIN": "Gestão técnica de utilizadores, identidades e papéis.",
    "EDITORIAL_DIRECTOR": "Triagem e decisões editoriais autorizadas.",
    "INVESTIGATOR": "Registo de fontes, alegações e evidências.",
    "FACT_CHECKER": "Avaliação factual de alegações e evidências.",
    "WRITER": "Criação de versões de texto editorial.",
    "EDITOR": "Revisão editorial e solicitação de alterações.",
    "SOCIAL_EDITOR": "Criação de derivados para redes sociais.",
    "PUBLISHER": "Execução de publicação previamente autorizada.",
    "AUDITOR": "Consulta de registos de auditoria.",
    "SYSTEM_ORCHESTRATOR": "Execução de tarefas técnicas explicitamente autorizadas.",
}

PERMISSION_DESCRIPTIONS = {
    "identity.manage": "Gerir identidades internas e associações OIDC.",
    "roles.manage": "Conceder e revogar papéis de utilizadores.",
    "assignments.read": "Consultar pautas.",
    "assignments.create": "Criar pautas.",
    "assignments.triage": "Executar operações técnicas de triagem.",
    "sources.write": "Registar fontes e evidências.",
    "factcheck.assess": "Registar avaliações factuais.",
    "artifacts.write": "Criar versões de artefactos editoriais.",
    "artifacts.review": "Rever artefactos e solicitar alterações.",
    "editorial.decide": "Tomar decisões editoriais.",
    "social.create": "Criar derivados para redes sociais.",
    "distribution.authorize": "Autorizar distribuição por canal.",
    "publication.execute": "Executar publicação autorizada.",
    "audit.read": "Consultar registos de auditoria.",
    "workflow.execute": "Executar tarefas técnicas do workflow.",
}

ROLE_PERMISSIONS = {
    "PLATFORM_ADMIN": {"identity.manage", "roles.manage", "assignments.read", "audit.read"},
    "EDITORIAL_DIRECTOR": {
        "assignments.read", "assignments.triage", "artifacts.review",
        "editorial.decide", "distribution.authorize", "audit.read",
    },
    "INVESTIGATOR": {"assignments.read", "sources.write"},
    "FACT_CHECKER": {"assignments.read", "sources.write", "factcheck.assess"},
    "WRITER": {"assignments.read", "artifacts.write"},
    "EDITOR": {"assignments.read", "artifacts.write", "artifacts.review"},
    "SOCIAL_EDITOR": {"assignments.read", "social.create"},
    "PUBLISHER": {"assignments.read", "publication.execute"},
    "AUDITOR": {"audit.read"},
    "SYSTEM_ORCHESTRATOR": {
        "assignments.read", "assignments.create", "assignments.triage",
        "sources.write", "publication.execute", "audit.read", "workflow.execute",
    },
}


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(240)),
        sa.Column("email", sa.String(320)),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE','DISABLED')", name="ck_users_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "external_identities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("issuer", sa.String(2048), nullable=False),
        sa.Column("subject", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issuer", "subject", name="uq_external_identity_issuer_subject"),
    )
    op.create_index("ix_external_identity_user", "external_identities", ["user_id"])
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_permission", "role_permissions", ["permission_id"])
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("scope_type", sa.String(64)),
        sa.Column("scope_id", sa.String(160)),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.Column("granted_by", sa.String(160), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_by", sa.String(160)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED')", name="ck_user_roles_status"),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_user_roles_validity",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_roles_user_status", "user_roles", ["user_id", "status"])
    op.create_index("ix_user_roles_role_status", "user_roles", ["role_id", "status"])
    op.create_table(
        "authorization_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("role_key", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_authorization_events_user_time", "authorization_events", ["user_id", "occurred_at"]
    )
    op.create_index(
        "ix_authorization_events_actor_time", "authorization_events", ["actor_id", "occurred_at"]
    )

    role_ids = {key: uuid.uuid4() for key in ROLE_DESCRIPTIONS}
    permission_ids = {key: uuid.uuid4() for key in PERMISSION_DESCRIPTIONS}
    roles = [
        {"id": role_ids[key], "key": key, "description": value, "is_active": True}
        for key, value in ROLE_DESCRIPTIONS.items()
    ]
    permissions = [
        {"id": permission_ids[key], "key": key, "description": value, "is_active": True}
        for key, value in PERMISSION_DESCRIPTIONS.items()
    ]
    op.bulk_insert(sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("key", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_active", sa.Boolean()),
    ), roles)
    op.bulk_insert(sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("key", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_active", sa.Boolean()),
    ), permissions)
    grants = [
        {"id": uuid.uuid4(), "role_id": role_ids[role], "permission_id": permission_ids[permission]}
        for role, permissions_for_role in ROLE_PERMISSIONS.items()
        for permission in permissions_for_role
    ]
    op.bulk_insert(sa.table(
        "role_permissions",
        sa.column("id", sa.Uuid()),
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    ), grants)

    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_authorization_event_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'authorization_events is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER trg_authorization_events_append_only
            BEFORE UPDATE OR DELETE ON authorization_events
            FOR EACH ROW EXECUTE FUNCTION prevent_authorization_event_mutation();
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS trg_authorization_events_append_only ON authorization_events"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_authorization_event_mutation()")
    op.drop_index("ix_authorization_events_actor_time", table_name="authorization_events")
    op.drop_index("ix_authorization_events_user_time", table_name="authorization_events")
    op.drop_table("authorization_events")
    op.drop_index("ix_user_roles_role_status", table_name="user_roles")
    op.drop_index("ix_user_roles_user_status", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_index("ix_role_permissions_permission", table_name="role_permissions")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_index("ix_external_identity_user", table_name="external_identities")
    op.drop_table("external_identities")
    op.drop_table("users")
