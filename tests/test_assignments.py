# PONTO-FORA — testes do núcleo editorial
# Identificador: PF-TEST-ASSIGNMENTS-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Persistência, idempotência, permissões, transições e auditoria.
# SHA-256 (conteúdo normalizado): PENDING
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from ponto_fora_api.db import Base
from ponto_fora_api.domain import (
    Actor,
    ActorRole,
    ActorType,
    AssignmentStatus,
    DomainError,
    InvalidTransition,
    PermissionDenied,
    VersionConflict,
)
from ponto_fora_api.models import Assignment, AuditEvent, IdempotencyRecord
from ponto_fora_api.services.assignments import (
    IdempotencyConflict,
    create_assignment,
    transition_assignment,
)


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
def system_actor() -> Actor:
    return Actor(ActorType.SYSTEM, "orchestrator:v1", ActorRole.ORCHESTRATOR)


@pytest.fixture
def director() -> Actor:
    return Actor(ActorType.HUMAN, "user:director-01", ActorRole.EDITORIAL_DIRECTOR)


def test_create_assignment_writes_initial_audit_event(db, system_actor) -> None:
    assignment, created = create_assignment(
        db, title="Notícia de teste", actor=system_actor, idempotency_key="create-001"
    )
    assert created is True
    assert assignment.status == AssignmentStatus.RECEBIDA.value
    assert assignment.row_version == 1
    assert db.scalar(select(func.count()).select_from(AuditEvent)) == 1


def test_create_assignment_is_idempotent(db, system_actor) -> None:
    first, created_first = create_assignment(
        db, title="Notícia idempotente", actor=system_actor, idempotency_key="same-key"
    )
    second, created_second = create_assignment(
        db, title="Notícia idempotente", actor=system_actor, idempotency_key="same-key"
    )
    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert db.scalar(select(func.count()).select_from(Assignment)) == 1
    assert db.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1


def test_reusing_idempotency_key_with_different_payload_fails(db, system_actor) -> None:
    create_assignment(
        db, title="Primeira pauta", actor=system_actor, idempotency_key="same-key"
    )
    with pytest.raises(IdempotencyConflict):
        create_assignment(
            db, title="Outra pauta", actor=system_actor, idempotency_key="same-key"
        )


def test_orchestrator_can_start_triage(db, system_actor) -> None:
    assignment, _ = create_assignment(
        db, title="Triagem", actor=system_actor, idempotency_key="triage-001"
    )
    changed = transition_assignment(
        db, assignment.id, target=AssignmentStatus.EM_TRIAGEM,
        actor=system_actor, expected_row_version=1, command_id=uuid4()
    )
    assert changed.status == AssignmentStatus.EM_TRIAGEM.value
    assert changed.row_version == 2
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at)).all()
    assert len(events) == 2
    assert events[-1].previous_status == AssignmentStatus.RECEBIDA.value
    assert events[-1].new_status == AssignmentStatus.EM_TRIAGEM.value


def test_director_can_release_triage_to_investigation(db, system_actor, director) -> None:
    assignment, _ = create_assignment(
        db, title="Triagem editorial", actor=system_actor, idempotency_key="triage-002"
    )
    transition_assignment(
        db, assignment.id, target=AssignmentStatus.EM_TRIAGEM,
        actor=system_actor, expected_row_version=1
    )
    changed = transition_assignment(
        db, assignment.id, target=AssignmentStatus.AGUARDANDO_INVESTIGACAO,
        actor=director, expected_row_version=2, command_id=uuid4(), reason="Escopo e relevância confirmados."
    )
    assert changed.status == AssignmentStatus.AGUARDANDO_INVESTIGACAO.value
    assert changed.row_version == 3


def test_wrong_role_cannot_release_triage(db, system_actor) -> None:
    assignment, _ = create_assignment(
        db, title="Permissões", actor=system_actor, idempotency_key="triage-003"
    )
    transition_assignment(
        db, assignment.id, target=AssignmentStatus.EM_TRIAGEM,
        actor=system_actor, expected_row_version=1
    )
    with pytest.raises(PermissionDenied):
        transition_assignment(
            db, assignment.id, target=AssignmentStatus.AGUARDANDO_INVESTIGACAO,
            actor=system_actor, expected_row_version=2, command_id=uuid4()
        )


def test_rejection_requires_reason(db, system_actor, director) -> None:
    assignment, _ = create_assignment(
        db, title="Rejeição", actor=system_actor, idempotency_key="triage-004"
    )
    transition_assignment(
        db, assignment.id, target=AssignmentStatus.EM_TRIAGEM,
        actor=system_actor, expected_row_version=1
    )
    with pytest.raises(DomainError):
        transition_assignment(
            db, assignment.id, target=AssignmentStatus.REJEITADA,
            actor=director, expected_row_version=2, command_id=uuid4()
        )


def test_unsupported_transition_is_rejected(db, system_actor) -> None:
    assignment, _ = create_assignment(
        db, title="Sem atalhos", actor=system_actor, idempotency_key="triage-005"
    )
    with pytest.raises(InvalidTransition):
        transition_assignment(
            db, assignment.id, target=AssignmentStatus.EM_INVESTIGACAO,
            actor=system_actor, expected_row_version=1
        )


def test_stale_row_version_is_rejected(db, system_actor) -> None:
    assignment, _ = create_assignment(
        db, title="Concorrência", actor=system_actor, idempotency_key="triage-006"
    )
    transition_assignment(
        db, assignment.id, target=AssignmentStatus.EM_TRIAGEM,
        actor=system_actor, expected_row_version=1
    )
    with pytest.raises(VersionConflict):
        transition_assignment(
            db, assignment.id, target=AssignmentStatus.EM_TRIAGEM,
            actor=system_actor, expected_row_version=1
        )


def test_missing_assignment_is_rejected(db, system_actor) -> None:
    with pytest.raises(DomainError):
        transition_assignment(
            db, uuid4(), target=AssignmentStatus.EM_TRIAGEM,
            actor=system_actor, expected_row_version=1
        )
