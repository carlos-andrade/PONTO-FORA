# PONTO-FORA — testes de persistência das execuções dos agentes
# Identificador: PF-TEST-AGENT-EXECUTION-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Atomicidade, idempotência, integridade referencial e ausência de avanço implícito.
# SHA-256 (conteúdo normalizado): 4309ffcd77474e7e92569c7ff7c2d54318bfa3955d83da2a862a8b18467cf279
# Commit de referência (base documental): 025804dfc3f79256d48e3c04aab9a15495893c5a

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from ponto_fora_api.db import Base
from ponto_fora_api.domain import Actor, ActorRole, ActorType, AssignmentStatus, DomainError
from ponto_fora_api.models import AgentExecution, Assignment, AuditEvent
from ponto_fora_api.schemas.agent_contract import AgentEnvelope, AgentId, ExecutionStatus
from ponto_fora_api.services.agent_executions import (
    AgentExecutionConflict,
    record_agent_execution,
)
from ponto_fora_api.services.assignments import create_assignment


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def orchestrator() -> Actor:
    return Actor(ActorType.SYSTEM, "orchestrator:v1", ActorRole.ORCHESTRATOR)


def build_envelope(assignment_id, **overrides) -> AgentEnvelope:
    payload = {
        "pauta_id": str(assignment_id),
        "artifact_id": "dossier-001",
        "artifact_version": "1.0",
        "agent_id": AgentId.INVESTIGADOR.value,
        "agent_version": "1.4",
        "prompt_version": "1.0",
        "execution_id": str(uuid4()),
        "input_artifact_ids": ["dossier-001"],
        "input_versions": {"dossier-001": "1.0"},
        "execution_status": ExecutionStatus.SUCCESS.value,
        "editorial_opinion": "APTO PARA FACT-CHECKING",
        "output_artifact_id": "investigation-001",
        "output_version": "1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "correlation_id": str(uuid4()),
    }
    payload.update(overrides)
    return AgentEnvelope.model_validate(payload)


def create_test_assignment(db, orchestrator):
    assignment, created = create_assignment(
        db,
        title="Pauta de teste",
        actor=orchestrator,
        idempotency_key=f"create-{uuid4()}",
    )
    assert created is True
    return assignment


def test_successful_execution_is_persisted_with_audit_event(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id)

    execution, created = record_agent_execution(db, envelope, actor=orchestrator)

    assert created is True
    assert execution.assignment_id == assignment.id
    assert execution.agent_id == AgentId.INVESTIGADOR.value
    assert execution.execution_status == ExecutionStatus.SUCCESS.value
    assert execution.mapped_target_status == AssignmentStatus.AGUARDANDO_FACT_CHECK.value
    assert execution.payload["editorial_opinion"] == "APTO PARA FACT-CHECKING"
    assert db.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.event_type == "AGENT_EXECUTION_RECORDED"
        )
    ) == 1


def test_recording_execution_does_not_advance_assignment_state(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    original_status = assignment.status
    original_version = assignment.row_version

    record_agent_execution(db, build_envelope(assignment.id), actor=orchestrator)

    db.refresh(assignment)
    assert assignment.status == original_status == AssignmentStatus.RECEBIDA.value
    assert assignment.row_version == original_version == 1


def test_failed_execution_is_persisted_without_editorial_target(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(
        assignment.id,
        execution_status=ExecutionStatus.FAILED.value,
        editorial_opinion="EXECUÇÃO FALHOU",
    )

    execution, created = record_agent_execution(db, envelope, actor=orchestrator)

    assert created is True
    assert execution.execution_status == ExecutionStatus.FAILED.value
    assert execution.mapped_target_status is None


def test_same_execution_envelope_is_idempotent(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id)

    first, created_first = record_agent_execution(db, envelope, actor=orchestrator)
    second, created_second = record_agent_execution(db, envelope, actor=orchestrator)

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert db.scalar(
        select(func.count()).select_from(AgentExecution)
    ) == 1
    assert db.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.event_type == "AGENT_EXECUTION_RECORDED"
        )
    ) == 1


def test_reused_execution_id_with_different_payload_is_rejected(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id)
    record_agent_execution(db, envelope, actor=orchestrator)
    changed = envelope.model_copy(update={"output_version": "2.0"})

    with pytest.raises(AgentExecutionConflict):
        record_agent_execution(db, changed, actor=orchestrator)


def test_unknown_successful_opinion_is_not_persisted(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id, editorial_opinion="APTO PARA FACT CHECK")

    with pytest.raises(ValueError):
        record_agent_execution(db, envelope, actor=orchestrator)

    assert db.scalar(select(func.count()).select_from(AgentExecution)) == 0


def test_unknown_assignment_is_rejected_without_partial_audit(db, orchestrator):
    envelope = build_envelope(uuid4())

    with pytest.raises(DomainError):
        record_agent_execution(db, envelope, actor=orchestrator)

    assert db.scalar(select(func.count()).select_from(AgentExecution)) == 0
    assert db.scalar(select(func.count()).select_from(AuditEvent)) == 0


def test_human_actor_cannot_impersonate_agent_orchestrator(db):
    assignment = create_test_assignment(
        db, Actor(ActorType.SYSTEM, "bootstrap", ActorRole.ORCHESTRATOR)
    )
    envelope = build_envelope(assignment.id)
    human = Actor(ActorType.HUMAN, "user:editor-01", ActorRole.EDITORIAL_DIRECTOR)

    with pytest.raises(DomainError):
        record_agent_execution(db, envelope, actor=human)

    assert db.scalar(select(func.count()).select_from(AgentExecution)) == 0
