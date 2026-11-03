# PONTO-FORA — testes do domínio factual
# Identificador: PF-TEST-EVIDENCE-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Validar proveniência, isolamento entre pautas e versionamento de pareceres.
# SHA-256 (conteúdo normalizado): PENDENTE
# Commit de referência (base documental): c5d4cf29b6d2ab23b99439852235868c3b422195

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from ponto_fora_api.domain import Actor, ActorRole, ActorType, DomainError
from ponto_fora_api.models import (
    Assignment, AuditEvent, Claim, EvidenceRecord, SourceRecord,
)
from ponto_fora_api.schemas.evidence import (
    ClaimCreate, ClaimEvidenceCreate, EvidenceCreate, FactCheckAssessmentCreate,
    FactCheckVerdict, ReviewerType, SourceCreate, SourceType, AccessStatus,
)
from ponto_fora_api.services.assignments import create_assignment
from ponto_fora_api.services.evidence import (
    create_claim, create_evidence, create_fact_check_assessment, create_source,
    link_claim_evidence,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from ponto_fora_api.db import Base
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def two_assignments(db):
    actor = Actor(ActorType.SYSTEM, "test-runner", ActorRole.ORCHESTRATOR)
    a, _ = create_assignment(db, title="Pauta A", actor=actor, idempotency_key="pauta-a")
    b, _ = create_assignment(db, title="Pauta B", actor=actor, idempotency_key="pauta-b")
    return a, b


def source_payload():
    return SourceCreate(
        canonical_url="https://example.org/noticia",
        title="Fonte de teste",
        source_type=SourceType.SECONDARY,
        retrieved_at=datetime.now(UTC),
        access_status=AccessStatus.AVAILABLE,
    )


def test_source_claim_evidence_and_link_are_persisted(db, two_assignments):
    assignment, _ = two_assignments
    source = create_source(db, assignment.id, source_payload(), actor_id="investigator:test")
    claim = create_claim(db, assignment.id, ClaimCreate(
        claim_text="A entidade publicou um relatório.",
        created_by="investigator:test",
    ))
    evidence = create_evidence(db, assignment.id, EvidenceCreate(
        source_id=source.id,
        locator="parágrafo 3",
        observation="A fonte informa a publicação do relatório.",
        collected_by="investigator:test",
        collected_at=datetime.now(UTC),
    ))
    link = link_claim_evidence(db, assignment.id, ClaimEvidenceCreate(
        claim_id=claim.id,
        evidence_id=evidence.id,
        relationship="SUPPORTS",
        rationale="O trecho identifica a publicação.",
        assessed_by="fact-checker:test",
        assessed_at=datetime.now(UTC),
    ))
    assert db.scalar(select(func.count()).select_from(SourceRecord)) == 1
    assert db.scalar(select(func.count()).select_from(Claim)) == 1
    assert db.scalar(select(func.count()).select_from(EvidenceRecord)) == 1
    assert link.assignment_id == assignment.id
    assert db.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.assignment_id == assignment.id)) == 5


def test_evidence_cannot_use_source_from_another_assignment(db, two_assignments):
    assignment_a, assignment_b = two_assignments
    source = create_source(db, assignment_a.id, source_payload(), actor_id="investigator:test")
    with pytest.raises(DomainError):
        create_evidence(db, assignment_b.id, EvidenceCreate(
            source_id=source.id,
            locator="página 1",
            observation="Conteúdo observado.",
            collected_by="investigator:test",
            collected_at=datetime.now(UTC),
        ))


def test_claim_evidence_link_cannot_cross_assignments(db, two_assignments):
    assignment_a, assignment_b = two_assignments
    source = create_source(db, assignment_a.id, source_payload(), actor_id="investigator:test")
    claim = create_claim(db, assignment_b.id, ClaimCreate(
        claim_text="Afirmação de outra pauta.",
        created_by="investigator:test",
    ))
    evidence = create_evidence(db, assignment_a.id, EvidenceCreate(
        source_id=source.id,
        locator="secção 1",
        observation="Observação.",
        collected_by="investigator:test",
        collected_at=datetime.now(UTC),
    ))
    with pytest.raises(DomainError):
        link_claim_evidence(db, assignment_a.id, ClaimEvidenceCreate(
            claim_id=claim.id,
            evidence_id=evidence.id,
            relationship="SUPPORTS",
            rationale="Não deve ser associado.",
            assessed_by="fact-checker:test",
            assessed_at=datetime.now(UTC),
        ))


def test_unproven_and_contradicted_are_distinct_verdicts(db, two_assignments):
    assignment, _ = two_assignments
    claim = create_claim(db, assignment.id, ClaimCreate(
        claim_text="Afirmação sem confirmação.",
        created_by="investigator:test",
    ))
    unproven = create_fact_check_assessment(db, assignment.id, FactCheckAssessmentCreate(
        claim_id=claim.id,
        verdict=FactCheckVerdict.NAO_COMPROVADA,
        reasoning_summary="Não foi encontrada evidência suficiente.",
        reviewer_type=ReviewerType.AI,
        reviewer_id="fact-checker:test",
        assessed_at=datetime.now(UTC),
    ))
    contradicted = create_fact_check_assessment(db, assignment.id, FactCheckAssessmentCreate(
        claim_id=claim.id,
        verdict=FactCheckVerdict.CONTRADITA,
        reasoning_summary="Uma fonte primária contradiz diretamente a afirmação.",
        reviewer_type=ReviewerType.HUMAN,
        reviewer_id="editor:test",
        assessed_at=datetime.now(UTC),
        assessment_version=2,
        supersedes_assessment_id=unproven.id,
    ))
    assert unproven.verdict != contradicted.verdict
    assert db.scalar(select(func.count()).select_from(FactCheckAssessment)) == 2


def test_source_url_rejects_non_http_and_credentials():
    with pytest.raises(ValueError):
        SourceCreate(canonical_url="file:///etc/passwd", title="Invalid", retrieved_at=datetime.now(UTC))
    with pytest.raises(ValueError):
        SourceCreate(canonical_url="https://user:pass@example.org/x", title="Invalid", retrieved_at=datetime.now(UTC))
