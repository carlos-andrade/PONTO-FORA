# NORMA DOCUMENTAL — PONTO-FORA

**Identificador:** PF-GOV-DOC-001  
**Versão:** 1.4  
**Data de criação:** 03/11/2026 (primeiro registo no GitHub)  
**Data da última atualização:** 03/11/2026  
**Estado:** Obrigatória  
**Responsável:** Governança do projeto PONTO-FORA  
**Âmbito:** Todos os documentos e ficheiros documentais do projeto PONTO-FORA  
**SHA-256 (conteúdo normalizado):** d7ce746c3275258dd0e03df750fe13ab795a4f3103d22d47420da53de87631c3
**Commit de referência (base documental):** c34d0fcdd03e8235bafc540911a175ea128e994c

## 1. PRINCÍPIO FUNDAMENTAL

> **UM DOCUMENTO SEM DATA NÃO É DOCUMENTO.**

Nenhum documento do PONTO-FORA deve ser considerado documentalmente completo se não apresentar datas de criação e de atualização no próprio conteúdo ou em metadados documentais legíveis e associados.

## 2. CAMPOS OBRIGATÓRIOS

Todo documento deve apresentar:
- **Data de criação:** data em que a primeira versão foi efetivamente criada.
- **Data da última atualização:** data da alteração mais recente do conteúdo.
- **Versão:** quando o documento possuir controlo de versões.

Formato obrigatório: **DD/MM/AAAA**.

## 3. CABEÇALHO MARKDOWN PADRÃO OBRIGATÓRIO

Todo ficheiro documental em Markdown (`.md`) criado, alterado ou salvo no repositório deve começar com um cabeçalho Markdown padronizado. O cabeçalho deve vir antes do conteúdo principal e conter, no mínimo, os seguintes campos:

```markdown
# TÍTULO DO DOCUMENTO

**Identificador:** PF-[ÁREA]-[ID]  
**Versão:** 1.0  
**Data de criação:** DD/MM/AAAA  
**Data da última atualização:** DD/MM/AAAA  
**Estado:** Rascunho | Em revisão | Aprovado | Obsoleto  
**Responsável:** [papel, agente ou equipa responsável]  
**Âmbito:** [finalidade e abrangência do documento]
```

### 3.1 Regras de preenchimento

1. O título deve ser claro, específico e corresponder ao conteúdo.
2. O identificador deve ser estável e único quando o documento estiver sujeito a controlo formal. Não inventar identificadores retroativamente; documentos simples podem omitir o campo apenas quando a governança da área assim determinar.
3. A versão deve seguir o padrão de versionamento documental definido pelo projeto.
4. As datas devem seguir **DD/MM/AAAA** e nunca podem ser inventadas.
5. O estado deve refletir a situação real do documento.
6. O responsável deve indicar uma função, agente ou equipa; não é necessário expor dados pessoais.
7. O âmbito deve indicar para que serve o documento e a que processos se aplica.
8. O cabeçalho deve ser atualizado sempre que os metadados ou o conteúdo correspondente mudarem.
9. O cabeçalho não substitui o histórico de alterações quando este for exigido.

## 4. FICHEIROS QUE NÃO SÃO MARKDOWN

A obrigatoriedade de cabeçalho Markdown aplica-se diretamente a ficheiros Markdown. Para outros formatos, aplicar metadados equivalentes no mecanismo nativo do formato ou num ficheiro de controlo associado, com referência inequívoca ao artefacto e à versão.

Exemplos:
- **Código-fonte:** cabeçalho de comentário adequado à linguagem, quando compatível com as convenções e ferramentas do projeto.
- **JSON/YAML/XML:** propriedades ou comentários de metadados apenas quando válidos para o formato; nunca introduzir comentários inválidos.
- **CSV:** ficheiro de metadados associado, sem inserir linhas que contaminem os dados.
- **PDF, DOCX, XLSX, PPTX e imagens:** propriedades/metadados nativos ou registo documental associado.
- **Binários e ficheiros gerados:** registo documental externo associado e rastreável.

Não inserir Markdown num ficheiro cujo formato não o suporte. Não modificar arbitrariamente formatos padronizados, licenças legais, ficheiros de terceiros ou artefactos gerados automaticamente. Preservar a integridade funcional e jurídica.

## 5. DOCUMENTOS PREEXISTENTES

Não inventar, deduzir ou atribuir retroativamente uma data de criação sem evidência. Quando não for possível confirmar a data original, utilizar exatamente:

**Data de criação: Não confirmada — documento preexistente.**

A data da revisão ou atualização atual deve ser registada normalmente. O primeiro registo no GitHub pode ser usado como evidência de existência no repositório, mas não prova necessariamente a data original de redação fora dele.

## 6. REGISTO DE ATUALIZAÇÕES

Sempre que um documento for alterado:
1. Atualizar imediatamente o campo “Data da última atualização”.
2. Acrescentar uma entrada no histórico de alterações quando a mudança for material, estrutural, editorial ou técnica.
3. Preservar as entradas anteriores; nunca apagar o histórico para fazer parecer que o documento foi criado na data mais recente.
4. Atualizar a versão quando existir controlo formal de versões.

Modelo:

| Data | Versão | Alteração |
|---|---|---|
| DD/MM/AAAA | X.Y | Descrição objetiva da alteração |

## 7. ÂMBITO DE APLICAÇÃO

Esta norma aplica-se a README, prompts, instruções de agentes, políticas editoriais, relatórios, dossiês de investigação, verificações factuais, artigos, manuais, especificações, procedimentos, atas, documentação de arquitetura, planos, ficheiros de configuração documentais e demais artefactos que registem decisões ou conhecimento do projeto.

## 8. RESPONSABILIDADES DOS AGENTES DE IA E CONTRIBUIDORES

Todos os agentes, automações e contribuidores do PONTO-FORA devem:
- Verificar o cabeçalho e os metadados antes de salvar ou entregar um documento.
- Inserir o cabeçalho padrão ao criar ficheiros Markdown.
- Preservar o cabeçalho e atualizar os campos pertinentes em revisões.
- Aplicar metadados equivalentes a ficheiros não Markdown.
- Não inventar datas históricas, versões, estados ou responsáveis.
- Sinalizar ficheiros sem metadados como não conformes.
- Atualizar o inventário documental quando aplicável.

## 9. CRITÉRIO DE CONFORMIDADE

Um ficheiro Markdown só está conforme quando começa com o cabeçalho padrão, apresenta os campos obrigatórios aplicáveis, contém datas válidas (ou declaração de data de criação não confirmada para documento preexistente) e mantém histórico quando exigido.

Um ficheiro de outro formato só está conforme quando possui metadados equivalentes no próprio formato ou em registo associado rastreável.

A data do commit, do upload ou da modificação no sistema de ficheiros não substitui os campos documentais.


## 10. INTEGRIDADE CRIPTOGRÁFICA E RASTREABILIDADE GIT

Todo documento e ficheiro mantido pelo projeto deve apresentar, no seu cabeçalho ou bloco de metadados associado:

- **SHA-256 (conteúdo normalizado):** hash SHA-256 hexadecimal de 64 caracteres, calculado segundo esta secção.
- **Commit de referência (base documental):** hash completo do commit Git que representa a versão-base imediatamente anterior à inclusão/atualização dos metadados de integridade.

### 10.1 Limitação de autorreferência do commit

O hash de um commit Git depende da árvore de ficheiros, incluindo o próprio conteúdo do documento. Portanto, não é tecnicamente possível gravar dentro de um ficheiro o hash do commit que contém exatamente essa mesma versão: a inclusão do hash altera o ficheiro e invalida o commit calculado.

Por esse motivo, o campo no cabeçalho identifica explicitamente o **commit de referência (base documental)**, isto é, o commit que contém a versão do documento antes da atualização dos metadados de integridade. Não deve ser apresentado como o commit que publicou a versão atual.

O **commit efetivo de publicação** de cada ficheiro deve ser registado no Inventário Documental, após confirmação do GitHub. Para o próprio Inventário, a impossibilidade de autorreferência deve ser declarada e o commit efetivo consultado no histórico Git do repositório.

### 10.2 Cálculo do SHA-256 normalizado

Para eliminar a autorreferência do próprio hash, o SHA-256 deve ser calculado sobre o conteúdo integral do ficheiro, removendo exclusivamente as linhas dos campos:

- `**SHA-256 (conteúdo normalizado):**`
- `**Commit de referência (base documental):**`

Procedimento obrigatório:

1. Ler o conteúdo em UTF-8, sem BOM.
2. Converter terminações de linha para LF (\\n).
3. Remover integralmente as linhas dos dois campos de integridade acima, sem remover quaisquer outros metadados ou conteúdo.
4. Preservar a ordem, os espaços, a pontuação e todo o restante conteúdo.
5. Preservar uma única quebra de linha final, se existente no conteúdo normalizado.
6. Calcular SHA-256 dos bytes UTF-8 resultantes.
7. Registar o resultado em hexadecimal minúsculo, com 64 caracteres.

O cálculo deve ser reproduzível. Não utilizar o SHA-1 do objeto blob Git como substituto do SHA-256.

### 10.3 Aplicação por formato

- **Markdown e texto:** os dois campos devem constar no cabeçalho documental.
- **LICENSE e textos legais:** preservar integralmente o texto jurídico. Inserir os campos apenas no bloco de metadados preexistente ou num registo documental associado, nunca no corpo da licença.
- **JSON, YAML, TOML, código e configurações:** utilizar comentários ou metadados válidos para o formato, sem invalidar a sintaxe ou o funcionamento.
- **PDF, DOCX, XLSX, imagens e outros binários:** inserir metadados internos quando suportados; caso contrário, utilizar um registo associado no Inventário Documental.
- **Ficheiros gerados:** incluir os metadados no artefacto ou registo associado antes da distribuição.

### 10.4 Atualização e auditoria

1. Recalcular o SHA-256 sempre que o conteúdo do ficheiro mudar.
2. Atualizar o commit de referência quando uma nova versão-base for estabelecida.
3. Registar no Inventário o SHA-256 e o commit efetivo de publicação confirmado pelo GitHub.
4. Não declarar um hash ou commit como verificado sem o calcular ou consultar.
5. Após cada atualização, reler o ficheiro, recalcular o SHA-256 normalizado e comparar com o valor declarado.
6. Se o conteúdo divergir do hash registado, marcar o ficheiro como **INTEGRIDADE NÃO VALIDADA** até à reconciliação.
7. Não alterar silenciosamente ficheiros binários, licenças ou formatos especiais para inserir metadados; utilizar registo associado quando necessário.

## 11. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 1.0 | Criação e entrada em vigor da norma documental obrigatória. |
| 03/11/2026 | 1.1 | Registo da data de criação com base no primeiro commit do GitHub e reforço da rastreabilidade documental. |
| 03/11/2026 | 1.2 | Inclusão do cabeçalho Markdown padrão obrigatório e definição de metadados equivalentes para ficheiros em outros formatos. |
| 03/11/2026 | 1.4 | Inclusão de regra de integridade criptográfica SHA-256, referência de commit Git, normalização de conteúdo, rastreabilidade e auditoria. |
| 03/11/2026 | 1.3 | Aplicação do cabeçalho padrão aos documentos Markdown existentes e atualização do inventário de conformidade. |
