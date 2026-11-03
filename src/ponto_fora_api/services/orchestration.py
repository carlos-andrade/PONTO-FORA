# PONTO-FORA — tradução controlada de pareceres editoriais
# Identificador: PF-COD-SVC-ORCHESTRATION-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software e Governança Editorial
# Âmbito: Mapeamento explícito de pareceres dos agentes para estados editoriais.
# SHA-256 (conteúdo normalizado): b082434ada44c8deb05ba11771eb196d0651a2bd02c386487028c273b8cd9715
# Commit de referência (base documental): cb1a16e6be6e890e64f3d0ca67f9ad22dcc974df

from dataclasses import dataclass

from ponto_fora_api.domain import AssignmentStatus
from ponto_fora_api.schemas.agent_contract import AgentId


class UnsupportedEditorialOpinion(ValueError):
    """Parecer não previsto no contrato; a transição deve ser suspensa."""


@dataclass(frozen=True)
class OpinionMapping:
    target_status: AssignmentStatus
    requires_follow_up: bool = False
    follow_up_owner: str | None = None


_OPINION_MAP: dict[tuple[AgentId, str], OpinionMapping] = {
    (AgentId.INVESTIGADOR, "APTO PARA FACT-CHECKING"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_FACT_CHECK
    ),
    (AgentId.INVESTIGADOR, "APTO COM RESSALVAS"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_FACT_CHECK, True, "FACT_CHECKER"
    ),
    (AgentId.INVESTIGADOR, "INVESTIGAÇÃO INSUFICIENTE"): OpinionMapping(
        AssignmentStatus.INVESTIGACAO_PENDENTE, True, "INVESTIGADOR"
    ),
    (AgentId.INVESTIGADOR, "BLOQUEADO"): OpinionMapping(
        AssignmentStatus.BLOQUEADA, True, "DIRECAO_EDITORIAL"
    ),
    (AgentId.FACT_CHECKER, "APROVADO PARA REDAÇÃO"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_REDACAO
    ),
    (AgentId.FACT_CHECKER, "APROVADO COM RESSALVAS"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_REDACAO, True, "REDATOR"
    ),
    (AgentId.FACT_CHECKER, "DEVOLVIDO À INVESTIGAÇÃO"): OpinionMapping(
        AssignmentStatus.INVESTIGACAO_PENDENTE, True, "INVESTIGADOR"
    ),
    (AgentId.FACT_CHECKER, "BLOQUEADO"): OpinionMapping(
        AssignmentStatus.BLOQUEADA, True, "DIRECAO_EDITORIAL"
    ),
    (AgentId.REDATOR, "REDAÇÃO CONCLUÍDA — PRONTA PARA EDIÇÃO"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_EDICAO
    ),
    (AgentId.REDATOR, "DEVOLVIDO AO FACT-CHECKER"): OpinionMapping(
        AssignmentStatus.DEVOLVIDA_A_FACT_CHECK, True, "FACT_CHECKER"
    ),
    (AgentId.REDATOR, "DEVOLVIDO À INVESTIGAÇÃO"): OpinionMapping(
        AssignmentStatus.INVESTIGACAO_PENDENTE, True, "INVESTIGADOR"
    ),
    (AgentId.REDATOR, "BLOQUEADO"): OpinionMapping(
        AssignmentStatus.BLOQUEADA, True, "DIRECAO_EDITORIAL"
    ),
    (AgentId.EDITOR, "APROVADO PARA DECISÃO EDITORIAL"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_DECISAO_EDITORIAL
    ),
    (AgentId.EDITOR, "APROVADO COM AJUSTES MENORES"): OpinionMapping(
        AssignmentStatus.EM_EDICAO, True, "EDITOR"
    ),
    (AgentId.EDITOR, "DEVOLVIDO AO REDATOR"): OpinionMapping(
        AssignmentStatus.DEVOLVIDA_A_REDACAO, True, "REDATOR"
    ),
    (AgentId.EDITOR, "DEVOLVIDO AO FACT-CHECKER"): OpinionMapping(
        AssignmentStatus.DEVOLVIDA_A_FACT_CHECK, True, "FACT_CHECKER"
    ),
    (AgentId.EDITOR, "DEVOLVIDO À INVESTIGAÇÃO"): OpinionMapping(
        AssignmentStatus.INVESTIGACAO_PENDENTE, True, "INVESTIGADOR"
    ),
    (AgentId.EDITOR, "BLOQUEADO"): OpinionMapping(
        AssignmentStatus.BLOQUEADA, True, "DIRECAO_EDITORIAL"
    ),
    (AgentId.SOCIAL_MEDIA, "PRONTO PARA REVISÃO EDITORIAL"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_REVISAO_SOCIAL
    ),
    (AgentId.SOCIAL_MEDIA, "DEVOLVIDO AO FACT-CHECKER"): OpinionMapping(
        AssignmentStatus.DEVOLVIDA_A_FACT_CHECK, True, "FACT_CHECKER"
    ),
    (AgentId.SOCIAL_MEDIA, "DEVOLVIDO AO EDITOR"): OpinionMapping(
        AssignmentStatus.AGUARDANDO_REVISAO_SOCIAL, True, "EDITOR"
    ),
    (AgentId.SOCIAL_MEDIA, "DEVOLVIDO AO SOCIAL MEDIA"): OpinionMapping(
        AssignmentStatus.DEVOLVIDA_A_SOCIAL_MEDIA, True, "SOCIAL_MEDIA"
    ),
    (AgentId.SOCIAL_MEDIA, "BLOQUEADO"): OpinionMapping(
        AssignmentStatus.BLOQUEADA, True, "DIRECAO_EDITORIAL"
    ),
}


def map_editorial_opinion(agent_id: AgentId, opinion: str) -> OpinionMapping:
    """Mapeia apenas pareceres explícitos; não infere estados por semelhança textual."""
    key = (agent_id, opinion.strip())
    try:
        return _OPINION_MAP[key]
    except KeyError as exc:
        raise UnsupportedEditorialOpinion(
            f"Parecer não mapeado para {agent_id}: {opinion!r}"
        ) from exc
