# BOOTSTRAP SEGURO DO PRIMEIRO ADMINISTRADOR

**Identificador:** PF-SYS-BOOTSTRAP-001  
**Versão:** 1.0  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Em revisão  
**Responsável:** Engenharia de Software  
**Âmbito:** Procedimento local e transacional para criar a primeira identidade interna com o papel técnico PLATFORM_ADMIN.  
**SHA-256 (conteúdo normalizado):** 21c5f2d085481f75f34c7a3fc89804bb00193cd2e8a16c3cc9a90311b4e0da69  
**Commit de referência (base documental):** 6ed842788df04670d724559c10103975f60ae9b4

## Objetivo e fronteira de confiança

O bootstrap é um procedimento operacional local. Não existe endpoint HTTP para autoelevação. A execução exige acesso ao ambiente que contém a base de dados e uma confirmação explícita na linha de comando.

O email é apenas um atributo informativo. A identidade é vinculada exclusivamente pelo par OIDC `issuer` + `subject`.

## Pré-requisitos

1. Aplicar as migrações até `0004_system_bootstrap`.
2. Configurar `DATABASE_URL` para a base de dados pretendida.
3. Configurar o provedor OIDC e validar previamente o par exato `issuer` + `subject` do operador.
4. Executar o comando num ambiente administrativo controlado.
5. Confirmar que a conta OIDC indicada pertence à pessoa autorizada a assumir a administração técnica inicial.

## Execução

```bash
alembic upgrade head
python -m ponto_fora_api.bootstrap \
  --issuer "https://id.example.com/" \
  --subject "SUBJECT_OIDC_VALIDADO" \
  --display-name "Administrador da plataforma" \
  --reason "Bootstrap inicial autorizado e registado." \
  --confirm CREATE-INITIAL-PLATFORM-ADMIN
```

O parâmetro `--email` é opcional e não participa na identificação.

## Garantias implementadas

- Confirmação textual obrigatória.
- Validação HTTPS do issuer, sem credenciais, query ou fragmento.
- Validação de comprimento e presença de subject e nome.
- Verificação da existência e atividade de `PLATFORM_ADMIN`.
- Verificação de que o papel contém `identity.manage` e `roles.manage`.
- Recusa se existir atribuição histórica de `PLATFORM_ADMIN`.
- Marcador persistente de execução única, protegido por chave primária.
- Criação de utilizador, identidade, papel, evento de auditoria e marcador na mesma transação.
- Em conflito concorrente, a transação perdedora é revertida.
- Nenhum segredo OIDC é solicitado ou armazenado pelo comando.

## Limites

O comando não cria o provedor OIDC, não emite tokens, não configura o primeiro utilizador no IdP e não substitui a verificação humana da identidade. A proteção do host, das credenciais da base de dados e do próprio processo de execução continua a ser responsabilidade operacional.

O bootstrap não concede papéis editoriais. A atribuição posterior de papéis deve passar pelos serviços administrativos autorizados e pelas regras de separação de funções.

## Recuperação

Não apagar o marcador `system_bootstrap` para repetir o procedimento. Perda de acesso administrativo deve ser tratada como recuperação controlada, com evidência de autorização, revisão independente e procedimento próprio. Não usar downgrade da migração como mecanismo de recuperação.

## Histórico de alterações

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 1.0 | Especificação inicial do bootstrap local e de execução única. |
