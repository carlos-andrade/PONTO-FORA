# RBAC — MODELO DE PAPÉIS E PERMISSÕES

**Identificador:** PF-SYS-RBAC-001  
**Versão:** 1.0  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Em revisão  
**Responsável:** Engenharia de Software  
**Âmbito:** Modelo de autorização por papéis para utilizadores humanos e identidades técnicas da plataforma PONTO-FORA.  
**SHA-256 (conteúdo normalizado):** 2edf24629e444c1b4d885b80e28a930c79b2239b037e7aeba46b00b654b81ee6  
**Commit de referência (base documental):** 0c4e4d012f2c23bd7da134f9d2c06c249901bcf3

## 1. Objetivo

Definir a camada RBAC (Role-Based Access Control) da API PONTO-FORA, separando autenticação de autorização. A autenticação OIDC identifica o sujeito; o RBAC da aplicação determina o que esse sujeito pode executar.

Um token válido não concede, por si só, qualquer papel editorial. Claims de `roles`, `groups` ou permissões enviados pelo provedor OIDC não são fonte de autoridade para operações editoriais.

## 2. Princípios obrigatórios

1. **Negação por omissão:** qualquer operação sem permissão explícita é negada.
2. **Menor privilégio:** cada papel recebe apenas as permissões necessárias à sua função.
3. **Autorização no servidor:** a interface não é uma fronteira de segurança.
4. **Identidade persistente:** o sujeito OIDC é associado a uma identidade interna; email e nome são atributos informativos, não chaves de autorização.
5. **Separação de funções:** administrar acessos não equivale a aprovar conteúdo; produzir conteúdo não equivale a autorizar publicação.
6. **Auditoria:** alterações de papéis, concessões, revogações e decisões privilegiadas devem ser registadas.
7. **Controlo de versão:** aprovações e autorizações devem referir a versão imutável exata do artefacto.
8. **Identidades técnicas distintas:** serviços e agentes não devem reutilizar a identidade de uma pessoa.
9. **Sem escalada por token:** papéis e permissões não são aceites diretamente de claims externos.
10. **Falha segura:** indisponibilidade ou inconsistência do serviço de autorização não deve permitir a operação.

## 3. Catálogo inicial de papéis

| Papel | Tipo | Responsabilidade |
|---|---|---|
| `PLATFORM_ADMIN` | Humano | Gestão técnica de utilizadores, associações de identidade e atribuições de papéis. Não aprova conteúdo por privilégio administrativo. |
| `EDITORIAL_DIRECTOR` | Humano | Triagem, decisões editoriais e decisões de bloqueio/rejeição nos gates autorizados. |
| `INVESTIGATOR` | Humano | Registar fontes, alegações, evidências e contexto de investigação. |
| `FACT_CHECKER` | Humano | Avaliar alegações e evidências, emitir parecer factual e identificar limitações. |
| `WRITER` | Humano | Criar e rever versões de texto editorial. |
| `EDITOR` | Humano | Rever conteúdo, solicitar alterações e preparar versões para decisão editorial. |
| `SOCIAL_EDITOR` | Humano | Criar e rever derivados para redes sociais a partir de conteúdo elegível. |
| `PUBLISHER` | Humano | Executar publicação apenas após autorização específica para artefacto, versão e canal. |
| `AUDITOR` | Humano | Consultar registos de auditoria e trilhos de decisão, sem alterar conteúdo ou permissões. |
| `SYSTEM_ORCHESTRATOR` | Serviço | Executar transições técnicas explicitamente autorizadas e tarefas internas. Não representa uma pessoa nem decide mérito editorial. |

Os papéis acima são um catálogo proposto. A atribuição de papéis a pessoas reais não faz parte desta especificação.

## 4. Matriz inicial de permissões

Legenda: **P** = permitido; **—** = não permitido. A permissão efetiva depende também do estado do workflow, do recurso, da versão e das regras de separação de funções.

| Capacidade | Admin | Dir. Editorial | Investigador | Fact-checker | Redator | Editor | Social | Publisher | Auditor | Orchestrator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gerir identidades e papéis | P | — | — | — | — | — | — | — | — | — |
| Consultar pautas | P | P | P | P | P | P | P | P | P | P |
| Criar/triagem de pauta | — | P | — | — | — | — | — | — | — | P* |
| Registar fontes e evidências | — | — | P | P | — | — | — | — | — | P* |
| Avaliar alegações | — | — | — | P | — | — | — | — | — | — |
| Redigir artefacto editorial | — | — | — | — | P | P | — | — | — | — |
| Rever/solicitar alterações editoriais | — | P | — | — | — | P | — | — | — | — |
| Decisão editorial final | — | P | — | — | — | — | — | — | — | — |
| Criar derivados sociais | — | — | — | — | — | — | P | — | — | — |
| Autorizar distribuição por canal | — | P** | — | — | — | — | — | — | — | — |
| Executar publicação autorizada | — | — | — | — | — | — | — | P | — | P* |
| Consultar auditoria | P | P | — | — | — | — | — | — | P | P* |

* Apenas operações técnicas explicitamente enumeradas e sem decisão editorial discricionária. A autorização técnica não pode ultrapassar gates de negócio.  
** A autorização editorial e a execução operacional da publicação são capacidades separadas. A direção editorial autoriza; o papel `PUBLISHER` executa.

Esta matriz é uma baseline para discussão e não deve ser convertida automaticamente em permissões de produção antes da validação dos fluxos e dos contratos de cada operação.

## 5. Separação de funções e conflitos

1. `PLATFORM_ADMIN` não recebe automaticamente permissões editoriais.
2. `SYSTEM_ORCHESTRATOR` não pode assumir identidade humana nem emitir aprovação editorial.
3. `INVESTIGATOR` não pode aprovar o próprio trabalho de fact-checking.
4. `FACT_CHECKER` não pode transformar um parecer factual em aprovação editorial.
5. `WRITER` não pode aprovar a versão que produziu.
6. `EDITOR` pode preparar e devolver conteúdo, mas não substitui a decisão final da direção editorial.
7. `PUBLISHER` só pode publicar a combinação previamente autorizada de artefacto, hash/versão e canal.
8. Alterações ao artefacto depois da aprovação invalidam a autorização associada à versão anterior.
9. A possibilidade de acumular papéis por uma mesma pessoa deve ser limitada por política; papéis incompatíveis não podem ser usados em autoaprovação.
10. Para conteúdo de risco elevado, a exigência de duas pessoas distintas deve ser configurável por política editorial e aplicada antes da produção.

## 6. Modelo de autorização

A autorização deve ser avaliada por uma função central com, no mínimo:

- sujeito interno autenticado;
- papel ativo atribuído pela aplicação;
- permissão solicitada;
- tipo e identificador do recurso;
- estado atual do workflow;
- versão do recurso/artefacto;
- contexto da decisão, quando aplicável.

A decisão deve ser `ALLOW` ou `DENY`, com negação como resultado padrão. A camada de domínio deve continuar a validar as regras de transição; RBAC não substitui `TRANSITION_POLICY`, gates, controlo de versão ou validações de evidência.

## 7. Persistência proposta

A implementação deve considerar, no mínimo, entidades equivalentes a:

- `users`: identidade interna e estado da conta;
- `external_identities`: associação única entre `issuer` + `subject` OIDC e utilizador interno;
- `roles`: catálogo controlado de papéis;
- `permissions`: catálogo de permissões estáveis;
- `role_permissions`: relação entre papéis e permissões;
- `user_roles`: atribuições de papéis, com estado, âmbito, validade e responsável pela concessão;
- `authorization_events`: auditoria append-only de concessões, revogações e alterações.

As chaves externas devem usar `issuer` + `subject`, nunca email como identificador primário. A associação de identidade deve impedir colisões entre emissores diferentes.

## 8. Limites desta fase

Esta especificação não implementa ainda:
- tabelas ou migrações RBAC;
- provisionamento ou gestão de utilizadores;
- associação automática de identidades OIDC;
- endpoints administrativos;
- proteção de endpoints editoriais;
- autorização de decisões humanas;
- publicação ou integração com canais externos.

Esses elementos dependem da aprovação desta matriz e serão implementados em entregas controladas posteriores da Fase D.

## 9. Critérios de aceitação D2

- A matriz de papéis e permissões é aprovada e versionada.
- A identidade OIDC é associada internamente por `issuer` + `subject`.
- Nenhuma permissão editorial é derivada diretamente do JWT.
- A política adota negação por omissão.
- Papéis administrativos e editoriais permanecem separados.
- Conflitos de autoaprovação são impedidos no servidor.
- Concessões e revogações são auditáveis.
- Testes cobrem acesso permitido, negado, papel revogado, utilizador inativo, identidade desconhecida e tentativa de escalada.
- A camada de domínio continua a validar estados, gates, versões e razões obrigatórias.

## 10. Decisões pendentes

Antes da implementação física do RBAC, devem ser validados:
1. Catálogo de papéis e matriz da secção 4.
2. Se os papéis serão globais ou poderão ter âmbito por equipa/projeto.
3. Política de acumulação de papéis e incompatibilidades.
4. Exigência de dupla aprovação para temas de risco elevado.
5. Quem pode conceder o papel `PLATFORM_ADMIN` e como será recuperado o acesso administrativo.

## 11. Histórico de alterações

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 1.0 | Proposta inicial do catálogo de papéis, matriz de permissões, separação de funções e modelo de autorização RBAC. |
