# PONTO-FORA — persistência transacional de execuções dos agentes
# Identificador: PF-COD-SVC-AGENT-EXECUTION-001
# Versão: 1.2
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software e Governança Editorial
# Âmbito: Persistência, gates de evidência e transições editoriais transacionais.
# Não permite avanço implícito do estado editorial.
# SHA-256 (conteúdo normalizado): 58ad4e35c03e24fe33c590cb88d7f0f0442730bf4d5e481ae8bd4c262f4ee36a
# Commit de referência (base documental): 3439b36f8468ce420cd46cb1135d98dc9170c6c8

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ponto_fora_api.domain import (
    Actor,
    ActorRole,
    ActorType,
    AssignmentStatus,
    DomainError,
    VersionConflict,
    validate_transition,
)
from ponto_fora_api.models import (
    AgentExecution,
    Assignment,
    AuditEvent,
    IdempotencyRecord,
    utc_now,
)
from ponto_fora_api.schemas.agent_contract import AgentEnvelope, ExecutionStatus
from ponto_fora_api.services.agent_gates import validate_agent_gate
from ponto_fora_api.services.orchestration import resolve_agent_envelope


class AgentExecutionConflict(DomainError):
    """O execution_id já existe associado a um envelope diferente."""


def _canonical_payload(envelope: AgentEnvelope) -> tuple[dict, str]:
    payload = envelope.model_dump(mode="json")
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return payload, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _find_execution(
    db: Session, execution_id, request_sha256: str
) -> AgentExecution | None:
    existing = db.scalar(
        select(AgentExecution).where(AgentExecution.execution_id == execution_id)
    )
    if existing is None:
        return None
    if existing.request_sha256 != request_sha256:
        raise AgentExecutionConflict(
            "execution_id reutilizado com conteúdo de envelope diferente."
        )
    return existing


def record_agent_execution(
    db: Session,
    envelope: AgentEnvelope,
    *,
    actor: Actor,
) -> tuple[AgentExecution, bool]:
    """Regista a execução e o evento de auditoria numa única transação.

    O parecer mapeado fica persistido como intenção de encaminhamento. O estado
    da pauta não muda nesta operação: a transição exige um comando separado,
    um gate ativo e autorização validada pela máquina de estados.
    """
    if actor.actor_type != ActorType.SYSTEM or actor.role != ActorRole.ORCHESTRATOR:
        raise DomainError("O registo de execução exige SYSTEM/ORCHESTRATOR.")

    payload, request_sha256 = _canonical_payload(envelope)
    existing = _find_execution(db, envelope.execution_id, request_sha256)
    if existing is not None:
        return existing, False

    assignment = db.scalar(
        select(Assignment)
        .where(Assignment.id == envelope.pauta_id)
        .with_for_update()
    )
    if assignment is None:
        raise DomainError("A pauta indicada no envelope não existe.")
    if assignment.id != envelope.pauta_id:
        raise DomainError("O envelope não corresponde à pauta carregada.")

    # Revalidar após o lock para proteger contra repetição concorrente.
    existing = _find_execution(db, envelope.execution_id, request_sha256)
    if existing is not None:
        return existing, False

    mapped_target_status = None
    if envelope.execution_status == ExecutionStatus.SUCCESS:
        mapped_target_status = resolve_agent_envelope(envelope).target_status.value

    execution = AgentExecution(
        assignment_id=assignment.id,
        execution_id=envelope.execution_id,
        agent_id=envelope.agent_id.value,
        agent_version=envelope.agent_version,
        prompt_version=envelope.prompt_version,
        artifact_id=envelope.artifact_id,
        artifact_version=envelope.artifact_version,
        output_artifact_id=envelope.output_artifact_id,
        output_version=envelope.output_version,
        execution_status=envelope.execution_status.value,
        editorial_opinion=envelope.editorial_opinion,
        mapped_target_status=mapped_target_status,
        payload=payload,
        request_sha256=request_sha256,
        correlation_id=envelope.correlation_id,
        created_at=utc_now(),
    )
    event = AuditEvent(
        assignment_id=assignment.id,
        event_type="AGENT_EXECUTION_RECORDED",
        actor_type=actor.actor_type.value,
        actor_id=actor.actor_id,
        previous_status=assignment.status,
        new_status=assignment.status,
        payload={
            "execution_id": str(envelope.execution_id),
            "agent_id": envelope.agent_id.value,
            "execution_status": envelope.execution_status.value,
            "editorial_opinion": envelope.editorial_opinion,
            "mapped_target_status": mapped_target_status,
            "request_sha256": request_sha256,
            "state_transition_applied": False,
        },
        correlation_id=envelope.correlation_id,
    )
    db.add_all([execution, event])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _find_execution(db, envelope.execution_id, request_sha256)
        if existing is not None:
            return existing, False
        raise
    db.refresh(execution)
    return execution, True



def _find_transition_result(
    db: Session, *, scope: str, command_id: str, request_sha256: str
) -> Assignment | None:
    record = db.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == command_id,
        )
    )
    if record is None:
        return None
    if record.request_hash != request_sha256:
        raise AgentExecutionConflict(
            "command_id reutilizado com conteúdo de transição diferente."
        )
    assignment = db.get(Assignment, record.resource_id)
    if assignment is None:
        raise DomainError("Registo idempotente aponta para pauta inexistente.")
    return assignment


def apply_agent_execution_transition(
    db: Session,
    execution_id,
    *,
    actor: Actor,
    expected_row_version: int,
    command_id,
    reason: str | None = None,
) -> tuple[Assignment, bool]:
    """Aplica o estado-alvo de uma execução usando a política ativa.

    A alteração da pauta, o evento de auditoria e a chave idempotente são
    confirmados na mesma transação. Um estado-alvo ainda não autorizado pela
    TRANSITION_POLICY é rejeitado sem alterar a pauta.
    """
    scope = f"agent-execution:transition:{execution_id}"
    request_payload = {
        "execution_id": str(execution_id),
        "actor_type": actor.actor_type.value,
        "actor_id": actor.actor_id,
        "actor_role": actor.role.value,
        "expected_row_version": expected_row_version,
        "reason": reason,
    }
    canonical = json.dumps(
        request_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    request_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    command_key = str(command_id)

    existing = _find_transition_result(
        db, scope=scope, command_id=command_key, request_sha256=request_sha256
    )
    if existing is not None:
        return existing, False

    execution = db.scalar(
        select(AgentExecution).where(AgentExecution.execution_id == execution_id)
    )
    if execution is None:
        raise DomainError("Execução de agente não encontrada.")
    if execution.execution_status != ExecutionStatus.SUCCESS.value:
        raise DomainError("Apenas execuções SUCCESS podem solicitar transição.")
    if execution.mapped_target_status is None:
        raise DomainError("A execução não possui estado-alvo editorial mapeado.")

    assignment = db.scalar(
        select(Assignment)
        .where(Assignment.id == execution.assignment_id)
        .with_for_update()
    )
    if assignment is None:
        raise DomainError("A pauta associada à execução não existe.")

    existing = _find_transition_result(
        db, scope=scope, command_id=command_key, request_sha256=request_sha256
    )
    if existing is not None:
        return existing, False

    if assignment.row_version != expected_row_version:
        raise VersionConflict(
            f"Versão desatualizada: esperada {expected_row_version}, "
            f"atual {assignment.row_version}."
        )

    current = AssignmentStatus(assignment.status)
    target = AssignmentStatus(execution.mapped_target_status)
    validate_transition(current, target, actor, reason)
    validate_agent_gate(db, execution)

    assignment.status = target.value
    assignment.row_version += 1
    assignment.updated_at = utc_now()
    event = AuditEvent(
        assignment_id=assignment.id,
        event_type="AGENT_EXECUTION_STATE_TRANSITIONED",
        actor_type=actor.actor_type.value,
        actor_id=actor.actor_id,
        previous_status=current.value,
        new_status=target.value,
        payload={
            "execution_id": str(execution.execution_id),
            "agent_id": execution.agent_id,
            "editorial_opinion": execution.editorial_opinion,
            "row_version": assignment.row_version,
            "reason": reason,
        },
        correlation_id=execution.correlation_id,
    )
    idempotency = IdempotencyRecord(
        scope=scope,
        idempotency_key=command_key,
        request_hash=request_sha256,
        resource_id=assignment.id,
    )
    db.add_all([event, idempotency])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _find_transition_result(
            db, scope=scope, command_id=command_key, request_sha256=request_sha256
        )
        if existing is not None:
            return existing, False
        raise
    db.refresh(assignment)
    return assignment, True
