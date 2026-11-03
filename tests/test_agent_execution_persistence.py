# PONTO-FORA — testes de persistência das execuções dos agentes
# Identificador: PF-TEST-AGENT-EXECUTION-001
# Versão: 1.1
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Testes de atomicidade, idempotência, auditoria e gates editoriais.
# SHA-256 (conteúdo normalizado): 11c4cd252171323ae6893e046e50fdc601e17f393565d8ed85485fed41770696
# Commit de referência (base documental): 5d064a9430f0c8066ec0bbce4ab06d35b5232c8f

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from ponto_fora_api.db import Base
from ponto_fora_api.domain import (
    TRANSITION_POLICY,
    Actor,
    ActorRole,
    ActorType,
    AssignmentStatus,
    DomainError,
    InvalidTransition,
    PermissionDenied,
    VersionConflict,
)
from ponto_fora_api.models import AgentExecution, AuditEvent
from ponto_fora_api.schemas.agent_contract import AgentEnvelope, AgentId, ExecutionStatus
from ponto_fora_api.services.agent_executions import (
    AgentExecutionConflict,
    apply_agent_execution_transition,
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



def test_mapped_target_cannot_bypass_inactive_transition_policy(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id)
    record_agent_execution(db, envelope, actor=orchestrator)

    with pytest.raises(InvalidTransition):
        apply_agent_execution_transition(
            db,
            envelope.execution_id,
            actor=orchestrator,
            expected_row_version=1,
            command_id=uuid4(),
        )

    db.refresh(assignment)
    assert assignment.status == AssignmentStatus.RECEBIDA.value
    assert assignment.row_version == 1
    assert db.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.event_type == "AGENT_EXECUTION_STATE_TRANSITIONED"
        )
    ) == 0


def test_authorized_transition_is_atomic_and_idempotent(db, orchestrator, monkeypatch):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id)
    record_agent_execution(db, envelope, actor=orchestrator)
    transition = (
        AssignmentStatus.RECEBIDA,
        AssignmentStatus.AGUARDANDO_FACT_CHECK,
    )
    monkeypatch.setitem(TRANSITION_POLICY, transition, ActorRole.ORCHESTRATOR)
    monkeypatch.setattr(
        "ponto_fora_api.services.agent_executions.validate_agent_gate",
        lambda _db, _execution: None,
    )
    command_id = uuid4()

    changed, created = apply_agent_execution_transition(
        db,
        envelope.execution_id,
        actor=orchestrator,
        expected_row_version=1,
        command_id=command_id,
    )
    replayed, replay_created = apply_agent_execution_transition(
        db,
        envelope.execution_id,
        actor=orchestrator,
        expected_row_version=1,
        command_id=command_id,
    )

    assert created is True
    assert replay_created is False
    assert changed.id == replayed.id == assignment.id
    assert replayed.status == AssignmentStatus.AGUARDANDO_FACT_CHECK.value
    assert replayed.row_version == 2
    assert db.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.event_type == "AGENT_EXECUTION_STATE_TRANSITIONED"
        )
    ) == 1


def test_transition_rejects_stale_assignment_version(db, orchestrator, monkeypatch):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id)
    record_agent_execution(db, envelope, actor=orchestrator)
    monkeypatch.setitem(
        TRANSITION_POLICY,
        (AssignmentStatus.RECEBIDA, AssignmentStatus.AGUARDANDO_FACT_CHECK),
        ActorRole.ORCHESTRATOR,
    )

    with pytest.raises(VersionConflict):
        apply_agent_execution_transition(
            db,
            envelope.execution_id,
            actor=orchestrator,
            expected_row_version=2,
            command_id=uuid4(),
        )

    db.refresh(assignment)
    assert assignment.status == AssignmentStatus.RECEBIDA.value
    assert assignment.row_version == 1


def test_transition_requires_policy_actor_role(db, orchestrator, monkeypatch):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(assignment.id)
    record_agent_execution(db, envelope, actor=orchestrator)
    monkeypatch.setitem(
        TRANSITION_POLICY,
        (AssignmentStatus.RECEBIDA, AssignmentStatus.AGUARDANDO_FACT_CHECK),
        ActorRole.EDITORIAL_DIRECTOR,
    )

    with pytest.raises(PermissionDenied):
        apply_agent_execution_transition(
            db,
            envelope.execution_id,
            actor=orchestrator,
            expected_row_version=1,
            command_id=uuid4(),
        )

    db.refresh(assignment)
    assert assignment.status == AssignmentStatus.RECEBIDA.value


def test_failed_execution_cannot_apply_editorial_transition(db, orchestrator):
    assignment = create_test_assignment(db, orchestrator)
    envelope = build_envelope(
        assignment.id,
        execution_status=ExecutionStatus.FAILED.value,
        editorial_opinion="EXECUÇÃO FALHOU",
    )
    record_agent_execution(db, envelope, actor=orchestrator)

    with pytest.raises(DomainError):
        apply_agent_execution_transition(
            db,
            envelope.execution_id,
            actor=orchestrator,
            expected_row_version=1,
            command_id=uuid4(),
        )
