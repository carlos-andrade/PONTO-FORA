# PONTO-FORA — domínio editorial e máquina de estados
# Identificador: PF-COD-DOMAIN-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Estados editoriais, atores e política explícita de transições.
# SHA-256 (conteúdo normalizado): PENDING
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

from dataclasses import dataclass
from enum import StrEnum


class AssignmentStatus(StrEnum):
    RECEBIDA = "RECEBIDA"
    EM_TRIAGEM = "EM_TRIAGEM"
    AGUARDANDO_INVESTIGACAO = "AGUARDANDO_INVESTIGACAO"
    EM_INVESTIGACAO = "EM_INVESTIGACAO"
    INVESTIGACAO_PENDENTE = "INVESTIGACAO_PENDENTE"
    AGUARDANDO_FACT_CHECK = "AGUARDANDO_FACT_CHECK"
    EM_FACT_CHECK = "EM_FACT_CHECK"
    FACT_CHECK_PENDENTE = "FACT_CHECK_PENDENTE"
    BLOQUEADA = "BLOQUEADA"
    AGUARDANDO_REDACAO = "AGUARDANDO_REDACAO"
    EM_REDACAO = "EM_REDACAO"
    AGUARDANDO_EDICAO = "AGUARDANDO_EDICAO"
    EM_EDICAO = "EM_EDICAO"
    DEVOLVIDA_A_REDACAO = "DEVOLVIDA_A_REDACAO"
    DEVOLVIDA_A_FACT_CHECK = "DEVOLVIDA_A_FACT_CHECK"
    AGUARDANDO_DECISAO_EDITORIAL = "AGUARDANDO_DECISAO_EDITORIAL"
    APROVADA_PARA_PUBLICACAO = "APROVADA_PARA_PUBLICACAO"
    REJEITADA = "REJEITADA"
    AGUARDANDO_SOCIAL_MEDIA = "AGUARDANDO_SOCIAL_MEDIA"
    EM_PRODUCAO_SOCIAL = "EM_PRODUCAO_SOCIAL"
    AGUARDANDO_REVISAO_SOCIAL = "AGUARDANDO_REVISAO_SOCIAL"
    DEVOLVIDA_A_SOCIAL_MEDIA = "DEVOLVIDA_A_SOCIAL_MEDIA"
    APROVADA_PARA_DISTRIBUICAO = "APROVADA_PARA_DISTRIBUICAO"
    PUBLICADA = "PUBLICADA"
    EM_CORRECAO = "EM_CORRECAO"
    ATUALIZADA = "ATUALIZADA"
    ARQUIVADA = "ARQUIVADA"


class ActorType(StrEnum):
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"


class ActorRole(StrEnum):
    ORCHESTRATOR = "ORCHESTRATOR"
    EDITORIAL_DIRECTOR = "EDITORIAL_DIRECTOR"


@dataclass(frozen=True)
class Actor:
    actor_type: ActorType
    actor_id: str
    role: ActorRole


class DomainError(Exception):
    """Erro de regra de negócio."""


class InvalidTransition(DomainError):
    """Transição não prevista ou ainda não habilitada."""


class PermissionDenied(DomainError):
    """Ator sem autoridade para executar a transição."""


class VersionConflict(DomainError):
    """A versão esperada não corresponde à versão persistida."""


# A Fase B ativa apenas a passagem técnica inicial e a decisão de triagem.
# As restantes transições serão habilitadas quando os respetivos gates e
# contratos de evidência estiverem implementados nas fases seguintes.
TRANSITION_POLICY: dict[tuple[AssignmentStatus, AssignmentStatus], ActorRole] = {
    (AssignmentStatus.RECEBIDA, AssignmentStatus.EM_TRIAGEM): ActorRole.ORCHESTRATOR,
    (
        AssignmentStatus.EM_TRIAGEM,
        AssignmentStatus.AGUARDANDO_INVESTIGACAO,
    ): ActorRole.EDITORIAL_DIRECTOR,
    (AssignmentStatus.EM_TRIAGEM, AssignmentStatus.REJEITADA): ActorRole.EDITORIAL_DIRECTOR,
    (AssignmentStatus.EM_TRIAGEM, AssignmentStatus.BLOQUEADA): ActorRole.EDITORIAL_DIRECTOR,
}


def validate_transition(
    current: AssignmentStatus, target: AssignmentStatus, actor: Actor, reason: str | None
) -> None:
    required_role = TRANSITION_POLICY.get((current, target))
    if required_role is None:
        raise InvalidTransition(f"Transição não habilitada: {current} -> {target}.")
    if actor.role != required_role:
        raise PermissionDenied(f"A transição exige o papel {required_role}.")
    if actor.actor_type == ActorType.SYSTEM and actor.role != ActorRole.ORCHESTRATOR:
        raise PermissionDenied("Atores de sistema só podem atuar como ORCHESTRATOR.")
    if actor.actor_type == ActorType.HUMAN and actor.role == ActorRole.ORCHESTRATOR:
        raise PermissionDenied("ORCHESTRATOR é um papel técnico, não uma identidade humana.")
    if target in {AssignmentStatus.REJEITADA, AssignmentStatus.BLOQUEADA} and not (
        reason and reason.strip()
    ):
        raise DomainError("A rejeição ou o bloqueio exigem fundamentação.")
