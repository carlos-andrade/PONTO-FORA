# INVENTÁRIO DOCUMENTAL — PONTO-FORA

**Identificador:** PF-GOV-INV-001  
**Versão:** 3.3  
**Data de criação:** 03/11/2026 (primeiro registo no GitHub)  
**Data da última atualização:** 03/11/2026  
**Estado:** Em manutenção  
**Responsável:** Governança do projeto PONTO-FORA  
**Âmbito:** Inventário dos ficheiros rastreados na branch main e dos artefactos de implementação em branches de trabalho, com respetiva conformidade documental.  
**SHA-256 (conteúdo normalizado):** d3191b5a25066643dbd7f4dea777d1b8ac3b98268e03fd000ae1c93530378e8d
**Commit de referência (base documental):** 016ca632fbb23e4f284fc67fba2cd46f733f883c

## Finalidade

Registar o estado de conformidade documental dos ficheiros existentes no repositório. Este inventário complementa a [NORMA-DOCUMENTAL.md](NORMA-DOCUMENTAL.md), que estabelece o cabeçalho Markdown padrão obrigatório e metadados equivalentes para formatos que não suportam Markdown.

## Inventário da branch main

| Ficheiro | Data de criação | Data da última atualização / controlo | Metadados | Estado e observação |
|---|---|---|---|---|
| `README.md` | 03/11/2026 (primeiro registo no GitHub) | 03/11/2026 | Cabeçalho Markdown padrão aplicado | Conforme; versão documental 1.3. |
| `PROMPT/PROMPT-MESTRE-PONTO-FORA.md` | 03/11/2026 (primeiro registo no GitHub) | 03/11/2026 | Cabeçalho Markdown padrão aplicado | Conforme; versão 1.3. |
| `AGENTES/AGENTE-INVESTIGADOR.md` | 03/11/2026 (primeiro registo no GitHub) | 03/11/2026 | Cabeçalho + contrato de integração + SHA-256 | Harmonizado; versão 1.4. |
| `AGENTES/AGENTE-FACT-CHECKER.md` | 03/11/2026 | 03/11/2026 | Cabeçalho + contrato de integração + SHA-256 | Harmonizado; versão 1.1. |
| `AGENTES/AGENTE-REDATOR.md` | 03/11/2026 | 03/11/2026 | Cabeçalho + contrato de integração + SHA-256 | Harmonizado; versão 1.1. |
| `AGENTES/AGENTE-EDITOR.md` | 03/11/2026 | 03/11/2026 | Cabeçalho + contrato de integração + SHA-256 | Harmonizado; revisão social incluída; versão 1.1. |
| `AGENTES/AGENTE-SOCIAL-MEDIA.md` | 03/11/2026 | 03/11/2026 | Cabeçalho + contrato de integração + SHA-256 | Harmonizado; versão 1.1. |
| `SISTEMA/ORQUESTRADOR-EDITORIAL.md` | 03/11/2026 | 03/11/2026 | Cabeçalho + contrato comum + mapeamentos + SHA-256 | Harmonizado; versão 1.1. |
| `SISTEMA/AUDITORIA-COERENCIA-AGENTES-01.md` | 03/11/2026 | 03/11/2026 | Cabeçalho padrão + SHA-256 + commit-base | Auditoria documental concluída; 12 pontos de harmonização; versão 1.0. |
| `SISTEMA/ARQUITETURA-DE-SOFTWARE.md` 03/11/2026 | 03/11/2026 | Cabeçalho padrão + SHA-256 + commit-base | Nova especificação técnica; versão 1.0; em desenvolvimento controlado. |
| `GOVERNANCA/NORMA-DOCUMENTAL.md` | 03/11/2026 (primeiro registo no GitHub) | 03/11/2026 | Cabeçalho padrão + SHA-256 + commit-base | Conforme; versão 1.5. |
| `GOVERNANCA/INVENTARIO-DOCUMENTAL.md` | 03/11/2026 (primeiro registo no GitHub) | 03/11/2026 | Cabeçalho padrão + SHA-256 + commit-base | Conforme; versão 3.2. |
| `LICENSE` | 03/11/2026 (primeiro registo no GitHub) | 03/11/2026 | Metadados externos no preâmbulo; texto MIT preservado | Conforme; não inserir cabeçalho Markdown no texto jurídico. |
| `.gitignore` | 03/11/2026 | 03/11/2026 | Comentários de metadados + SHA-256 + commit-base | Conforme; exclusões locais Python. |
| `pyproject.toml` | 03/11/2026 | 03/11/2026 | Comentários de metadados + SHA-256 + commit-base | Conforme; configuração de backend e ferramentas, versão 1.0 na main. |
| `src/ponto_fora_api/__init__.py` | 03/11/2026 | 03/11/2026 | Comentários de metadados + SHA-256 + commit-base | Conforme; pacote Python, versão 0.1.0 na main. |
| `src/ponto_fora_api/main.py` | 03/11/2026 | 03/11/2026 | Comentários de metadados + SHA-256 + commit-base | Conforme; API inicial e health check, versão 1.0 na main. |
| `tests/test_health.py` | 03/11/2026 | 03/11/2026 | Comentários de metadados + SHA-256 + commit-base | Conforme; testes do health check e OpenAPI. |
| `.github/workflows/ci.yml` | 03/11/2026 | 03/11/2026 | Comentários de metadados + SHA-256 + commit-base | Conforme; lint e testes da Fase A na main. |
| `docs/GUIA-DE-DESENVOLVIMENTO.md` | 03/11/2026 | 03/11/2026 | Cabeçalho Markdown + SHA-256 + commit-base | Conforme; guia de desenvolvimento, versão 1.0. |


## Integridade criptográfica e commits de publicação

Os hashes SHA-256 abaixo foram calculados segundo a [Norma Documental](NORMA-DOCUMENTAL.md), excluindo apenas os dois campos de integridade do cabeçalho e normalizando o texto em UTF-8/LF. Os commits de publicação são os commits Git devolvidos pelo GitHub após a atualização de cada ficheiro.

| Ficheiro | SHA-256 (conteúdo normalizado) | Commit efetivo de publicação |
|---|---|---|
| `README.md` | `57c066a7b515de4558224466154cd2cf887aec016c4c776d93f2e6687626e7eb` | `e4f4913d5e33c6fc20cdd422f0c2447e5e185f64` |
| `PROMPT/PROMPT-MESTRE-PONTO-FORA.md` | `77d6bd94dd7e9280144a6247b2a68b798d767eb9473f6bba9afaaab4da3f8ea7` | `8f5dd7d53644e65d62cb17ed59944e88a21a20d0` |
| `AGENTES/AGENTE-INVESTIGADOR.md` | `f1f8ec0de597cf2ef3348707b5bbe4d97a40a9fd113140614181b6ae664d7993` | `40f45381f7492b2ec0f7e86055b3574fae5ac8a7` |
| `AGENTES/AGENTE-FACT-CHECKER.md` | `5575dfa7a22d02277b6eae15f491dd6149745529c5cce10dce7ac0f4a5510054` | `1589c2299db96354e5ca1e2e7454743a4edc12a0` |
| `AGENTES/AGENTE-REDATOR.md` | `43d3501f3cccd8c82b99bea67bc2ea2c17f6382876dc545b7921728135b2f156` | `3a14818c90d12583fda7af61db970ee2e23dff2a` |
| `AGENTES/AGENTE-EDITOR.md` | `b31dd35444049bef8052edf19090b12644091869bd73c93ba6ec691c1d3ee95d` | `6bcc5ded7555abfdf0b14aabea51fb4b7f1731f7` |
| `AGENTES/AGENTE-SOCIAL-MEDIA.md` | `f561edc8678723e0589f8b7417b67e844780c54271d8474cd8b6a303d73c500e` | `5f655ad23fee2e204591102e466c5bc6e134f563` |
| `SISTEMA/AUDITORIA-COERENCIA-AGENTES-01.md` | `246cc737f6c6fe49fe53fe63355cd9749e4aa7db9d862b2a5664457ee607c510` | `5ba38d82ebad536b14cee3c94b1bffc049cbcf43` |
| `SISTEMA/ORQUESTRADOR-EDITORIAL.md` | `c447fd647c5d9668ea5cc7a0770adba7e8a11307add7d7bca8b339089ff0c542` | `774da1847e0448f0b4591f7a53c16dffa5eadfc6` |
| `AGENTES/AGENTE-INVESTIGADOR.md` | `e606cf790d8d267e4d507833dc320538ec84a731bb4e82a8ff7b7ecf165163c9` | `f33ccb9ce24162be972f35be2ccd8e2b3625f84b` |
| `AGENTES/AGENTE-FACT-CHECKER.md` | `ae9651527c6d6b5176f60ae8db32e2e53ee194af8c5dbd1b26b48b73aaa5dc90` | `83d6220286194dbd48168389059d77cbf8b4a187` |
| `AGENTES/AGENTE-REDATOR.md` | `6bccff646d528c404ce9ac4f29613b925dd8627270b916bf838cb4aa15347d89` | `03c25a840bc8658dd9c360e66fa260a1720c365c` |
| `AGENTES/AGENTE-EDITOR.md` | `6493739f680af14512e392bc4a5950d7ee7f2b219cab4c023da203885cb1b3a2` | `daeced58bfdc421d60a9095fe5da4c57b7b59210` |
| `AGENTES/AGENTE-SOCIAL-MEDIA.md` | `48eed4d565ff415ed1cb6a20fb1b05813b56875815a6ed00fb08827ba4f3400e` | `016ca632fbb23e4f284fc67fba2cd46f733f883c` |
| `SISTEMA/ORQUESTRADOR-EDITORIAL.md` | `f5029ff10730e6b533e4dd1034512bc4cba8becc626f52a8ecb24c80066ec37b` | `ed8d469648a9d59497fedb38a4d8c626cda9f0df` |
| `SISTEMA/ARQUITETURA-DE-SOFTWARE.md` | `1ae725ea77e73a4039f14b8adcf181d11b2771b7b6f114dc689ed1354c44eb17` | `8355e0162f2ee53abfba253cb9041b88d419ed1b` |
| `GOVERNANCA/NORMA-DOCUMENTAL.md` | `f731f940fef6e542d103aa0f83765c6e7749be62a510112032b4433d835e4e44` | `243a1bea864253e9b870931e6a5b1841c05816f1` |
| `LICENSE` | `a3b6bf7bfaa2b3b9cb6f8edafb531eb9ca07b84f7b595200198116538acfceaa` | `fc7ac004e8335ee20641c75b1263aadc8f2e5e40` |
| `GOVERNANCA/INVENTARIO-DOCUMENTAL.md` | Ver cabeçalho (não duplicar o próprio hash) | Autorreferência: consultar o histórico Git; commit atual confirmado no relatório de execução. |

O SHA-256 do próprio Inventário consta no seu cabeçalho. O commit efetivo que publica o próprio Inventário não pode ser inscrito dentro do mesmo ficheiro sem autorreferência circular; consulte o histórico Git do repositório. O campo de commit no cabeçalho identifica o commit-base documental.


## Artefactos de implementação — Fase A (integrados na branch `main`)

A Fase A foi integrada na branch `main` através do Pull Request #1, com merge commit `eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4`. Os commits indicados são os commits efetivos de criação dos ficheiros na branch de trabalho integrada.

| Ficheiro | Identificador | SHA-256 (conteúdo normalizado) | Commit efetivo de publicação | Estado |
|---|---|---|---|---|
| `.gitignore` | PF-COD-GITIGNORE-001 | `ea12f593093ecaea5d62d2ba237c2b128247e1f09a0931e5a16c618510c5f979` | `264fb26c2696d53eb7a9102943d2690e842d2272` | Criado |
| `pyproject.toml` | PF-COD-CONFIG-001 | `63e6639d2fe16986e3fe0f5e03502f33d52c0ee135fc41370d3d54ecc886b348` | `add73736f125a8cf74d90c0b2e716bac95da3ce8` | Criado |
| `src/ponto_fora_api/__init__.py` | PF-COD-PKG-001 | `40faa39f5e5853f5ea4afb654fb54b06c24cac44773dd9d4d062afbe9d336df4` | `de82699b2857312768503bad870f2812b9f6a653` | Criado |
| `src/ponto_fora_api/main.py` | PF-COD-API-001 | `2deff6ae9348eec64aba63e80297b38cc6f4755e012a15710c8e22fa38ee60b4` | `bf51fd2e932f090aab58cf475a65f0dfbc9e1157` | Criado |
| `tests/test_health.py` | PF-COD-TEST-001 | `dfa825008d3e5aabfee18e91892f5d356a5ac5d19644c74d3d81708c72ce6b21` | `81bf9fceb887e779d5a5032ff9603ecc448933d1` | Criado |
| `.github/workflows/ci.yml` | PF-CI-PYTHON-001 | `bee61d07d376d8d41b70d0e9a283665093e0c7762e0fd6956e0ef3b935389f86` | `29425bc3166b08f27a1248f18ce72ec40b129d0d` | Criado; CI validada |
| `docs/GUIA-DE-DESENVOLVIMENTO.md` | PF-DOC-DEV-001 | `482414b762d642d50266c2a24c99cb0e99eedbff58d541dc1b7f450850c05f2a` | `3d6e12a9f086c2cf5108b19e77d15a66aa507423` | Criado |

## Artefactos de implementação — Fase B (integrados na branch `main`)

A Fase B foi integrada na branch `main` através do PR #2, com merge commit `c5d4cf29b6d2ab23b99439852235868c3b422195`. Os commits originais de cada ficheiro permanecem no histórico Git e os artefactos abaixo fazem parte da árvore integrada. O CI da versão submetida foi concluído com sucesso: Ruff aprovado, migração PostgreSQL 16 aplicada e 13 testes aprovados.

| Ficheiro | Identificador | SHA-256 (conteúdo normalizado) | Commit efetivo de publicação | Estado |
|---|---|---|---|---|
| `pyproject.toml` | PF-COD-CONFIG-001 | `5ff8c7c6038509672a4490222b63c94e89f46fe3d2ec7ec4801073046b0078f0` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Integrado na main; versão 0.2.0; dependências SQLAlchemy, Alembic e Psycopg. |
| `.env.example` | PF-CFG-ENV-001 | `be55eddeee8db66eb9c7d32d461e6f694b8bc82f2e74e950b9f2839960b02fd8` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado; sem credenciais reais. |
| `alembic.ini` | PF-CFG-ALEMBIC-001 | `f4da5c02c8aa04c5c98a6068e36edca071a8259824b6a62ff7bb299801601d98` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado; configuração de migrações. |
| `migrations/env.py` | PF-COD-MIG-ENV-001 | `2725612c07b42febb50e885f2d348c985f87fdb89cd8e14e783d2b6981beb0c9` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado. |
| `migrations/script.py.mako` | PF-CFG-MIG-TEMPLATE-001 | `d3aeb93c4508fbea0bd6e6c7f4d3f4852ccc09f7b8b826dfbed4eda8c70bb9b7` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado. |
| `migrations/versions/0001_initial.py` | PF-MIG-0001 | `d8d0d97fd1396ab2304391747229f2cf422c512dae74f10a5ccf22461b2aaa32` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado; migração inicial. |
| `src/ponto_fora_api/__init__.py` | PF-COD-PKG-001 | `1b07b2af43caf591eceb3f62bbdb551fdcf4573fe47d89e700940cf1f2be2307` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Atualizado para versão 0.2.0. |
| `src/ponto_fora_api/main.py` | PF-COD-API-001 | `2e6078f0c8db94c1fe129b4c4fcec6fe0dddaf2d93bda45d7732f8bf17453bee` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Health check; rotas editoriais não montadas sem autenticação. |
| `src/ponto_fora_api/db.py` | PF-COD-DB-001 | `315e73a3c2bb467f069d734b7ef83529bdf8b3f5a44de01b0dbbb5df103a73e9` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado; engine e sessões SQLAlchemy. |
| `src/ponto_fora_api/models.py` | PF-COD-MODELS-001 | `7c1961c338ac29d535e56d0cb206b04bf68d6a71b38f1f32b3193aefbb252d63` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Integrado na main; cinco tabelas do núcleo. |
| `src/ponto_fora_api/domain.py` | PF-COD-DOMAIN-001 | `c69af0cc1225f48935ade424acb458d866bbd30abcf595f2e20ad960d46e984c` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado; estados e política limitada de transições. |
| `src/ponto_fora_api/services/__init__.py` | PF-COD-SVC-PKG-001 | `880334064a64455de4fac5352b5f596be904c685cd876d6b849c12a444dca9ed` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado. |
| `src/ponto_fora_api/services/assignments.py` | PF-COD-ASSIGNMENTS-001 | `4d16d85952bd3e8e6e2491b0de85490fc0b281f7b85980f584bc5be6c9d936fc` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado; criação idempotente e transições auditadas. |
| `src/ponto_fora_api/api/__init__.py` | PF-COD-API-PKG-001 | `a073dc24fed665553c563c86b4d7e44dff0e2fbc439f60420bbd2abc4a1a65e0` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado. |
| `src/ponto_fora_api/api/assignments.py` | PF-COD-API-ASSIGN-001 | `a477491ddd832a0a98a1957432241379165f34d4437ede4f8e61752e35ec5ed1` | `633eb45366f105b939d31149ee776979602d9bbe` | Rotas de consulta preparadas, ainda não montadas. |
| `tests/test_assignments.py` | PF-TEST-ASSIGNMENTS-001 | `a3e8e480aacb7feda000b30ee7268ab420599044e4a837d0efe923f93b621547` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Criado; testes de domínio e persistência. |
| `docs/FASE-B-NUCLEO-EDITORIAL.md` | PF-DOC-FASE-B-001 | `961dfc52323543d25b096270fc4b5ada87dfaabf8859077f1f109f68d1129463` | `633eb45366f105b939d31149ee776979602d9bbe` | Criado; escopo e limites da fase. |
| `.github/workflows/ci.yml` | PF-CI-PYTHON-001 | `9d8e402fd0751a90c30fd7e1e2bce4d9d6044fcdb3fc56557ca87cb782349a4e` | `41851dee6932347e2e55c6598ceb8658c9a7cac0` | Atualizado; PostgreSQL 16, Alembic, Ruff e Pytest. |


## Artefactos de implementação — Fase C (branch `phase-c/evidencias-contratos`)

A Fase C está em implementação controlada numa branch derivada do merge commit da Fase B. Os ficheiros abaixo foram criados ou atualizados na branch; ainda não estão integrados na `main`. A CI do PR #3 foi concluída com sucesso: migração PostgreSQL 16 aplicada até 0002_evidence_domain e 18 testes aprovados.

| Ficheiro | Identificador | SHA-256 (conteúdo normalizado) | Commit efetivo de publicação | Estado |
|---|---|---|---|---|
| `docs/FASE-C-EVIDENCIAS-E-CONTRATOS.md` | PF-DOC-FASE-C-001 | `bb23dc33368d0175022792e17a6420b55de0f2aa3b6c66d1fee05a7bf66b6600` | `f5e137b5f7ff816e826fd2cc0d4ca4e4f81868d1` | Especificação criada; em revisão. |
| `src/ponto_fora_api/models.py` | PF-COD-MODELS-001 | `77cc91bbb71b37e21948df294404644f2a7441f2f57d23398db81a4df0394fd9` | `3fb74baee95a89b983aa9dd5486488eed5849400` | Modelos factuais adicionados; CI aprovada. |
| `migrations/versions/0002_evidence_domain.py` | PF-MIG-0002 | `6a12e195c29c3e0e42f6d87c5b9dd0122cbead9133a2316397906828cc2aead7` | `2ccc9b288fc174242562ca522df15e1aeff32539` | Migração criada; PostgreSQL 16 aplicado com sucesso. |
| `src/ponto_fora_api/schemas/evidence.py` | PF-COD-SCHEMAS-EVIDENCE-001 | `622bdb45ce7c7d46a076e89f2727788a5deb30e5a0ab578a098909a6e1a077bb` | `33b4091aba3b2c1db13871ea2a9ca3a911d86a72` | Contratos Pydantic criados; CI aprovada. |
| `src/ponto_fora_api/services/evidence.py` | PF-COD-SVC-EVIDENCE-001 | `c824b955602edca2696fb2b9dd89ebcd76627dd427793db14ccb332b33ee79d9` | `9d97ad8b3db7c0814d1e7bac61cd6c1ccc61fb36` | Serviços de persistência criados; CI aprovada. |
| `tests/test_evidence.py` | PF-TEST-EVIDENCE-001 | `d2a91defd045b345a2033625bdf4c5d8132d68ce3a19aba848fbde6febe3ccd3` | `d01457e14fab9a7b4a90b31ce4e08c6c5bba6f80` | 18 testes aprovados em CI. |
| `.github/workflows/ci.yml` | PF-CI-PYTHON-001 | `312833e5e03139e5703bdf3733c23619bceb91ea51ef12cd1d9b7333b8057643` | `da4886d96a654d5441acd087e113650b90c5fb92` | CI configurada para branches phase-c/**. |
| `pyproject.toml` | PF-COD-CONFIG-001 | `1f5e61d9a402b1e0b779e5b5b807181c1f7f21f110ecb5326d30ac403f4be88c` | `4b7f26bb2bd7c4a648604e3d0a95aab7aa2fb07e` | Lint da Fase C; E501 temporariamente ignorado; revisão de estilo pendente. |

## Regra de manutenção

Sempre que um ficheiro documental for criado ou alterado:
1. Aplicar o cabeçalho Markdown padrão aos ficheiros `.md`.
2. Inserir metadados equivalentes nos demais formatos, sem invalidar a sintaxe ou alterar conteúdo normativo de terceiros.
3. Atualizar a data da última atualização e a versão, quando aplicável.
4. Atualizar este inventário quando o estado, a versão, a data ou a conformidade do ficheiro mudar.
5. Registar a criação com base em evidência; o primeiro commit prova a presença no GitHub, não necessariamente a primeira redação fora do repositório.
6. Executar uma auditoria à árvore completa da branch, incluindo ficheiros não documentais, para identificar novos formatos que exijam metadados compatíveis.

## Histórico de alterações

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 1.0 | Inventário inicial dos ficheiros existentes e respetivo estado documental. |
| 03/11/2026 | 1.1 | Auditoria integral da branch main; registo específico da LICENSE preservada sem alteração. |
| 03/11/2026 | 1.2 | Datas de criação atualizadas com base no primeiro commit de cada ficheiro; atualização dos metadados e histórico. |
| 03/11/2026 | 1.3 | Inclusão do próprio inventário na listagem de documentos auditados. |
| 03/11/2026 | 1.4 | Inclusão do cabeçalho Markdown padrão obrigatório no inventário de conformidade. |
| 03/11/2026 | 1.5 | Auditoria dos seis ficheiros da branch main e aplicação dos cabeçalhos e metadados documentais correspondentes. |
| 03/11/2026 | 1.6 | Inclusão do Agente Fact-checker no inventário e registo da sua conformidade documental. |
| 03/11/2026 | 1.7 | Inclusão do Agente Redator no inventário e registo da sua conformidade documental. |
| 03/11/2026 | 1.8 | Inclusão do Agente Editor no inventário e registo da sua conformidade documental. |
| 03/11/2026 | 1.9 | Inclusão do Agente Social Media e correção da versão documental indicada na linha do próprio inventário. |
| 03/11/2026 | 2.1 | Inclusão dos hashes SHA-256 normalizados e dos commits efetivos de publicação; atualização da norma de integridade. |
| 03/11/2026 | 2.2 | Atualização da referência à Norma Documental 1.5 e do respetivo hash SHA-256/commit de publicação. |
| 03/11/2026 | 2.0 | Inclusão do Orquestrador Editorial no inventário e atualização da versão documental. |
| 03/11/2026 | 2.3 | Inclusão do próprio Inventário no registo de integridade, com tratamento explícito da autorreferência Git/SHA-256. |
| 03/11/2026 | 2.4 | Registo da arquitetura de software, correção dos metadados do Fact-checker e atualização da integridade documental. |
| 03/11/2026 | 2.5 | Registo dos sete artefactos técnicos e documentais da Fase A na branch de trabalho, com hashes e commits confirmados. |
| 03/11/2026 | 2.6 | Atualização do estado da Fase A após integração na main e registo dos 18 artefactos da Fase B com hashes SHA-256 e commit de publicação. |
| 03/11/2026 | 2.7 | Correção da assinatura das dependências FastAPI e atualização do hash/commit da rota de consulta no inventário. |
| 03/11/2026 | 2.8 | Aplicação dos hashes SHA-256 em falta na rota de consulta e no documento da Fase B, com atualização dos commits de publicação. |
| 03/11/2026 | 2.9 | Confirmação da integração da Fase B na main e inventário inicial dos artefactos da Fase C na branch de implementação. |
| 03/11/2026 | 3.0 | Atualização do commit efetivo de publicação do serviço factual e revisão do inventário da Fase C. |
| 03/11/2026 | 3.1 | Atualização dos hashes e commits dos ficheiros de modelos, serviços, testes, configuração e CI após correções de lint.
| 03/11/2026 | 3.2 | Registo da CI aprovada para a Fase C: migração PostgreSQL 16 aplicada e 18 testes aprovados. |
| 03/11/2026 | 3.3 | Registo da auditoria de coerência, Orquestrador Editorial V1.1 e harmonização dos cinco contratos de agentes, com hashes e commits confirmados. | |
