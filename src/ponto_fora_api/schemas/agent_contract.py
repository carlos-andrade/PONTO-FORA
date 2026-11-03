# PONTO-FORA — contrato comum de saída dos agentes editoriais
# Identificador: PF-COD-SCHEMA-AGENT-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software e Governança Editorial
# Âmbito: Validação do envelope comum e dos campos específicos de cada agente.
# SHA-256 (conteúdo normalizado): cc584c44ba1f8b60e1b0d2f6f8d86ee83d6c30a346656ffbed901c12821ad22d
# Commit de referência (base documental): cb1a16e6be6e890e64f3d0ca67f9ad22dcc974df

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AgentId(StrEnum):
    INVESTIGADOR = "INVESTIGADOR"
    FACT_CHECKER = "FACT_CHECKER"
    REDATOR = "REDATOR"
    EDITOR = "EDITOR"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"


class ExecutionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYABLE = "RETRYABLE"


class AgentEnvelope(BaseModel):
    """Envelope de integração; execução técnica e parecer editorial são independentes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    pauta_id: UUID
    artifact_id: str = Field(min_length=1, max_length=160)
    artifact_version: str = Field(min_length=1, max_length=40)
    agent_id: AgentId
    agent_version: str = Field(min_length=1, max_length=40)
    prompt_version: str = Field(min_length=1, max_length=40)
    execution_id: UUID
    input_artifact_ids: list[str] = Field(min_length=1)
    input_versions: dict[str, str] = Field(min_length=1)
    execution_status: ExecutionStatus
    editorial_opinion: str = Field(min_length=1, max_length=120)
    output_artifact_id: str = Field(min_length=1, max_length=160)
    output_version: str = Field(min_length=1, max_length=40)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    created_at: datetime
    correlation_id: UUID

    claim_verdicts: dict[str, str] | None = None
    fact_check_decision: str | None = None
    news_draft_id: str | None = None
    claim_traceability: dict[str, list[str]] | None = None
    editorial_findings: list[dict[str, Any]] | None = None
    severity: str | None = None
    editorial_decision: str | None = None
    source_news_id: str | None = None
    source_news_version: str | None = None
    piece_id: str | None = None
    channel: str | None = None
    format: str | None = None
    rights_status: str | None = None

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at deve incluir fuso horário.")
        return value

    @model_validator(mode="after")
    def require_agent_fields(self):
        required: dict[AgentId, tuple[str, ...]] = {
            AgentId.FACT_CHECKER: ("claim_verdicts", "fact_check_decision"),
            AgentId.REDATOR: ("news_draft_id", "claim_traceability"),
            AgentId.EDITOR: ("editorial_findings", "severity", "editorial_decision"),
            AgentId.SOCIAL_MEDIA: (
                "source_news_id",
                "source_news_version",
                "piece_id",
                "channel",
                "format",
                "rights_status",
            ),
        }
        missing = [
            field
            for field in required.get(self.agent_id, ())
            if getattr(self, field) is None
        ]
        if missing:
            raise ValueError(
                f"Campos específicos obrigatórios para {self.agent_id}: "
                + ", ".join(missing)
            )
        missing_versions = set(self.input_artifact_ids) - set(self.input_versions)
        if missing_versions:
            raise ValueError(
                "Faltam versões de entrada para: " + ", ".join(sorted(missing_versions))
            )
        if "RESSALVAS" in self.editorial_opinion.upper() and not self.caveats:
            raise ValueError("Parecer com ressalvas exige caveats não vazios.")
        return self
