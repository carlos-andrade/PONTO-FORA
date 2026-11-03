# PONTO-FORA — validação de gates editoriais baseada em evidências persistidas
# Identificador: PF-COD-SVC-EDITORIAL-GATES-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software e Governança Editorial
# Âmbito: Validar evidências e rastreabilidade antes de aplicar transições de aprovação.
# SHA-256 (conteúdo normalizado): 545d88181a971e3f65413366a2fad2d2c969a8f709e67f2a95e15891898e2801
# Commit de referência (base documental): 3439b36f8468ce420cd46cb1135d98dc9170c6c8

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ponto_fora_api.domain import DomainError
from ponto_fora_api.models import (
    Claim,
    ClaimEvidenceLink,
    EvidenceRecord,
    FactCheckAssessment,
)
from ponto_fora_api.schemas.agent_contract import AgentId
from ponto_fora_api.schemas.evidence import FactCheckVerdict


class GateValidationError(DomainError):
    """Um critério documental ou factual obrigatório não foi satisfeito."""


class GateNotImplemented(GateValidationError):
    """O gate ainda não tem estrutura de dados suficiente para ser validado."""


def _uuid_set(values: list[str], field: str) -> set[UUID]:
    if not values:
        raise GateValidationError(f"{field} não pode estar vazio para este gate.")
    try:
        return {UUID(str(value)) for value in values}
    except (TypeError, ValueError) as exc:
        raise GateValidationError(f"{field} contém identificador UUID inválido.") from exc


def _validate_claims_and_evidence(
    db: Session,
    *,
    assignment_id: UUID,
    claim_ids: set[UUID],
    evidence_ids: set[UUID],
) -> None:
    claims = set(
        db.scalars(
            select(Claim.id).where(
                Claim.assignment_id == assignment_id,
                Claim.id.in_(claim_ids),
            )
        ).all()
    )
    if claims != claim_ids:
        raise GateValidationError(
            "Uma ou mais afirmações não existem ou pertencem a outra pauta."
        )

    evidence = set(
        db.scalars(
            select(EvidenceRecord.id).where(
                EvidenceRecord.assignment_id == assignment_id,
                EvidenceRecord.id.in_(evidence_ids),
            )
        ).all()
    )
    if evidence != evidence_ids:
        raise GateValidationError(
            "Uma ou mais evidências não existem ou pertencem a outra pauta."
        )

    links = db.scalars(
        select(ClaimEvidenceLink).where(
            ClaimEvidenceLink.assignment_id == assignment_id,
            ClaimEvidenceLink.claim_id.in_(claim_ids),
            ClaimEvidenceLink.evidence_id.in_(evidence_ids),
        )
    ).all()
    linked_claims = {link.claim_id for link in links}
    linked_evidence = {link.evidence_id for link in links}
    if linked_claims != claim_ids:
        raise GateValidationError(
            "Cada afirmação submetida precisa de pelo menos uma ligação a evidência."
        )
    if linked_evidence != evidence_ids:
        raise GateValidationError(
            "Cada evidência declarada precisa de estar ligada a uma afirmação."
        )


def _latest_assessment(db: Session, assignment_id: UUID, claim_id: UUID):
    return db.scalar(
        select(FactCheckAssessment)
        .where(
            FactCheckAssessment.assignment_id == assignment_id,
            FactCheckAssessment.claim_id == claim_id,
        )
        .order_by(desc(FactCheckAssessment.assessment_version))
        .limit(1)
    )


def validate_agent_gate(db: Session, execution) -> None:
    """Valida apenas gates cuja estrutura persistida já permite prova objetiva.

    G4 e G6 permanecem bloqueados até existirem contratos estruturados para
    findings resolvidos e decisões/autorização humana vinculadas a versões.
    """
    opinion = execution.editorial_opinion
    agent_id = AgentId(execution.agent_id)
    payload = execution.payload

    if agent_id == AgentId.INVESTIGADOR and opinion in {
        "APTO PARA FACT-CHECKING",
        "APTO COM RESSALVAS",
    }:
        claim_ids = _uuid_set(payload.get("claim_ids", []), "claim_ids")
        evidence_ids = _uuid_set(payload.get("evidence_refs", []), "evidence_refs")
        _validate_claims_and_evidence(
            db,
            assignment_id=execution.assignment_id,
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
        )
        return

    if agent_id == AgentId.FACT_CHECKER and opinion in {
        "APROVADO PARA REDAÇÃO",
        "APROVADO COM RESSALVAS",
    }:
        claim_ids = _uuid_set(payload.get("claim_ids", []), "claim_ids")
        evidence_ids = _uuid_set(payload.get("evidence_refs", []), "evidence_refs")
        _validate_claims_and_evidence(
            db,
            assignment_id=execution.assignment_id,
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
        )
        verdicts = payload.get("claim_verdicts")
        expected_keys = {str(claim_id) for claim_id in claim_ids}
        if not isinstance(verdicts, dict) or set(verdicts) != expected_keys:
            raise GateValidationError(
                "O Fact-checker tem de emitir exatamente um veredicto por afirmação."
            )
        for claim_id in claim_ids:
            assessment = _latest_assessment(db, execution.assignment_id, claim_id)
            if assessment is None:
                raise GateValidationError(
                    f"A afirmação {claim_id} não possui avaliação factual persistida."
                )
            try:
                expected_verdict = FactCheckVerdict(verdicts[str(claim_id)]).value
            except ValueError as exc:
                raise GateValidationError(
                    f"Veredicto inválido para a afirmação {claim_id}."
                ) from exc
            if assessment.verdict != expected_verdict:
                raise GateValidationError(
                    f"O veredicto persistido diverge do envelope para {claim_id}."
                )
        return

    if agent_id == AgentId.REDATOR and opinion == (
        "REDAÇÃO CONCLUÍDA — PRONTA PARA EDIÇÃO"
    ):
        claim_ids = _uuid_set(payload.get("claim_ids", []), "claim_ids")
        traceability = payload.get("claim_traceability")
        expected_keys = {str(claim_id) for claim_id in claim_ids}
        if not isinstance(traceability, dict) or set(traceability) != expected_keys:
            raise GateValidationError(
                "A rastreabilidade do Redator tem de cobrir todas as afirmações declaradas."
            )
        for claim_id in claim_ids:
            refs = traceability[str(claim_id)]
            if not isinstance(refs, list) or not refs or not all(
                isinstance(ref, str) and ref.strip() for ref in refs
            ):
                raise GateValidationError(
                    f"A afirmação {claim_id} não possui referências de rastreabilidade."
                )
            if _latest_assessment(db, execution.assignment_id, claim_id) is None:
                raise GateValidationError(
                    f"A afirmação {claim_id} não possui verificação factual persistida."
                )
        claims = set(
            db.scalars(
                select(Claim.id).where(
                    Claim.assignment_id == execution.assignment_id,
                    Claim.id.in_(claim_ids),
                )
            ).all()
        )
        if claims != claim_ids:
            raise GateValidationError(
                "O texto referencia afirmações inexistentes ou de outra pauta."
            )
        return

    if agent_id == AgentId.EDITOR and opinion == "APROVADO PARA DECISÃO EDITORIAL":
        findings = payload.get("editorial_findings")
        aggregate_severity = payload.get("severity")
        decision = payload.get("editorial_decision")
        output_version = execution.payload.get("output_version")

        if not isinstance(findings, list):
            raise GateValidationError(
                "G4 exige editorial_findings como lista estruturada."
            )
        if decision != opinion:
            raise GateValidationError(
                "A decisão editorial do payload diverge do parecer do envelope."
            )
        severity_rank = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
        if not isinstance(aggregate_severity, str) or aggregate_severity not in severity_rank:
            raise GateValidationError("severity deve ser LOW, MODERATE, HIGH ou CRITICAL.")

        seen_ids: set[str] = set()
        observed_severity = "LOW"
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                raise GateValidationError(
                    f"Finding na posição {index} deve ser um objeto."
                )
            required = {
                "finding_id",
                "severity",
                "excerpt",
                "problem",
                "resolution_status",
                "resolution_note",
                "resolved_artifact_version",
                "revalidated",
            }
            missing = required - finding.keys()
            if missing:
                raise GateValidationError(
                    f"Finding {index} sem campos obrigatórios: {', '.join(sorted(missing))}."
                )
            finding_id = finding["finding_id"]
            if not isinstance(finding_id, str) or not finding_id.strip():
                raise GateValidationError("finding_id deve ser uma string não vazia.")
            if finding_id in seen_ids:
                raise GateValidationError(f"finding_id duplicado: {finding_id}.")
            seen_ids.add(finding_id)

            finding_severity = finding["severity"]
            if not isinstance(finding_severity, str) or finding_severity not in severity_rank:
                raise GateValidationError(
                    f"Severidade inválida no finding {finding_id}."
                )
            if severity_rank[finding_severity] > severity_rank[observed_severity]:
                observed_severity = finding_severity
            for field in ("excerpt", "problem", "resolution_note"):
                if not isinstance(finding[field], str) or not finding[field].strip():
                    raise GateValidationError(
                        f"{field} deve estar preenchido no finding {finding_id}."
                    )
            if finding["resolution_status"] != "RESOLVED":
                raise GateValidationError(
                    f"Finding {finding_id} permanece sem resolução confirmada."
                )
            if finding["resolved_artifact_version"] != output_version:
                raise GateValidationError(
                    f"Finding {finding_id} não aponta para a versão de saída atual."
                )
            if finding["revalidated"] is not True:
                raise GateValidationError(
                    f"Finding {finding_id} não foi revalidado pelo Editor."
                )
            if finding_severity in {"CRITICAL", "HIGH"}:
                raise GateValidationError(
                    f"Finding {finding_id} de severidade {finding_severity} "
                    "exige encaminhamento e evidência de resolução fora do gate G4; "
                    "não pode ser encerrado apenas por declaração do Editor."
                )

        if aggregate_severity != observed_severity:
            raise GateValidationError(
                "severity agregado não corresponde à maior severidade dos findings."
            )
        return

    if agent_id == AgentId.SOCIAL_MEDIA and opinion == "PRONTO PARA REVISÃO EDITORIAL":
        raise GateNotImplemented(
            "G6 permanece bloqueado: é necessária uma decisão humana persistida "
            "sobre a notícia-base e a versão exata antes da produção social."
        )
