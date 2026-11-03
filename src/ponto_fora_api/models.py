# PONTO-FORA — modelos relacionais do núcleo editorial
# Identificador: PF-COD-MODELS-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Pautas, eventos append-only, tarefas, idempotência e versões imutáveis.
# SHA-256 (conteúdo normalizado): PENDING
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ponto_fora_api.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint("row_version >= 1", name="ck_assignments_row_version"),
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
    __table_args__ = (
        Index("ix_audit_assignment_time", "assignment_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False
    )
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
    assignment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False
    )
    task_key: Mapped[str] = mapped_column(String(240), nullable=False)
    task_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("scope", "idempotency_key", name="uq_idempotency_scope_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"
    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "artifact_type", "version_number", name="uq_artifact_version"
        ),
        CheckConstraint("version_number >= 1", name="ck_artifact_version_number"),
        Index("ix_artifacts_assignment_type", "assignment_id", "artifact_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False
    )
    artifact_type: Mapped[str] = mapped_column(String(80), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
