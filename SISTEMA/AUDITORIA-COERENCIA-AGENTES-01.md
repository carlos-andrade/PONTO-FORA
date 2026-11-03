# AUDITORIA DE COERÊNCIA ENTRE AGENTES E ORQUESTRADOR — PONTO-FORA

**Identificador:** PF-SYS-AUD-001  
**Versão:** 1.0  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Concluída — harmonização pendente  
**Responsável:** Governança e Direção Editorial do PONTO-FORA  
**Âmbito:** Auditoria documental dos cinco agentes editoriais e do Orquestrador Editorial; contratos, pareceres, estados e autoridade.  
**SHA-256 (conteúdo normalizado):** 246cc737f6c6fe49fe53fe63355cd9749e4aa7db9d862b2a5664457ee607c510  
**Commit de referência (base documental):** c34d0fcdd03e8235bafc540911a175ea128e994c

## 1. OBJETIVO E LIMITES

Auditoria documental dos agentes Investigador, Fact-checker, Redator, Editor e Social Media, em relação ao Orquestrador Editorial, com base nos ficheiros existentes na branch main em 03/11/2026. Não foram executados agentes, testes funcionais, APIs ou integrações de produção.

## 2. RESULTADO EXECUTIVO

**Conclusão: COERÊNCIA PARCIAL.** As funções gerais são compatíveis, mas os contratos de passagem, a tradução de pareceres em estados e a distinção entre aprovação editorial e autorização operacional precisam de harmonização.

Foram identificados 12 pontos:

| ID | Prioridade | Constatação | Correção |
|---|---|---|---|
| AUD-01 | P0 | Pareceres do Investigador sem mapeamento inequívoco. | Mapear pareceres para estados. |
| AUD-02 | P0 | Ressalvas do Fact-checker podem perder-se na passagem. | Transportar claims, veredictos, ressalvas e decisão. |
| AUD-03 | P1 | Parecer do Redator sem mapeamento formal. | Associar conclusão a AGUARDANDO_EDICAO. |
| AUD-04 | P1 | “APROVADO COM AJUSTES MENORES” é ambíguo. | Não avançar até ajustes aplicados e revalidados. |
| AUD-05 | P1 | Parecer do Social Media sem estado formal. | Mapear para AGUARDANDO_REVISAO_SOCIAL. |
| AUD-06 | P0 | Responsabilidade de revisão social pouco explícita. | Editor revê tecnicamente; Direção Editorial decide. |
| AUD-07 | P0 | APROVADA_PARA_PUBLICACAO pode ser confundida com autorização de publicar. | Significa apenas aprovação editorial da notícia-base. |
| AUD-08 | P0 | Autorização não está granular. | Vincular a peça, canal, versão, responsável e data/hora. |
| AUD-09 | P1 | Devoluções podem não identificar o problema exato. | Exigir claim_id, artifact_id, trecho, motivo e destino. |
| AUD-10 | P0 | Estado técnico e parecer editorial podem ser confundidos. | Separar execution_status de editorial_opinion. |
| AUD-11 | P0 | Derivados sociais sem vínculo imutável suficientemente formalizado. | Exigir source_news_id e source_news_version. |
| AUD-12 | P1 | Reabertura de estados terminais sem regra uniforme. | Reabrir por novo evento/versão ou decisão humana, preservando histórico. |

## 3. MAPEAMENTO CANÓNICO DE PARECERES

O parecer original deve ser preservado literalmente. O estado abaixo é a tradução operacional do Orquestrador.

| Agente | Parecer | Estado |
|---|---|---|
| Investigador | APTO PARA FACT-CHECKING | AGUARDANDO_FACT_CHECK |
| Investigador | APTO COM RESSALVAS | AGUARDANDO_FACT_CHECK, com ressalvas obrigatórias |
| Investigador | INVESTIGAÇÃO INSUFICIENTE | INVESTIGACAO_PENDENTE |
| Investigador | BLOQUEADO | BLOQUEADA |
| Fact-checker | APROVADO PARA REDAÇÃO | AGUARDANDO_REDACAO |
| Fact-checker | APROVADO COM RESSALVAS | AGUARDANDO_REDACAO, com ressalvas obrigatórias |
| Fact-checker | DEVOLVIDO À INVESTIGAÇÃO | INVESTIGACAO_PENDENTE |
| Fact-checker | BLOQUEADO | BLOQUEADA |
| Redator | REDAÇÃO CONCLUÍDA — PRONTA PARA EDIÇÃO | AGUARDANDO_EDICAO |
| Redator | DEVOLVIDO AO FACT-CHECKER | DEVOLVIDA_A_FACT_CHECK |
| Redator | DEVOLVIDO À INVESTIGAÇÃO | INVESTIGACAO_PENDENTE |
| Redator | BLOQUEADO | BLOQUEADA |
| Editor | APROVADO PARA DECISÃO EDITORIAL | AGUARDANDO_DECISAO_EDITORIAL |
| Editor | APROVADO COM AJUSTES MENORES | Permanece em edição até correção e revalidação |
| Editor | DEVOLVIDO AO REDATOR | DEVOLVIDA_A_REDACAO |
| Editor | DEVOLVIDO AO FACT-CHECKER | DEVOLVIDA_A_FACT_CHECK |
| Editor | DEVOLVIDO À INVESTIGAÇÃO | INVESTIGACAO_PENDENTE |
| Editor | BLOQUEADO | BLOQUEADA |
| Social Media | PRONTO PARA REVISÃO EDITORIAL | AGUARDANDO_REVISAO_SOCIAL |
| Social Media | DEVOLVIDO AO FACT-CHECKER | DEVOLVIDA_A_FACT_CHECK |
| Social Media | DEVOLVIDO AO EDITOR | AGUARDANDO_REVISAO_SOCIAL, com correção pendente |
| Social Media | DEVOLVIDO AO SOCIAL MEDIA | DEVOLVIDA_A_SOCIAL_MEDIA |
| Social Media | BLOQUEADO | BLOQUEADA |

Parecer não mapeado suspende a transição e exige intervenção humana; não inferir equivalências por semelhança textual.

## 4. CONTRATO COMUM MÍNIMO

Todos os agentes devem devolver: pauta_id, artifact_id, artifact_version, agent_id, agent_version, prompt_version, execution_id, input_artifact_ids, input_versions, execution_status (SUCCESS, FAILED, RETRYABLE), editorial_opinion, output_artifact_id, output_version, claim_ids, evidence_refs, caveats, unresolved_questions, created_at com fuso horário e correlation_id.

Campos especializados:
- Fact-checker: claim_verdicts e fact_check_decision.
- Redator: news_draft_id e claim_traceability.
- Editor: editorial_findings, severity e editorial_decision.
- Social Media: source_news_id, source_news_version, piece_id, channel, format e rights_status.

SUCCESS não significa aprovação editorial. Parecer favorável não corrige execução FAILED. As dimensões são independentes.

## 5. AUTORIDADE E PUBLICAÇÃO

1. A aprovação da notícia-base é decisão editorial humana sobre uma versão identificada.
2. APROVADA_PARA_PUBLICACAO significa apenas “notícia-base aprovada editorialmente”; não autoriza publicação, envio ou distribuição.
3. Cada autorização operacional contém piece_id, channel, artifact_version, approved_by, approved_at e authorization_scope.
4. O Editor revê fidelidade, afirmações, linguagem, cortes, decupagem, atribuições, direitos e acessibilidade das peças sociais.
5. A Direção Editorial mantém a decisão final e autoriza cada peça, canal e versão.
6. Cada peça social referencia a versão imutável da notícia-base. Alterações na notícia exigem reavaliação dos derivados afetados.
7. Devoluções identificam artefacto, afirmação, trecho, motivo, destino e ação exigida.

## 6. REABERTURA E ESTADOS TERMINAIS

REJEITADA, ARQUIVADA, PUBLICADA ou BLOQUEADA não devem ser reescritos retroativamente. A reabertura exige novo evento com ator, data/hora, motivo, estado anterior, novo estado e referência à versão ou decisão justificadora. Preservar a versão anteriormente aprovada.

## 7. PRÓXIMAS AÇÕES

1. Incorporar os mapeamentos e gates no Orquestrador V1.1.
2. Formalizar o envelope comum nos cinco agentes.
3. Atualizar o Inventário Documental.
4. Recalcular e verificar SHA-256 e commits efetivos.
5. Executar testes de integração para pareceres válidos/desconhecidos, ressalvas, devoluções, bloqueios, divergência entre execução e parecer, autorização granular e reabertura.

## 8. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 1.0 | Auditoria documental dos cinco agentes e Orquestrador; 12 pontos e contrato comum proposto. |

---
**PONTO-FORA — A NOTÍCIA VAI ALÉM DO FACTO. O IMPORTANTE É ENTENDER O QUE ESTÁ POR TRÁS DELE.**
