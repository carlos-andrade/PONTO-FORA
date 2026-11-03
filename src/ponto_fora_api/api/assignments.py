# PONTO-FORA — endpoints de consulta de pautas
# Identificador: PF-COD-API-ASSIGN-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Consultas paginadas de pautas e eventos de auditoria.
# SHA-256 (conteúdo normalizado): 243a9ba3614bf58afae502031719353eeb7d22327fff3bf146fb5553abb40344
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ponto_fora_api.db import get_db
from ponto_fora_api.models import Assignment, AuditEvent

router = APIRouter(prefix="/api/v1/assignments", tags=["Pautas"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("")
def list_assignments(
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
) -> dict:
    statement = (
        select(Assignment)
        .order_by(Assignment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        statement = statement.where(Assignment.status == status)
    rows = db.scalars(statement).all()
    return {"items": [_assignment_view(row) for row in rows], "limit": limit, "offset": offset}


@router.get("/{assignment_id}")
def get_assignment(assignment_id: UUID, db: DbSession) -> dict:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Pauta não encontrada.")
    return _assignment_view(assignment)


@router.get("/{assignment_id}/audit")
def get_assignment_audit(assignment_id: UUID, db: DbSession) -> dict:
    if db.get(Assignment, assignment_id) is None:
        raise HTTPException(status_code=404, detail="Pauta não encontrada.")
    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.assignment_id == assignment_id)
        .order_by(AuditEvent.occurred_at.asc(), AuditEvent.id.asc())
    ).all()
    return {
        "items": [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "actor_type": event.actor_type,
                "actor_id": event.actor_id,
                "previous_status": event.previous_status,
                "new_status": event.new_status,
                "payload": event.payload,
                "correlation_id": str(event.correlation_id),
                "occurred_at": event.occurred_at.isoformat(),
            }
            for event in events
        ]
    }


def _assignment_view(assignment: Assignment) -> dict:
    return {
        "id": str(assignment.id),
        "reference_code": assignment.reference_code,
        "title": assignment.title,
        "summary": assignment.summary,
        "origin_url": assignment.origin_url,
        "topic": assignment.topic,
        "target_audience": assignment.target_audience,
        "status": assignment.status,
        "priority": assignment.priority,
        "row_version": assignment.row_version,
        "created_at": assignment.created_at.isoformat(),
        "updated_at": assignment.updated_at.isoformat(),
    }
