# PONTO-FORA — serviços do domínio factual
# Identificador: PF-COD-SVC-EVIDENCE-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Serviços transacionais de fontes, afirmações, evidências e avaliações.
# SHA-256 (conteúdo normalizado): b5daf8a118fdeb203b7aa19573ab276c9c23e0b11c10db5ccea54309e82e5819
# Commit de referência (base documental): c5d4cf29b6d2ab23b99439852235868c3b422195

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ponto_fora_api.domain import DomainError
from ponto_fora_api.models import Assignment, AuditEvent, Claim, ClaimEvidenceLink, EvidenceRecord, FactCheckAssessment, SourceRecord
from ponto_fora_api.schemas.evidence import ClaimCreate, ClaimEvidenceCreate, EvidenceCreate, FactCheckAssessmentCreate, SourceCreate


def _assignment(db: Session, assignment_id: UUID) -> Assignment:
    item = db.get(Assignment, assignment_id)
    if item is None:
        raise DomainError("Pauta não encontrada.")
    return item


def _audit(db: Session, assignment_id: UUID, event_type: str, actor_id: str, payload: dict) -> None:
    from uuid import uuid4
    db.add(AuditEvent(assignment_id=assignment_id, event_type=event_type, actor_type="SYSTEM", actor_id=actor_id, payload=payload, correlation_id=uuid4()))


def create_source(db: Session, assignment_id: UUID, data: SourceCreate, actor_id: str) -> SourceRecord:
    _assignment(db, assignment_id)
    item = SourceRecord(assignment_id=assignment_id, **data.model_dump(exclude={"metadata"}) | {"metadata_json": data.metadata})
    db.add(item)
    _audit(db, assignment_id, "SOURCE_RECORDED", actor_id, {"source_id": str(item.id)})
    db.commit()
    db.refresh(item)
    return item


def create_claim(db: Session, assignment_id: UUID, data: ClaimCreate) -> Claim:
    _assignment(db, assignment_id)
    item = Claim(assignment_id=assignment_id, **data.model_dump())
    db.add(item)
    _audit(db, assignment_id, "CLAIM_RECORDED", data.created_by, {"claim_id": str(item.id)})
    db.commit()
    db.refresh(item)
    return item


def create_evidence(db: Session, assignment_id: UUID, data: EvidenceCreate) -> EvidenceRecord:
    _assignment(db, assignment_id)
    source = db.scalar(select(SourceRecord).where(SourceRecord.id == data.source_id, SourceRecord.assignment_id == assignment_id))
    if source is None:
        raise DomainError("A fonte não existe ou pertence a outra pauta.")
    item = EvidenceRecord(assignment_id=assignment_id, **data.model_dump())
    db.add(item)
    _audit(db, assignment_id, "EVIDENCE_RECORDED", data.collected_by, {"evidence_id": str(item.id)})
    db.commit()
    db.refresh(item)
    return item


def link_claim_evidence(db: Session, assignment_id: UUID, data: ClaimEvidenceCreate) -> ClaimEvidenceLink:
    _assignment(db, assignment_id)
    claim = db.scalar(select(Claim).where(Claim.id == data.claim_id, Claim.assignment_id == assignment_id))
    evidence = db.scalar(select(EvidenceRecord).where(EvidenceRecord.id == data.evidence_id, EvidenceRecord.assignment_id == assignment_id))
    if claim is None or evidence is None:
        raise DomainError("Afirmação e evidência têm de existir na mesma pauta.")
    item = ClaimEvidenceLink(assignment_id=assignment_id, **data.model_dump())
    db.add(item)
    _audit(db, assignment_id, "CLAIM_EVIDENCE_LINKED", data.assessed_by, {"claim_id": str(claim.id), "evidence_id": str(evidence.id)})
    db.commit()
    db.refresh(item)
    return item


def create_fact_check_assessment(db: Session, assignment_id: UUID, data: FactCheckAssessmentCreate) -> FactCheckAssessment:
    _assignment(db, assignment_id)
    claim = db.scalar(select(Claim).where(Claim.id == data.claim_id, Claim.assignment_id == assignment_id))
    if claim is None:
        raise DomainError("A afirmação não existe ou pertence a outra pauta.")
    if data.supersedes_assessment_id is None and data.assessment_version != 1:
        raise DomainError("A primeira avaliação deve ter versão 1.")
    if data.supersedes_assessment_id is not None:
        previous = db.scalar(select(FactCheckAssessment).where(FactCheckAssessment.id == data.supersedes_assessment_id, FactCheckAssessment.assignment_id == assignment_id, FactCheckAssessment.claim_id == data.claim_id))
        if previous is None or data.assessment_version != previous.assessment_version + 1:
            raise DomainError("O parecer substituído deve pertencer à mesma afirmação e a versão deve ser consecutiva.")
    item = FactCheckAssessment(assignment_id=assignment_id, **data.model_dump())
    db.add(item)
    _audit(db, assignment_id, "FACT_CHECK_ASSESSED", data.reviewer_id, {"assessment_id": str(item.id), "claim_id": str(claim.id), "verdict": data.verdict.value})
    db.commit()
    db.refresh(item)
    return item
