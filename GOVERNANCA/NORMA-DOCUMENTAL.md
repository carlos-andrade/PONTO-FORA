# NORMA DOCUMENTAL — PONTO-FORA

**Identificador:** PF-GOV-DOC-001  
**Versão:** 1.1  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Obrigatória  
**Âmbito:** Todos os documentos e ficheiros documentais do projeto PONTO-FORA

## 1. PRINCÍPIO FUNDAMENTAL

> **UM DOCUMENTO SEM DATA NÃO É DOCUMENTO.**

Nenhum documento do PONTO-FORA deve ser considerado documentalmente completo se não apresentar datas de criação e de atualização no próprio conteúdo ou em metadados documentais legíveis e associados.

## 2. CAMPOS OBRIGATÓRIOS

Todo documento deve apresentar:

- **Data de criação:** data em que a primeira versão foi efetivamente criada.
- **Data da última atualização:** data da alteração mais recente do conteúdo.
- **Versão:** quando o documento possuir controlo de versões.

Formato obrigatório: **DD/MM/AAAA**.

## 3. DOCUMENTOS PREEXISTENTES

Não inventar, deduzir ou atribuir retroativamente uma data de criação sem evidência. Quando não for possível confirmar a data original, utilizar exatamente:

**Data de criação: Não confirmada — documento preexistente.**

A data da revisão ou atualização atual deve ser registada normalmente.

## 4. REGISTO DE ATUALIZAÇÕES

Sempre que um documento for alterado:

1. Atualizar imediatamente o campo “Data da última atualização”.
2. Acrescentar uma entrada no histórico de alterações quando a mudança for material, estrutural, editorial ou técnica.
3. Preservar as entradas anteriores; nunca apagar o histórico para fazer parecer que o documento foi criado na data mais recente.
4. Atualizar a versão quando existir controlo formal de versões.

Modelo de histórico:

| Data | Versão | Alteração |
|---|---|---|
| DD/MM/AAAA | X.Y | Descrição objetiva da alteração |

## 5. ÂMBITO DE APLICAÇÃO

Esta norma aplica-se a README, prompts, instruções de agentes, políticas editoriais, relatórios, dossiês de investigação, verificações factuais, artigos, manuais, especificações, procedimentos, atas, documentação de arquitetura, planos, ficheiros de configuração documentais e demais artefactos que registem decisões ou conhecimento do projeto.

Em ficheiros binários ou formatos sem campo visível adequado, a data deve ser registada nos metadados do próprio ficheiro ou num registo documental associado, com referência inequívoca ao ficheiro e à sua versão.

Não alterar arbitrariamente formatos padronizados de terceiros, licenças legais ou ficheiros gerados automaticamente. Nesses casos, utilizar metadados externos associados ou documentação de controlo, preservando o conteúdo normativo original.

## 6. RESPONSABILIDADES DOS AGENTES DE IA

Todos os agentes do PONTO-FORA devem:

- Verificar a presença das datas antes de entregar um documento.
- Inserir as datas obrigatórias ao criar documentos.
- Atualizar a data de atualização em qualquer revisão.
- Não inventar datas históricas.
- Sinalizar documentos sem data como não conformes.
- Preservar o histórico de alterações.

## 7. CRITÉRIO DE CONFORMIDADE

Um documento só está conforme quando contém a data de criação (ou a declaração de data não confirmada para documentos preexistentes), a data da última atualização e, quando aplicável, versão e histórico de alterações.

A data do commit, do upload ou da modificação no sistema de ficheiros não substitui os campos documentais.

## 8. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 1.0 | Criação e entrada em vigor da norma documental obrigatória. |
| 03/11/2026 | 1.1 | Registo da data de criação com base no primeiro commit do GitHub e reforço da rastreabilidade documental. |
