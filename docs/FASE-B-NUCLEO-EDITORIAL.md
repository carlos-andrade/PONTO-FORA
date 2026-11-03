# FASE B — NÚCLEO EDITORIAL

**Identificador:** PF-DOC-FASE-B-001  
**Versão:** 1.0  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Em desenvolvimento controlado  
**Responsável:** Engenharia de Software e Governança Editorial  
**Âmbito:** Registar o escopo implementado da Fase B, as regras de domínio, persistência, auditoria e limites operacionais.  
**SHA-256 (conteúdo normalizado):** PENDING  
**Commit de referência (base documental):** eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

## 1. Objetivo

Implementar a base transacional do PONTO-FORA para pautas, estados editoriais, eventos de auditoria, idempotência, tarefas e versões de artefactos.

A implementação segue a especificação de arquitetura e a máquina de estados do Orquestrador Editorial.

## 2. Componentes incluídos

- Modelos SQLAlchemy 2.x para pautas, eventos, tarefas, idempotência e versões de artefactos.
- Migração Alembic inicial.
- Suporte a PostgreSQL com driver Psycopg 3.
- SQLite permitido apenas para desenvolvimento e testes.
- Criação idempotente de pautas no serviço de domínio.
- Transição de estado com controlo otimista por `row_version`.
- Eventos de auditoria criados na mesma transação da alteração de estado.
- Política de transições inicial, deliberadamente limitada.
- Módulo de consulta preparado, mas não exposto pela aplicação até existir autenticação.

## 3. Estados e transições

A enumeração técnica contém os 28 estados definidos no Orquestrador Editorial. Nesta fase, apenas estão habilitadas estas transições:

| Origem | Destino | Autoridade |
|---|---|---|
| RECEBIDA | EM_TRIAGEM | Orquestrador técnico |
| EM_TRIAGEM | AGUARDANDO_INVESTIGACAO | Direção Editorial humana |
| EM_TRIAGEM | REJEITADA | Direção Editorial humana, com motivo |
| EM_TRIAGEM | BLOQUEADA | Direção Editorial humana, com motivo |

As restantes transições permanecem bloqueadas até que os gates, contratos de evidência, pareceres e aprovações das etapas correspondentes estejam implementados e testados.

A identidade do ator é um objeto interno do serviço. Não existe endpoint público de escrita nem cabeçalho HTTP que permita ao cliente declarar o próprio papel. A autenticação e o RBAC serão implementados na fase própria antes da exposição de comandos de escrita na API.

## 4. Persistência

Tabelas criadas pela migração inicial:
- `assignments`
- `audit_events`
- `workflow_tasks`
- `idempotency_records`
- `artifact_versions`

Os eventos de auditoria não podem ser atualizados ou apagados por operações normais da aplicação. A migração instala um trigger PostgreSQL para rejeitar `UPDATE` e `DELETE` na tabela `audit_events`. Em SQLite, os testes validam o comportamento do serviço; o trigger de produção é específico de PostgreSQL.

## 5. Idempotência e concorrência

A criação de pauta usa chave de idempotência com hash do payload canónico. Repetir a mesma chave e o mesmo payload devolve a pauta existente. Reutilizar a chave com payload diferente gera conflito de domínio.

As transições exigem `command_id` e `expected_row_version`. A repetição do mesmo comando devolve o recurso resultante; uma chave reutilizada com conteúdo diferente gera conflito. Uma versão desatualizada é rejeitada, sem sobrescrever o estado atual.

## 6. API nesta fase

A aplicação expõe apenas `GET /health`. As rotas de consulta editorial estão preparadas em módulo separado, mas não são montadas até existir autenticação e autorização. Isto evita expor pautas e histórico de auditoria sem controlo de acesso.

## 7. Configuração local

Copiar `.env.example` para `.env` e ajustar `DATABASE_URL`.

SQLite local:
```text
DATABASE_URL=sqlite:///./ponto_fora.db
```

PostgreSQL:
```text
DATABASE_URL=postgresql+psycopg://utilizador:senha@localhost:5432/ponto_fora
```

Aplicar migrações:
```bash
alembic upgrade head
```

Executar:
```bash
uvicorn ponto_fora_api.main:app --reload
```

Validar:
```bash
ruff check .
pytest
```

## 8. Limites e trabalho posterior

Ainda não estão implementados:
- Autenticação, gestão de utilizadores ou RBAC real.
- Endpoints de escrita e consultas editoriais autenticadas.
- Outbox transacional e dispatch de filas.
- Fontes, afirmações e evidências.
- Execução de agentes.
- Aprovações humanas por versão.
- Dashboard, publicação, armazenamento de objetos ou deployment.

A tabela `workflow_tasks` é apenas a estrutura persistente inicial; não existe worker ou fila operacional nesta fase.

## 9. Critérios de aceitação desta entrega

- Migração Alembic cria o esquema previsto.
- Criação idempotente e conflito de chave são testados.
- Transições permitidas e proibidas são testadas.
- Concorrência otimista é testada.
- Cada transição gera evento de auditoria.
- Repetição de comando não duplica eventos.
- CI executa Ruff e Pytest.
