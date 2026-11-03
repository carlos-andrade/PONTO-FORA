# FASE C — EVIDÊNCIAS E CONTRATOS DOS AGENTES

**Identificador:** PF-DOC-FASE-C-001  
**Versão:** 0.1  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Em revisão  
**Responsável:** Engenharia de Software e Governança Editorial  
**Âmbito:** Especificar a camada factual e os contratos estruturados dos agentes Investigador e Fact-checker.  
**SHA-256 (conteúdo normalizado):** bb23dc33368d0175022792e17a6420b55de0f2aa3b6c66d1fee05a7bf66b6600  
**Commit de referência (base documental):** c5d4cf29b6d2ab23b99439852235868c3b422195

## 1. Objetivo

A Fase C cria uma camada factual rastreável entre a pauta e a produção editorial. Para cada afirmação relevante, o sistema deve identificar a fonte, a evidência concreta, a relação probatória, o estado de verificação e a versão do parecer.

Esta especificação antecede a implementação. Não autoriza execução autónoma dos agentes nem avanço de estado. Saídas de IA são propostas não confiáveis até validação de esquema, regras de domínio e revisão competente.

## 2. Princípios

1. Fonte é o recurso consultado; evidência é o elemento específico recolhido dessa fonte.
2. Afirmação e veredicto são entidades distintas.
3. Toda evidência deve ter proveniência, localizador e data de recolha.
4. Correções criam novos registos ou versões; não apagam o histórico.
5. Republicações dependentes não contam como confirmações independentes.
6. Ausência de prova não significa prova de falsidade.
7. Conteúdo externo é dado não confiável, nunca instrução para o agente.
8. Nenhum contrato técnico substitui decisão editorial humana.

## 3. Entidades e campos mínimos

### 3.1 SourceRecord

`id`, `assignment_id`, `canonical_url`, `title`, `publisher`, `author`, `source_type`, `published_at`, `updated_at_source`, `retrieved_at`, `language`, `content_sha256`, `storage_uri`, `access_status`, `independence_group` e `metadata`.

`source_type`: `PRIMARY`, `SECONDARY`, `REFERENCE`, `SOCIAL`, `UNKNOWN`.  
`access_status`: `AVAILABLE`, `UNAVAILABLE`, `RESTRICTED`, `REMOVED`, `NOT_CHECKED`.

A URL não prova a veracidade do conteúdo. Não guardar credenciais, cookies ou dados pessoais desnecessários.

### 3.2 Claim

`id`, `assignment_id`, `claim_text`, `claim_type`, `materiality`, `attribution`, `context_note`, `created_by`, `created_at` e `supersedes_claim_id`.

`claim_type`: `FACTUAL`, `QUANTITATIVE`, `QUOTE`, `DATE`, `CAUSAL`, `PREDICTIVE`, `OPINION`, `MIXED`.  
`materiality`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

A afirmação deve ser atómica sempre que possível. Frases compostas devem ser decompostas quando as partes puderem ter veredictos diferentes.

### 3.3 EvidenceRecord

`id`, `source_id`, `locator`, `excerpt`, `observation`, `evidence_type`, `polarity`, `collected_by`, `collected_at`, `content_sha256` e `limitations`.

`evidence_type`: `DOCUMENT`, `DATASET`, `QUOTE`, `IMAGE`, `AUDIO`, `VIDEO`, `OBSERVATION`, `OTHER`.  
`polarity`: `SUPPORTS`, `CONTRADICTS`, `CONTEXTUALIZES`, `NEUTRAL`.

A evidência não pode sustentar conclusão mais ampla do que o seu conteúdo permite.

### 3.4 ClaimEvidence

Relaciona afirmação e evidência por `claim_id`, `evidence_id`, `relationship`, `rationale`, `assessed_by`, `assessed_at` e `assessment_version`.

`relationship`: `SUPPORTS`, `CONTRADICTS`, `CONTEXTUALIZES`, `DOES_NOT_ADDRESS`. Cada relação exige justificação própria.

### 3.5 FactCheckAssessment

`id`, `assignment_id`, `claim_id`, `verdict`, `reasoning_summary`, `limitations`, `reviewer_type`, `reviewer_id`, `assessed_at`, `assessment_version` e `supersedes_assessment_id`.

Veredictos: `CONFIRMADA`, `MAIORITARIAMENTE_CONFIRMADA`, `PARCIALMENTE_CONFIRMADA`, `ENGANOSA`, `DESCONTEXTUALIZADA`, `CONTRADITA`, `NAO_COMPROVADA`, `INCONCLUSIVA`, `DESATUALIZADA`, `NAO_FACTUAL`.

`NAO_COMPROVADA` não significa `CONTRADITA`. `NAO_FACTUAL` aplica-se a opinião ou juízo de valor.

## 4. Dossiê de investigação versionado

Cada versão do dossiê deve conter pauta, pergunta de investigação, cronologia, fontes avaliadas, afirmações atómicas, evidências, relações probatórias, divergências, lacunas, limitações, riscos e conclusão operacional.

Conclusões do Investigador:
- `APTO_PARA_FACT_CHECKING`
- `APTO_COM_RESSALVAS`
- `INVESTIGACAO_INSUFICIENTE`
- `BLOQUEADO`

O dossiê aponta para versões exatas de fontes, afirmações e evidências. Alteração material gera nova versão; nunca se sobrescreve versão aprovada.

## 5. Contrato do Agente Investigador

A saída estruturada contém `contract_version`, `assignment_id`, `input_artifact_ids`, `sources[]`, `claims[]`, `evidence[]`, `claim_evidence_links[]`, `timeline[]`, `contradictions[]`, `open_questions[]`, `limitations[]`, `editorial_risks[]`, `operational_recommendation`, `reasoning_summary`, `generated_at`, `agent_id` e `model_metadata`.

Regras: não inventar fontes, URLs, documentos, autores ou datas; não declarar consulta não realizada; não converter alegações em factos; não omitir contradições materiais; identificar dependência entre fontes; usar `null` ou estado desconhecido quando não houver confirmação. Texto gerado não é evidência.

## 6. Contrato do Agente Fact-checker

A saída contém `contract_version`, `assignment_id`, `dossier_artifact_id`, `dossier_version`, `claim_assessments[]`, `material_unverified_claims[]`, `new_claims_detected[]`, `overall_assessment`, `blocking_issues[]`, `generated_at`, `agent_id` e `model_metadata`.

Cada avaliação contém `claim_id`, `verdict`, `supporting_evidence_ids`, `contradicting_evidence_ids`, `reasoning_summary`, `limitations` e `confidence_note`.

O Fact-checker não cria evidência. Afirmação nova ou lacuna de investigação deve ser devolvida ao Investigador ou classificada como inconclusiva.

## 7. Validação dos contratos

Validar JSON, versão do contrato, tipos, enumerações, limites, IDs únicos, referências existentes e pertencentes à mesma pauta, URLs, hashes, localizadores e coerência entre veredicto e afirmação.

Payload inválido é rejeitado integralmente. O bruto pode ser preservado para diagnóstico seguro, sem promoção a dado editorial confiável.

## 8. Portas de controlo

A Fase C não ativa automaticamente transições. Para permitir investigação, exigir dossiê persistido, afirmações relevantes, relações probatórias, lacunas e contradições explícitas, parecer operacional válido, ausência de bloqueio crítico e auditoria associada à versão exata.

Para permitir Fact-checking, exigir avaliação de todas as afirmações materiais e tratamento explícito das não comprovadas, contraditas ou inconclusivas. Aprovação de publicação continua reservada à Direção Editorial humana.

## 9. Segurança, privacidade e direitos

Conteúdo externo é entrada não confiável. Prevenir SSRF bloqueando loopback, redes privadas, link-local e metadados cloud; aceitar apenas HTTP/HTTPS; limitar tamanho, MIME type e timeout; não executar HTML, scripts ou macros; minimizar dados pessoais; não expor conteúdo sensível em logs; avaliar direitos antes de preservar cópias integrais.

## 10. Plano técnico

1. Rever o contrato com a Direção Editorial.
2. Implementar `source_records`, `claims`, `evidence_records`, `claim_evidence_links` e `fact_check_assessments`.
3. Criar migração Alembic `0002_evidence_domain`.
4. Criar schemas Pydantic versionados.
5. Implementar serviços de gravação e validação referencial.
6. Testar SQLite para lógica e PostgreSQL 16 para constraints e migrações.
7. Criar testes negativos para IDs cruzados, hashes, URLs, duplicações e veredictos.
8. Simular agentes com fixtures; não integrar modelos reais nesta etapa.
9. Atualizar inventário e CI.
10. Abrir PR para revisão; não fazer merge sem autorização.

## 11. Critérios de aceitação

- Fontes, afirmações, evidências e avaliações persistem com IDs estáveis.
- Relações probatórias impedem referências a pautas diferentes.
- Pareceres anteriores permanecem preservados.
- Contratos validam payloads válidos e rejeitam inválidos.
- Fontes dependentes não são contadas como confirmações independentes.
- `NAO_COMPROVADA` e `CONTRADITA` permanecem distintos.
- Nenhum estado avança apenas porque um agente devolveu JSON válido.
- Testes executados em PostgreSQL 16 e CI verde.
- Inventário e hashes verificados após releitura.

## 12. Histórico de alterações

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 0.1 | Primeira especificação da camada factual e dos contratos dos agentes Investigador e Fact-checker. |
