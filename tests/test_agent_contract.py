# PONTO-FORA — testes dos contratos e do encaminhamento dos agentes
# Identificador: PF-TEST-AGENT-CONTRACT-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software e Governança Editorial
# Âmbito: Validação do envelope comum e do mapeamento de pareceres para estados.
# SHA-256 (conteúdo normalizado): e621835259401399e2d034e80d5870c30cac4d7d1237ad32f81533ff956c1565
# Commit de referência (base documental): cb1a16e6be6e890e64f3d0ca67f9ad22dcc974df

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ponto_fora_api.domain import AssignmentStatus
from ponto_fora_api.schemas.agent_contract import (
    AgentEnvelope,
    AgentId,
    ExecutionStatus,
)
from ponto_fora_api.services.orchestration import (
    AgentExecutionNotSuccessful,
    UnsupportedEditorialOpinion,
    map_editorial_opinion,
    resolve_agent_envelope,
)


def envelope(**overrides) -> dict:
    payload = {
        "pauta_id": str(uuid4()),
        "artifact_id": "artifact-001",
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
    return payload


def test_common_agent_envelope_is_valid() -> None:
    result = AgentEnvelope.model_validate(envelope())
    assert result.agent_id == AgentId.INVESTIGADOR
    assert result.execution_status == ExecutionStatus.SUCCESS


def test_execution_status_and_editorial_opinion_are_independent() -> None:
    result = AgentEnvelope.model_validate(
        envelope(
            execution_status=ExecutionStatus.FAILED.value,
            editorial_opinion="APTO COM RESSALVAS",
            caveats=["A fonte primária ainda não foi localizada."],
        )
    )
    assert result.execution_status == ExecutionStatus.FAILED
    assert result.editorial_opinion == "APTO COM RESSALVAS"


def test_naive_created_at_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentEnvelope.model_validate(
            envelope(created_at=datetime(2026, 11, 3, 10, 0).isoformat())
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentEnvelope.model_validate(envelope(unexpected_field="not allowed"))


@pytest.mark.parametrize(
    ("agent", "opinion", "expected"),
    [
        (
            AgentId.INVESTIGADOR,
            "APTO PARA FACT-CHECKING",
            AssignmentStatus.AGUARDANDO_FACT_CHECK,
        ),
        (
            AgentId.INVESTIGADOR,
            "APTO COM RESSALVAS",
            AssignmentStatus.AGUARDANDO_FACT_CHECK,
        ),
        (
            AgentId.INVESTIGADOR,
            "INVESTIGAÇÃO INSUFICIENTE",
            AssignmentStatus.INVESTIGACAO_PENDENTE,
        ),
        (
            AgentId.FACT_CHECKER,
            "APROVADO PARA REDAÇÃO",
            AssignmentStatus.AGUARDANDO_REDACAO,
        ),
        (
            AgentId.FACT_CHECKER,
            "APROVADO COM RESSALVAS",
            AssignmentStatus.AGUARDANDO_REDACAO,
        ),
        (
            AgentId.REDATOR,
            "REDAÇÃO CONCLUÍDA — PRONTA PARA EDIÇÃO",
            AssignmentStatus.AGUARDANDO_EDICAO,
        ),
        (
            AgentId.EDITOR,
            "APROVADO PARA DECISÃO EDITORIAL",
            AssignmentStatus.AGUARDANDO_DECISAO_EDITORIAL,
        ),
        (
            AgentId.EDITOR,
            "APROVADO COM AJUSTES MENORES",
            AssignmentStatus.EM_EDICAO,
        ),
        (
            AgentId.SOCIAL_MEDIA,
            "PRONTO PARA REVISÃO EDITORIAL",
            AssignmentStatus.AGUARDANDO_REVISAO_SOCIAL,
        ),
        (
            AgentId.SOCIAL_MEDIA,
            "DEVOLVIDO AO EDITOR",
            AssignmentStatus.AGUARDANDO_REVISAO_SOCIAL,
        ),
        (
            AgentId.SOCIAL_MEDIA,
            "DEVOLVIDO AO SOCIAL MEDIA",
            AssignmentStatus.DEVOLVIDA_A_SOCIAL_MEDIA,
        ),
    ],
)
def test_opinion_maps_to_expected_status(agent, opinion, expected) -> None:
    result = map_editorial_opinion(agent, opinion)
    assert result.target_status == expected


def test_minor_editorial_adjustments_require_follow_up() -> None:
    result = map_editorial_opinion(
        AgentId.EDITOR, "APROVADO COM AJUSTES MENORES"
    )
    assert result.requires_follow_up is True
    assert result.follow_up_owner == "EDITOR"


def test_social_media_return_to_editor_requires_follow_up() -> None:
    result = map_editorial_opinion(
        AgentId.SOCIAL_MEDIA, "DEVOLVIDO AO EDITOR"
    )
    assert result.requires_follow_up is True
    assert result.follow_up_owner == "EDITOR"


def test_unknown_opinion_is_rejected_without_fuzzy_matching() -> None:
    with pytest.raises(UnsupportedEditorialOpinion):
        map_editorial_opinion(AgentId.INVESTIGADOR, "APTO PARA FACT CHECK")


def test_fact_checker_requires_claim_verdicts_and_decision() -> None:
    with pytest.raises(ValidationError):
        AgentEnvelope.model_validate(
            envelope(
                agent_id=AgentId.FACT_CHECKER.value,
                editorial_opinion="APROVADO PARA REDAÇÃO",
            )
        )


def test_social_media_requires_immutable_source_reference() -> None:
    with pytest.raises(ValidationError):
        AgentEnvelope.model_validate(
            envelope(
                agent_id=AgentId.SOCIAL_MEDIA.value,
                editorial_opinion="PRONTO PARA REVISÃO EDITORIAL",
            )
        )


def test_social_media_envelope_accepts_complete_source_reference() -> None:
    result = AgentEnvelope.model_validate(
        envelope(
            agent_id=AgentId.SOCIAL_MEDIA.value,
            editorial_opinion="PRONTO PARA REVISÃO EDITORIAL",
            source_news_id="news-001",
            source_news_version="2.1",
            piece_id="piece-001",
            channel="instagram",
            format="reel",
            rights_status="CLEARED",
        )
    )
    assert result.source_news_id == "news-001"
    assert result.source_news_version == "2.1"


def test_caveats_are_required_when_opinion_contains_reservations() -> None:
    with pytest.raises(ValidationError):
        AgentEnvelope.model_validate(
            envelope(editorial_opinion="APTO COM RESSALVAS")
        )


def test_input_artifact_versions_must_cover_all_inputs() -> None:
    with pytest.raises(ValidationError):
        AgentEnvelope.model_validate(
            envelope(input_artifact_ids=["dossier-001", "source-002"])
        )


def test_failed_execution_cannot_advance_editorial_state() -> None:
    result = AgentEnvelope.model_validate(
        envelope(execution_status=ExecutionStatus.FAILED.value)
    )
    with pytest.raises(AgentExecutionNotSuccessful):
        resolve_agent_envelope(result)


def test_retryable_execution_cannot_advance_editorial_state() -> None:
    result = AgentEnvelope.model_validate(
        envelope(execution_status=ExecutionStatus.RETRYABLE.value)
    )
    with pytest.raises(AgentExecutionNotSuccessful):
        resolve_agent_envelope(result)


def test_successful_execution_resolves_opinion() -> None:
    result = AgentEnvelope.model_validate(envelope())
    mapped = resolve_agent_envelope(result)
    assert mapped.target_status == AssignmentStatus.AGUARDANDO_FACT_CHECK
