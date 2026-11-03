# PONTO-FORA — contratos Pydantic do domínio factual
# Identificador: PF-COD-SCHEMAS-EVIDENCE-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Validar payloads de fontes, afirmações, evidências, relações e avaliações factuais.
# SHA-256 (conteúdo normalizado): 622bdb45ce7c7d46a076e89f2727788a5deb30e5a0ab578a098909a6e1a077bb
# Commit de referência (base documental): c5d4cf29b6d2ab23b99439852235868c3b422195

from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(StrEnum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    REFERENCE = "REFERENCE"
    SOCIAL = "SOCIAL"
    UNKNOWN = "UNKNOWN"


class AccessStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    RESTRICTED = "RESTRICTED"
    REMOVED = "REMOVED"
    NOT_CHECKED = "NOT_CHECKED"


class ClaimType(StrEnum):
    FACTUAL = "FACTUAL"
    QUANTITATIVE = "QUANTITATIVE"
    QUOTE = "QUOTE"
    DATE = "DATE"
    CAUSAL = "CAUSAL"
    PREDICTIVE = "PREDICTIVE"
    OPINION = "OPINION"
    MIXED = "MIXED"


class Materiality(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceType(StrEnum):
    DOCUMENT = "DOCUMENT"
    DATASET = "DATASET"
    QUOTE = "QUOTE"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    OBSERVATION = "OBSERVATION"
    OTHER = "OTHER"


class EvidencePolarity(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXTUALIZES = "CONTEXTUALIZES"
    NEUTRAL = "NEUTRAL"


class EvidenceRelationship(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXTUALIZES = "CONTEXTUALIZES"
    DOES_NOT_ADDRESS = "DOES_NOT_ADDRESS"


class FactCheckVerdict(StrEnum):
    CONFIRMADA = "CONFIRMADA"
    MAIORITARIAMENTE_CONFIRMADA = "MAIORITARIAMENTE_CONFIRMADA"
    PARCIALMENTE_CONFIRMADA = "PARCIALMENTE_CONFIRMADA"
    ENGANOSA = "ENGANOSA"
    DESCONTEXTUALIZADA = "DESCONTEXTUALIZADA"
    CONTRADITA = "CONTRADITA"
    NAO_COMPROVADA = "NAO_COMPROVADA"
    INCONCLUSIVA = "INCONCLUSIVA"
    DESATUALIZADA = "DESATUALIZADA"
    NAO_FACTUAL = "NAO_FACTUAL"


class ReviewerType(StrEnum):
    HUMAN = "HUMAN"
    AI = "AI"


class ContractBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceCreate(ContractBase):
    canonical_url: str = Field(min_length=8, max_length=2048)
    title: str = Field(min_length=1, max_length=500)
    publisher: str | None = Field(default=None, max_length=240)
    author: str | None = Field(default=None, max_length=240)
    source_type: SourceType = SourceType.UNKNOWN
    published_at: datetime | None = None
    updated_at_source: datetime | None = None
    retrieved_at: datetime
    language: str | None = Field(default=None, max_length=24)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    storage_uri: str | None = Field(default=None, max_length=2048)
    access_status: AccessStatus = AccessStatus.NOT_CHECKED
    independence_group: str | None = Field(default=None, max_length=240)
    metadata: dict = Field(default_factory=dict)

    @field_validator("canonical_url")
    @classmethod
    def validate_http_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("A URL da fonte deve usar HTTP ou HTTPS e conter hostname.")
        if parsed.username or parsed.password:
            raise ValueError("A URL não pode conter credenciais.")
        if parsed.hostname.lower() in {"localhost"}:
            raise ValueError("Host local não é permitido como fonte.")
        return value


class ClaimCreate(ContractBase):
    claim_text: str = Field(min_length=1)
    claim_type: ClaimType = ClaimType.FACTUAL
    materiality: Materiality = Materiality.MEDIUM
    attribution: str | None = None
    context_note: str | None = None
    created_by: str = Field(min_length=1, max_length=160)
    supersedes_claim_id: UUID | None = None


class EvidenceCreate(ContractBase):
    source_id: UUID
    locator: str = Field(min_length=1, max_length=2048)
    excerpt: str | None = None
    observation: str = Field(min_length=1)
    evidence_type: EvidenceType = EvidenceType.OTHER
    polarity: EvidencePolarity = EvidencePolarity.NEUTRAL
    collected_by: str = Field(min_length=1, max_length=160)
    collected_at: datetime
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    limitations: str | None = None


class ClaimEvidenceCreate(ContractBase):
    claim_id: UUID
    evidence_id: UUID
    relationship: EvidenceRelationship
    rationale: str = Field(min_length=1)
    assessed_by: str = Field(min_length=1, max_length=160)
    assessed_at: datetime
    assessment_version: int = Field(default=1, ge=1)


class FactCheckAssessmentCreate(ContractBase):
    claim_id: UUID
    verdict: FactCheckVerdict
    reasoning_summary: str = Field(min_length=1)
    limitations: str | None = None
    reviewer_type: ReviewerType
    reviewer_id: str = Field(min_length=1, max_length=160)
    assessed_at: datetime
    assessment_version: int = Field(default=1, ge=1)
    supersedes_assessment_id: UUID | None = None
