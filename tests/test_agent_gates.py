# PONTO-FORA — testes dos gates editoriais baseados em evidências
# Identificador: PF-TEST-EDITORIAL-GATES-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software e Governança Editorial
# Âmbito: Testes dos gates de investigação, fact-checking, redação e bloqueios.
# SHA-256 (conteúdo normalizado): d4ff36853f61cbe78bfe82ed324e0c729e27bbf46d3175d9a681002ef318434a
# Commit de referência (base documental): 3439b36f8468ce420cd46cb1135d98dc9170c6c8

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from ponto_fora_api.db import Base
from ponto_fora_api.models import (
    Assignment,
    Claim,
    ClaimEvidenceLink,
    EvidenceRecord,
    FactCheckAssessment,
    SourceRecord,
)
from ponto_fora_api.schemas.agent_contract import AgentId
from ponto_fora_api.schemas.evidence import FactCheckVerdict
from ponto_fora_api.services.agent_gates import (
    GateNotImplemented,
    GateValidationError,
    validate_agent_gate,
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


def create_assignment(db):
    assignment_id = uuid4()
    assignment = Assignment(
        id=assignment_id,
        reference_code=f"PF-{assignment_id.hex[:12].upper()}",
        title="Pauta de validação dos gates",
        status="RECEBIDA",
        priority="normal",
        row_version=1,
        created_by="test",
    )
    db.add(assignment)
    db.commit()
    return assignment


def create_dossier(db, assignment_id):
    now = datetime.now(UTC)
    source_id, claim_id, evidence_id = uuid4(), uuid4(), uuid4()
    source = SourceRecord(
        id=source_id,
        assignment_id=assignment_id,
        canonical_url="https://example.org/primary",
        title="Documento primário",
        source_type="PRIMARY",
        retrieved_at=now,
        access_status="AVAILABLE",
    )
    claim = Claim(
        id=claim_id,
        assignment_id=assignment_id,
        claim_text="A decisão foi publicada na data indicada.",
        claim_type="FACTUAL",
        materiality="HIGH",
        created_by="investigator:test",
        created_at=now,
    )
    evidence = EvidenceRecord(
        id=evidence_id,
        assignment_id=assignment_id,
        source_id=source_id,
        locator="https://example.org/primary#date",
        observation="O documento identifica a data da decisão.",
        evidence_type="DOCUMENT",
        polarity="SUPPORTS",
        collected_by="investigator:test",
        collected_at=now,
    )
    link = ClaimEvidenceLink(
        id=uuid4(),
        assignment_id=assignment_id,
        claim_id=claim_id,
        evidence_id=evidence_id,
        relationship="SUPPORTS",
        rationale="A passagem documental sustenta a afirmação.",
        assessed_by="investigator:test",
        assessed_at=now,
    )
    db.add_all([source, claim, evidence, link])
    db.commit()
    return claim, evidence


def create_assessment(db, assignment_id, claim_id):
    assessment = FactCheckAssessment(
        id=uuid4(),
        assignment_id=assignment_id,
        claim_id=claim_id,
        verdict=FactCheckVerdict.CONFIRMADA.value,
        reasoning_summary="A evidência primária sustenta a afirmação.",
        reviewer_type="AI",
        reviewer_id="fact-checker:test",
        assessed_at=datetime.now(UTC),
        assessment_version=1,
    )
    db.add(assessment)
    db.commit()
    return assessment


def execution(assignment_id, agent_id, opinion, payload):
    return SimpleNamespace(
        assignment_id=assignment_id,
        agent_id=agent_id.value,
        editorial_opinion=opinion,
        payload=payload,
    )


def test_investigator_gate_rejects_missing_claims_and_evidence(db):
    assignment = create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.INVESTIGADOR,
        "APTO PARA FACT-CHECKING",
        {"claim_ids": [], "evidence_refs": []},
    )

    with pytest.raises(GateValidationError):
        validate_agent_gate(db, item)


def test_investigator_gate_accepts_linked_claims_and_evidence(db):
    assignment = create_assignment(db)
    claim, evidence = create_dossier(db, assignment.id)
    item = execution(
        assignment.id,
        AgentId.INVESTIGADOR,
        "APTO PARA FACT-CHECKING",
        {
            "claim_ids": [str(claim.id)],
            "evidence_refs": [str(evidence.id)],
        },
    )

    validate_agent_gate(db, item)


def test_investigator_gate_rejects_unlinked_evidence(db):
    assignment = create_assignment(db)
    claim, evidence = create_dossier(db, assignment.id)
    db.query(ClaimEvidenceLink).delete()
    db.commit()
    item = execution(
        assignment.id,
        AgentId.INVESTIGADOR,
        "APTO PARA FACT-CHECKING",
        {
            "claim_ids": [str(claim.id)],
            "evidence_refs": [str(evidence.id)],
        },
    )

    with pytest.raises(GateValidationError):
        validate_agent_gate(db, item)


def test_fact_checker_gate_requires_one_matching_assessment_per_claim(db):
    assignment = create_assignment(db)
    claim, evidence = create_dossier(db, assignment.id)
    create_assessment(db, assignment.id, claim.id)
    item = execution(
        assignment.id,
        AgentId.FACT_CHECKER,
        "APROVADO PARA REDAÇÃO",
        {
            "claim_ids": [str(claim.id)],
            "evidence_refs": [str(evidence.id)],
            "claim_verdicts": {str(claim.id): FactCheckVerdict.CONFIRMADA.value},
        },
    )

    validate_agent_gate(db, item)


def test_fact_checker_gate_rejects_divergent_verdict(db):
    assignment = create_assignment(db)
    claim, evidence = create_dossier(db, assignment.id)
    create_assessment(db, assignment.id, claim.id)
    item = execution(
        assignment.id,
        AgentId.FACT_CHECKER,
        "APROVADO PARA REDAÇÃO",
        {
            "claim_ids": [str(claim.id)],
            "evidence_refs": [str(evidence.id)],
            "claim_verdicts": {str(claim.id): FactCheckVerdict.CONTRADITA.value},
        },
    )

    with pytest.raises(GateValidationError):
        validate_agent_gate(db, item)


def test_writer_gate_requires_traceability_and_fact_check(db):
    assignment = create_assignment(db)
    claim, evidence = create_dossier(db, assignment.id)
    create_assessment(db, assignment.id, claim.id)
    item = execution(
        assignment.id,
        AgentId.REDATOR,
        "REDAÇÃO CONCLUÍDA — PRONTA PARA EDIÇÃO",
        {
            "claim_ids": [str(claim.id)],
            "claim_traceability": {str(claim.id): [str(evidence.id)]},
        },
    )

    validate_agent_gate(db, item)


def test_writer_gate_rejects_missing_claim_traceability(db):
    assignment = create_assignment(db)
    claim, _ = create_dossier(db, assignment.id)
    create_assessment(db, assignment.id, claim.id)
    item = execution(
        assignment.id,
        AgentId.REDATOR,
        "REDAÇÃO CONCLUÍDA — PRONTA PARA EDIÇÃO",
        {
            "claim_ids": [str(claim.id)],
            "claim_traceability": {},
        },
    )

    with pytest.raises(GateValidationError):
        validate_agent_gate(db, item)


def test_editor_gate_remains_blocked_until_findings_are_structured(db):
    assignment = create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.EDITOR,
        "APROVADO PARA DECISÃO EDITORIAL",
        {
            "editorial_findings": [],
            "severity": "LOW",
            "editorial_decision": "APROVADO PARA DECISÃO EDITORIAL",
        },
    )

    with pytest.raises(GateNotImplemented):
        validate_agent_gate(db, item)


def test_social_gate_remains_blocked_without_persisted_human_approval(db):
    assignment = create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.SOCIAL_MEDIA,
        "PRONTO PARA REVISÃO EDITORIAL",
        {
            "source_news_id": "news-001",
            "source_news_version": "1.0",
            "piece_id": "piece-001",
            "channel": "instagram",
            "format": "reel",
            "rights_status": "CLEARED",
        },
    )

    with pytest.raises(GateNotImplemented):
        validate_agent_gate(db, item)



def test_editor_gate_accepts_empty_findings_with_consistent_decision(db):
    create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.EDITOR,
        "APROVADO PARA DECISÃO EDITORIAL",
        {
            "editorial_findings": [],
            "severity": "LOW",
            "editorial_decision": "APROVADO PARA DECISÃO EDITORIAL",
            "output_version": "2.0",
        },
    )

    validate_agent_gate(db, item)


def test_editor_gate_accepts_resolved_moderate_finding_for_current_version(db):
    create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.EDITOR,
        "APROVADO PARA DECISÃO EDITORIAL",
        {
            "editorial_findings": [
                {
                    "finding_id": "EDT-001",
                    "severity": "MODERATE",
                    "excerpt": "O texto analisado.",
                    "problem": "Formulação ambígua.",
                    "resolution_status": "RESOLVED",
                    "resolution_note": "Formulação reescrita e conferida.",
                    "resolved_artifact_version": "2.1",
                    "revalidated": True,
                }
            ],
            "severity": "MODERATE",
            "editorial_decision": "APROVADO PARA DECISÃO EDITORIAL",
            "output_version": "2.1",
        },
    )

    validate_agent_gate(db, item)


def test_editor_gate_rejects_unresolved_finding(db):
    create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.EDITOR,
        "APROVADO PARA DECISÃO EDITORIAL",
        {
            "editorial_findings": [
                {
                    "finding_id": "EDT-002",
                    "severity": "LOW",
                    "excerpt": "Trecho.",
                    "problem": "Repetição.",
                    "resolution_status": "OPEN",
                    "resolution_note": "Ainda não corrigido.",
                    "resolved_artifact_version": "2.0",
                    "revalidated": False,
                }
            ],
            "severity": "LOW",
            "editorial_decision": "APROVADO PARA DECISÃO EDITORIAL",
            "output_version": "2.0",
        },
    )

    with pytest.raises(GateValidationError, match="sem resolução confirmada"):
        validate_agent_gate(db, item)


def test_editor_gate_rejects_resolution_for_another_artifact_version(db):
    create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.EDITOR,
        "APROVADO PARA DECISÃO EDITORIAL",
        {
            "editorial_findings": [
                {
                    "finding_id": "EDT-003",
                    "severity": "LOW",
                    "excerpt": "Trecho.",
                    "problem": "Ajuste de estilo.",
                    "resolution_status": "RESOLVED",
                    "resolution_note": "Ajustado.",
                    "resolved_artifact_version": "1.9",
                    "revalidated": True,
                }
            ],
            "severity": "LOW",
            "editorial_decision": "APROVADO PARA DECISÃO EDITORIAL",
            "output_version": "2.0",
        },
    )

    with pytest.raises(GateValidationError, match="versão de saída atual"):
        validate_agent_gate(db, item)


def test_editor_gate_rejects_critical_finding_even_when_claimed_resolved(db):
    create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.EDITOR,
        "APROVADO PARA DECISÃO EDITORIAL",
        {
            "editorial_findings": [
                {
                    "finding_id": "EDT-004",
                    "severity": "CRITICAL",
                    "excerpt": "Acusação não sustentada.",
                    "problem": "Risco jurídico e factual.",
                    "resolution_status": "RESOLVED",
                    "resolution_note": "Texto alterado.",
                    "resolved_artifact_version": "2.0",
                    "revalidated": True,
                }
            ],
            "severity": "CRITICAL",
            "editorial_decision": "APROVADO PARA DECISÃO EDITORIAL",
            "output_version": "2.0",
        },
    )

    with pytest.raises(GateValidationError, match="exige encaminhamento"):
        validate_agent_gate(db, item)


def test_editor_gate_rejects_aggregate_severity_mismatch(db):
    create_assignment(db)
    item = execution(
        assignment.id,
        AgentId.EDITOR,
        "APROVADO PARA DECISÃO EDITORIAL",
        {
            "editorial_findings": [
                {
                    "finding_id": "EDT-005",
                    "severity": "MODERATE",
                    "excerpt": "Trecho.",
                    "problem": "Ambiguidade.",
                    "resolution_status": "RESOLVED",
                    "resolution_note": "Reescrito.",
                    "resolved_artifact_version": "2.0",
                    "revalidated": True,
                }
            ],
            "severity": "LOW",
            "editorial_decision": "APROVADO PARA DECISÃO EDITORIAL",
            "output_version": "2.0",
        },
    )

    with pytest.raises(GateValidationError, match="maior severidade"):
        validate_agent_gate(db, item)
