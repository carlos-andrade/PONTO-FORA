# PONTO-FORA — modelos relacionais do núcleo editorial e factual
# Identificador: PF-COD-MODELS-001
# Versão: 1.2
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Pautas, auditoria, tarefas, versões, fontes, afirmações e fact-checking.
# Inclui registo imutável das execuções dos agentes editoriais.
# SHA-256 (conteúdo normalizado): 8cead1ebce063d342ccfebf55a097ced207258f3f92e87123329f26196255cf4
# Commit de referência (base documental): 025804dfc3f79256d48e3c04aab9a15495893c5a

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from ponto_fora_api.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint("row_version >= 1", name="ck_assignments_row_version"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')",
            name="ck_assignments_priority"),
        Index("ix_assignments_status_updated", "status", "updated_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    reference_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_audience: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(48), nullable=False, default="RECEBIDA")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_assignment_time", "assignment_id", "occurred_at"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(48), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(48), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"
    __table_args__ = (
        UniqueConstraint("task_key", name="uq_workflow_tasks_task_key"),
        Index("ix_workflow_tasks_assignment_status", "assignment_id", "status"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False)
    task_key: Mapped[str] = mapped_column(String(240), nullable=False)
    task_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("scope", "idempotency_key",
        name="uq_idempotency_scope_key"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("assignments.id",
        ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "artifact_type", "version_number",
            name="uq_artifact_version"),
        CheckConstraint("version_number >= 1", name="ck_artifact_version_number"),
        CheckConstraint("length(content_sha256) = 64", name="ck_artifact_sha256_length"),
        Index("ix_artifacts_assignment_type", "assignment_id", "artifact_type"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(80), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SourceRecord(Base):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("id", "assignment_id", name="uq_source_id_assignment"),
        CheckConstraint((
            "source_type IN ('PRIMARY','SECONDARY','REFERENCE"
            "','SOCIAL','UNKNOWN')"
        ), name="ck_source_type"),
        CheckConstraint((
            "access_status IN"
            " ('AVAILABLE','UNAVAILABLE','RESTRICTED','REMOVE"
            "D','NOT_CHECKED')"
        ), name="ck_source_access_status"),
        CheckConstraint("content_sha256 IS NULL OR length(content_sha256) = 64",
            name="ck_source_sha256"),
        Index("ix_sources_assignment_retrieved", "assignment_id", "retrieved_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(240))
    author: Mapped[str | None] = mapped_column(String(240))
    source_type: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at_source: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utc_now)
    language: Mapped[str | None] = mapped_column(String(24))
    content_sha256: Mapped[str | None] = mapped_column(String(64))
    storage_uri: Mapped[str | None] = mapped_column(String(2048))
    access_status: Mapped[str] = mapped_column(String(24), nullable=False, default="NOT_CHECKED")
    independence_group: Mapped[str | None] = mapped_column(String(240))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (
        UniqueConstraint("id", "assignment_id", name="uq_claim_id_assignment"),
        CheckConstraint((
            "claim_type IN ('FACTUAL','QUANTITATIVE','QUOTE',"
            "'DATE','CAUSAL','PREDICTIVE','OPINION','MIXED')"
        ), name="ck_claim_type"),
        CheckConstraint("materiality IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_claim_materiality"),
        ForeignKeyConstraint(["supersedes_claim_id", "assignment_id"], ["claims.id",
            "claims.assignment_id"], ondelete="RESTRICT",
                name="fk_claim_supersedes_same_assignment"),
        Index("ix_claims_assignment_materiality", "assignment_id", "materiality"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(24), nullable=False, default="FACTUAL")
    materiality: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM")
    attribution: Mapped[str | None] = mapped_column(Text)
    context_note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utc_now)
    supersedes_claim_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint("id", "assignment_id", name="uq_evidence_id_assignment"),
        ForeignKeyConstraint(["source_id", "assignment_id"], ["source_records.id",
            "source_records.assignment_id"], ondelete="RESTRICT",
                name="fk_evidence_source_same_assignment"),
        CheckConstraint((
            "evidence_type IN"
            " ('DOCUMENT','DATASET','QUOTE','IMAGE','AUDIO','"
            "VIDEO','OBSERVATION','OTHER')"
        ), name="ck_evidence_type"),
        CheckConstraint("polarity IN ('SUPPORTS','CONTRADICTS','CONTEXTUALIZES','NEUTRAL')",
            name="ck_evidence_polarity"),
        CheckConstraint("content_sha256 IS NULL OR length(content_sha256) = 64",
            name="ck_evidence_sha256"),
        Index("ix_evidence_assignment_collected", "assignment_id", "collected_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    locator: Mapped[str] = mapped_column(String(2048), nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(24), nullable=False, default="OTHER")
    polarity: Mapped[str] = mapped_column(String(24), nullable=False, default="NEUTRAL")
    collected_by: Mapped[str] = mapped_column(String(160), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utc_now)
    content_sha256: Mapped[str | None] = mapped_column(String(64))
    limitations: Mapped[str | None] = mapped_column(Text)


class ClaimEvidenceLink(Base):
    __tablename__ = "claim_evidence_links"
    __table_args__ = (
        UniqueConstraint("claim_id", "evidence_id", name="uq_claim_evidence_pair"),
        ForeignKeyConstraint(["claim_id", "assignment_id"], ["claims.id",
            "claims.assignment_id"], ondelete="RESTRICT", name="fk_link_claim_same_assignment"),
        ForeignKeyConstraint(["evidence_id", "assignment_id"], ["evidence_records.id",
            "evidence_records.assignment_id"], ondelete="RESTRICT",
                name="fk_link_evidence_same_assignment"),
        CheckConstraint((
            "relationship IN ('SUPPORTS','CONTRADICTS','CONTE"
            "XTUALIZES','DOES_NOT_ADDRESS')"
        ), name="ck_claim_evidence_relationship"),
        Index("ix_claim_evidence_assignment", "assignment_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    claim_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    assessed_by: Mapped[str] = mapped_column(String(160), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utc_now)
    assessment_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class FactCheckAssessment(Base):
    __tablename__ = "fact_check_assessments"
    __table_args__ = (
        UniqueConstraint("id", "assignment_id", name="uq_assessment_id_assignment"),
        UniqueConstraint("assignment_id", "claim_id", "assessment_version",
            name="uq_assessment_claim_version"),
        ForeignKeyConstraint(["claim_id", "assignment_id"], ["claims.id",
            "claims.assignment_id"], ondelete="RESTRICT",
                name="fk_assessment_claim_same_assignment"),
        ForeignKeyConstraint(["supersedes_assessment_id", "assignment_id"],
            ["fact_check_assessments.id", "fact_check_assessments.assignment_id"],
                ondelete="RESTRICT", name="fk_assessment_supersedes_same_assignment"),
        CheckConstraint((
            "verdict IN ('CONFIRMADA','MAIORITARIAMENTE_CONFI"
            "RMADA','PARCIALMENTE_CONFIRMADA','ENGANOSA','DES"
            "CONTEXTUALIZADA','CONTRADITA','NAO_COMPROVADA','"
            "INCONCLUSIVA','DESATUALIZADA','NAO_FACTUAL')"
        ), name="ck_fact_check_verdict"),
        CheckConstraint("reviewer_type IN ('HUMAN','AI')", name="ck_assessment_reviewer_type"),
        CheckConstraint("assessment_version >= 1", name="ck_assessment_version"),
        Index("ix_assessments_assignment_claim", "assignment_id", "claim_id", "assessment_version"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False)
    claim_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    limitations: Mapped[str | None] = mapped_column(Text)
    reviewer_type: Mapped[str] = mapped_column(String(8), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(160), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utc_now)
    assessment_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    supersedes_assessment_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))



class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','DISABLED')", name="ck_users_status"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    display_name: Mapped[str | None] = mapped_column(String(240))
    email: Mapped[str | None] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class ExternalIdentity(Base):
    __tablename__ = "external_identities"
    __table_args__ = (
        UniqueConstraint("issuer", "subject", name="uq_external_identity_issuer_subject"),
        Index("ix_external_identity_user", "user_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    issuer: Mapped[str] = mapped_column(String(2048), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("ix_role_permissions_permission", "permission_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    role_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    permission_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("permissions.id", ondelete="RESTRICT"), nullable=False
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','REVOKED')", name="ck_user_roles_status"),
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_user_roles_validity",
        ),
        Index("ix_user_roles_user_status", "user_id", "status"),
        Index("ix_user_roles_role_status", "role_id", "status"),
        Index(
            "uq_user_roles_active_global",
            "user_id",
            "role_id",
            unique=True,
            sqlite_where=sql_text(
                "status = 'ACTIVE' AND scope_type IS NULL AND scope_id IS NULL"
            ),
            postgresql_where=sql_text(
                "status = 'ACTIVE' AND scope_type IS NULL AND scope_id IS NULL"
            ),
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    role_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    scope_type: Mapped[str | None] = mapped_column(String(64))
    scope_id: Mapped[str | None] = mapped_column(String(160))
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    granted_by: Mapped[str] = mapped_column(String(160), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    revoked_by: Mapped[str | None] = mapped_column(String(160))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthorizationEvent(Base):
    __tablename__ = "authorization_events"
    __table_args__ = (
        Index("ix_authorization_events_user_time", "user_id", "occurred_at"),
        Index("ix_authorization_events_actor_time", "actor_id", "occurred_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    role_key: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class SystemBootstrap(Base):
    __tablename__ = "system_bootstrap"
    __table_args__ = (
        CheckConstraint("bootstrap_key = 'initial-admin'", name="ck_system_bootstrap_key"),
    )
    bootstrap_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    __table_args__ = (
        UniqueConstraint("execution_id", name="uq_agent_execution_id"),
        CheckConstraint(
            "execution_status IN ('SUCCESS','FAILED','RETRYABLE')",
            name="ck_agent_execution_status",
        ),
        CheckConstraint("length(request_sha256) = 64", name="ck_agent_execution_sha256"),
        Index("ix_agent_execution_assignment_created", "assignment_id", "created_at"),
        Index("ix_agent_execution_agent_status", "agent_id", "execution_status"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assignments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    execution_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(32), nullable=False)
    agent_version: Mapped[str] = mapped_column(String(40), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    artifact_id: Mapped[str] = mapped_column(String(160), nullable=False)
    artifact_version: Mapped[str] = mapped_column(String(40), nullable=False)
    output_artifact_id: Mapped[str] = mapped_column(String(160), nullable=False)
    output_version: Mapped[str] = mapped_column(String(40), nullable=False)
    execution_status: Mapped[str] = mapped_column(String(16), nullable=False)
    editorial_opinion: Mapped[str] = mapped_column(String(120), nullable=False)
    mapped_target_status: Mapped[str | None] = mapped_column(String(48))
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
