# PONTO-FORA — persistência transacional de execuções dos agentes
# Identificador: PF-COD-SVC-AGENT-EXECUTION-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software e Governança Editorial
# Âmbito: Persistência idempotente e auditável dos envelopes dos agentes sem avanço implícito de estado.
# SHA-256 (conteúdo normalizado): 39fb90c409fe934fa44793f5c22b00cce0588c42e7c71f58b8e862f854185829
# Commit de referência (base documental): 025804dfc3f79256d48e3c04aab9a15495893c5a

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ponto_fora_api.domain import (
    Actor,
    ActorRole,
    ActorType,
    DomainError,
)
from ponto_fora_api.models import AgentExecution, Assignment, AuditEvent, utc_now
from ponto_fora_api.schemas.agent_contract import AgentEnvelope, ExecutionStatus
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
