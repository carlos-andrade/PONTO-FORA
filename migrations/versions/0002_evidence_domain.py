# PONTO-FORA — migração do domínio factual
# Identificador: PF-MIG-0002
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Persistir fontes, afirmações, evidências, relações probatórias e avaliações factuais.
# SHA-256 (conteúdo normalizado): PENDENTE
# Commit de referência (base documental): c5d4cf29b6d2ab23b99439852235868c3b422195

import sqlalchemy as sa
from alembic import op

revision = "0002_evidence_domain"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("canonical_url", sa.String(2048), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("publisher", sa.String(240)),
        sa.Column("author", sa.String(240)),
        sa.Column("source_type", sa.String(24), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at_source", sa.DateTime(timezone=True)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(24)),
        sa.Column("content_sha256", sa.String(64)),
        sa.Column("storage_uri", sa.String(2048)),
        sa.Column("access_status", sa.String(24), nullable=False),
        sa.Column("independence_group", sa.String(240)),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.CheckConstraint("source_type IN ('PRIMARY','SECONDARY','REFERENCE','SOCIAL','UNKNOWN')", name="ck_source_type"),
        sa.CheckConstraint("access_status IN ('AVAILABLE','UNAVAILABLE','RESTRICTED','REMOVED','NOT_CHECKED')", name="ck_source_access_status"),
        sa.CheckConstraint("content_sha256 IS NULL OR length(content_sha256) = 64", name="ck_source_sha256"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "assignment_id", name="uq_source_id_assignment"),
    )
    op.create_index("ix_sources_assignment_retrieved", "source_records", ["assignment_id", "retrieved_at"])

    op.create_table(
        "claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(24), nullable=False),
        sa.Column("materiality", sa.String(16), nullable=False),
        sa.Column("attribution", sa.Text()),
        sa.Column("context_note", sa.Text()),
        sa.Column("created_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_claim_id", sa.Uuid()),
        sa.CheckConstraint("claim_type IN ('FACTUAL','QUANTITATIVE','QUOTE','DATE','CAUSAL','PREDICTIVE','OPINION','MIXED')", name="ck_claim_type"),
        sa.CheckConstraint("materiality IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_claim_materiality"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supersedes_claim_id", "assignment_id"], ["claims.id", "claims.assignment_id"], ondelete="RESTRICT", name="fk_claim_supersedes_same_assignment"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "assignment_id", name="uq_claim_id_assignment"),
    )
    op.create_index("ix_claims_assignment_materiality", "claims", ["assignment_id", "materiality"])

    op.create_table(
        "evidence_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("locator", sa.String(2048), nullable=False),
        sa.Column("excerpt", sa.Text()),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("evidence_type", sa.String(24), nullable=False),
        sa.Column("polarity", sa.String(24), nullable=False),
        sa.Column("collected_by", sa.String(160), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_sha256", sa.String(64)),
        sa.Column("limitations", sa.Text()),
        sa.CheckConstraint("evidence_type IN ('DOCUMENT','DATASET','QUOTE','IMAGE','AUDIO','VIDEO','OBSERVATION','OTHER')", name="ck_evidence_type"),
        sa.CheckConstraint("polarity IN ('SUPPORTS','CONTRADICTS','CONTEXTUALIZES','NEUTRAL')", name="ck_evidence_polarity"),
        sa.CheckConstraint("content_sha256 IS NULL OR length(content_sha256) = 64", name="ck_evidence_sha256"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_id", "assignment_id"], ["source_records.id", "source_records.assignment_id"], ondelete="RESTRICT", name="fk_evidence_source_same_assignment"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "assignment_id", name="uq_evidence_id_assignment"),
    )
    op.create_index("ix_evidence_assignment_collected", "evidence_records", ["assignment_id", "collected_at"])

    op.create_table(
        "claim_evidence_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("relationship", sa.String(24), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("assessed_by", sa.String(160), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assessment_version", sa.Integer(), nullable=False),
        sa.CheckConstraint("relationship IN ('SUPPORTS','CONTRADICTS','CONTEXTUALIZES','DOES_NOT_ADDRESS')", name="ck_claim_evidence_relationship"),
        sa.CheckConstraint("assessment_version >= 1", name="ck_link_assessment_version"),
        sa.ForeignKeyConstraint(["claim_id", "assignment_id"], ["claims.id", "claims.assignment_id"], ondelete="RESTRICT", name="fk_link_claim_same_assignment"),
        sa.ForeignKeyConstraint(["evidence_id", "assignment_id"], ["evidence_records.id", "evidence_records.assignment_id"], ondelete="RESTRICT", name="fk_link_evidence_same_assignment"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_id", "evidence_id", name="uq_claim_evidence_pair"),
    )
    op.create_index("ix_claim_evidence_assignment", "claim_evidence_links", ["assignment_id"])

    op.create_table(
        "fact_check_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text()),
        sa.Column("reviewer_type", sa.String(8), nullable=False),
        sa.Column("reviewer_id", sa.String(160), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assessment_version", sa.Integer(), nullable=False),
        sa.Column("supersedes_assessment_id", sa.Uuid()),
        sa.CheckConstraint("verdict IN ('CONFIRMADA','MAIORITARIAMENTE_CONFIRMADA','PARCIALMENTE_CONFIRMADA','ENGANOSA','DESCONTEXTUALIZADA','CONTRADITA','NAO_COMPROVADA','INCONCLUSIVA','DESATUALIZADA','NAO_FACTUAL')", name="ck_fact_check_verdict"),
        sa.CheckConstraint("reviewer_type IN ('HUMAN','AI')", name="ck_assessment_reviewer_type"),
        sa.CheckConstraint("assessment_version >= 1", name="ck_assessment_version"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["claim_id", "assignment_id"], ["claims.id", "claims.assignment_id"], ondelete="RESTRICT", name="fk_assessment_claim_same_assignment"),
        sa.ForeignKeyConstraint(["supersedes_assessment_id", "assignment_id"], ["fact_check_assessments.id", "fact_check_assessments.assignment_id"], ondelete="RESTRICT", name="fk_assessment_supersedes_same_assignment"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "assignment_id", name="uq_assessment_id_assignment"),
        sa.UniqueConstraint("assignment_id", "claim_id", "assessment_version", name="uq_assessment_claim_version"),
    )
    op.create_index("ix_assessments_assignment_claim", "fact_check_assessments", ["assignment_id", "claim_id", "assessment_version"])


def downgrade() -> None:
    op.drop_index("ix_assessments_assignment_claim", table_name="fact_check_assessments")
    op.drop_table("fact_check_assessments")
    op.drop_index("ix_claim_evidence_assignment", table_name="claim_evidence_links")
    op.drop_table("claim_evidence_links")
    op.drop_index("ix_evidence_assignment_collected", table_name="evidence_records")
    op.drop_table("evidence_records")
    op.drop_index("ix_claims_assignment_materiality", table_name="claims")
    op.drop_table("claims")
    op.drop_index("ix_sources_assignment_retrieved", table_name="source_records")
    op.drop_table("source_records")
