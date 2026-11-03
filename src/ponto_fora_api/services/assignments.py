# PONTO-FORA — serviços transacionais de pautas
# Identificador: PF-COD-ASSIGNMENTS-001
# Versão: 1.1
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Criação idempotente, transições atómicas e eventos de auditoria.
# SHA-256 (conteúdo normalizado): 4d16d85952bd3e8e6e2491b0de85490fc0b281f7b85980f584bc5be6c9d936fc
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

import hashlib
import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ponto_fora_api.domain import (
    Actor,
    AssignmentStatus,
    DomainError,
    VersionConflict,
    validate_transition,
)
from ponto_fora_api.models import Assignment, AuditEvent, IdempotencyRecord, utc_now


class IdempotencyConflict(DomainError):
    """A mesma chave foi reutilizada para um pedido diferente."""


def _payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _find_idempotent_result(
    db: Session, *, scope: str, key: str, request_hash: str
) -> Assignment | None:
    record = db.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == key,
        )
    )
    if record is None:
        return None
    if record.request_hash != request_hash:
        raise IdempotencyConflict("Chave de idempotência reutilizada com conteúdo diferente.")
    assignment = db.get(Assignment, record.resource_id)
    if assignment is None:
        raise DomainError("Registo de idempotência aponta para recurso inexistente.")
    return assignment


def create_assignment(
    db: Session,
    *,
    title: str,
    actor: Actor,
    idempotency_key: str,
    summary: str | None = None,
    origin_url: str | None = None,
    topic: str | None = None,
    target_audience: list[str] | None = None,
    priority: str = "normal",
    correlation_id: UUID | None = None,
) -> tuple[Assignment, bool]:
    clean_title = title.strip()
    if not clean_title:
        raise DomainError("O título da pauta é obrigatório.")
    if priority not in {"low", "normal", "high", "urgent"}:
        raise DomainError("Prioridade inválida.")
    if not idempotency_key.strip():
        raise DomainError("A chave de idempotência é obrigatória.")

    payload = {
        "title": clean_title,
        "summary": summary,
        "origin_url": origin_url,
        "topic": topic,
        "target_audience": target_audience or [],
        "priority": priority,
    }
    request_hash = _payload_hash(payload)
    scope = "assignment:create"
    existing = _find_idempotent_result(
        db, scope=scope, key=idempotency_key, request_hash=request_hash
    )
    if existing is not None:
        return existing, False

    assignment_id = uuid4()
    assignment = Assignment(
        id=assignment_id,
        reference_code=f"PF-{assignment_id.hex[:12].upper()}",
        title=clean_title,
        summary=summary,
        origin_url=origin_url,
        topic=topic,
        target_audience=target_audience or [],
        priority=priority,
        status=AssignmentStatus.RECEBIDA.value,
        row_version=1,
        created_by=actor.actor_id,
    )
    event = AuditEvent(
        assignment_id=assignment_id,
        event_type="ASSIGNMENT_CREATED",
        actor_type=actor.actor_type.value,
        actor_id=actor.actor_id,
        previous_status=None,
        new_status=AssignmentStatus.RECEBIDA.value,
        payload={"reference_code": assignment.reference_code, "request_hash": request_hash},
        correlation_id=correlation_id or uuid4(),
    )
    record = IdempotencyRecord(
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        resource_id=assignment_id,
    )
    db.add_all([assignment, event, record])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _find_idempotent_result(
            db, scope=scope, key=idempotency_key, request_hash=request_hash
        )
        if existing is not None:
            return existing, False
        raise
    db.refresh(assignment)
    return assignment, True


def transition_assignment(
    db: Session,
    assignment_id: UUID,
    *,
    target: AssignmentStatus,
    actor: Actor,
    expected_row_version: int,
    command_id: UUID,
    reason: str | None = None,
    correlation_id: UUID | None = None,
) -> Assignment:
    scope = f"assignment:transition:{assignment_id}"
    request_hash = _payload_hash(
        {
            "assignment_id": str(assignment_id),
            "target": target.value,
            "actor_type": actor.actor_type.value,
            "actor_id": actor.actor_id,
            "actor_role": actor.role.value,
            "expected_row_version": expected_row_version,
            "reason": reason,
        }
    )
    existing = _find_idempotent_result(
        db, scope=scope, key=str(command_id), request_hash=request_hash
    )
    if existing is not None:
        return existing

    assignment = db.scalar(
        select(Assignment).where(Assignment.id == assignment_id).with_for_update()
    )
    if assignment is None:
        raise DomainError("Pauta não encontrada.")
    # Revalidar a chave depois do lock: uma repetição concorrente pode ter
    # sido confirmada enquanto esta transação aguardava a linha.
    existing = _find_idempotent_result(
        db, scope=scope, key=str(command_id), request_hash=request_hash
    )
    if existing is not None:
        return existing
    if assignment.row_version != expected_row_version:
        raise VersionConflict(
            f"Versão desatualizada: esperada {expected_row_version}, "
            f"atual {assignment.row_version}."
        )
    current = AssignmentStatus(assignment.status)
    validate_transition(current, target, actor, reason)

    assignment.status = target.value
    assignment.row_version += 1
    assignment.updated_at = utc_now()
    event = AuditEvent(
        assignment_id=assignment.id,
        event_type="ASSIGNMENT_STATUS_CHANGED",
        actor_type=actor.actor_type.value,
        actor_id=actor.actor_id,
        previous_status=current.value,
        new_status=target.value,
        payload={"reason": reason, "row_version": assignment.row_version},
        correlation_id=correlation_id or uuid4(),
    )
    record = IdempotencyRecord(
        scope=scope,
        idempotency_key=str(command_id),
        request_hash=request_hash,
        resource_id=assignment.id,
    )
    db.add_all([event, record])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _find_idempotent_result(
            db, scope=scope, key=str(command_id), request_hash=request_hash
        )
        if existing is not None:
            return existing
        raise
    db.refresh(assignment)
    return assignment
