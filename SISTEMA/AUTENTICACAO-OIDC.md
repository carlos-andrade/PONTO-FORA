# AUTENTICAÇÃO OIDC — PONTO-FORA

**Identificador:** PF-SYS-AUTH-001  
**Versão:** 1.0  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Em desenvolvimento controlado  
**Responsável:** Engenharia de Software  
**Âmbito:** Contrato de autenticação da API através de tokens JWT emitidos por um provedor OpenID Connect.  
**SHA-256 (conteúdo normalizado):** 4974fd53d93a805752bbdd283167d38e5d2e72306978303a59a93178840a59e1  
**Commit de referência (base documental):** eaf2197a52de48c498f284a60d1aaf805b49e5b1

## 1. Objetivo

Definir a primeira camada de identidade da API PONTO-FORA. Esta etapa autentica a identidade técnica apresentada por um provedor OpenID Connect (OIDC), sem atribuir papéis editoriais nem conceder permissões de negócio.

## 2. Decisão técnica

A API valida tokens de acesso JWT assinados com RS256, utilizando as chaves públicas publicadas no endpoint JWKS configurado. O provedor de identidade permanece substituível, desde que cumpra o contrato configurado.

A implementação não escolhe nem instala um servidor de identidade. A escolha entre Keycloak, Authentik ou outro provedor compatível fica para a configuração de implantação.

## 3. Configuração

| Variável | Finalidade |
|---|---|
| `OIDC_ISSUER` | Identificador exato do emissor esperado no claim `iss`. |
| `OIDC_AUDIENCE` | Audiência esperada no claim `aud`, correspondente à API. |
| `OIDC_JWKS_URL` | URL HTTPS do conjunto de chaves públicas JWKS. |
| `OIDC_LEEWAY_SECONDS` | Tolerância de relógio; padrão 30, máximo 120. |

Exemplo ilustrativo — substituir pelos valores reais do provedor:

```dotenv
OIDC_ISSUER=https://identity.example.com/
OIDC_AUDIENCE=ponto-fora-api
OIDC_JWKS_URL=https://identity.example.com/.well-known/jwks.json
OIDC_LEEWAY_SECONDS=30
```

Não guardar tokens, segredos ou chaves privadas no repositório. O endpoint JWKS contém chaves públicas e deve ser obtido da configuração oficial do provedor.

## 4. Validações obrigatórias

A camada de autenticação:
- aceita apenas o esquema HTTP Bearer;
- limita o tamanho do token a 16 KiB;
- aceita exclusivamente o algoritmo RS256 nesta primeira versão;
- valida assinatura com chave pública obtida por JWKS;
- valida emissor, audiência e expiração;
- exige os claims `exp` e `sub`;
- rejeita identificadores vazios ou excessivamente longos;
- usa cache de chaves JWKS com prazo limitado;
- devolve 401 para credenciais inválidas e 503 para indisponibilidade do provedor.

As URLs do emissor e JWKS devem usar HTTPS e não podem conter credenciais, query string ou fragmento.

## 5. Identidade e separação de responsabilidades

O principal autenticado contém `subject`, `issuer` e os atributos opcionais `email` e `name`.

**Os claims de papéis, grupos ou permissões presentes no token são deliberadamente ignorados nesta fase.** A autorização editorial será implementada separadamente na Fase D2, através de RBAC controlado pela aplicação. Um token válido comprova identidade, não autoridade editorial.

## 6. Limites desta entrega

- Nenhuma rota editorial foi montada ou exposta.
- Não existe associação persistente entre utilizadores e registos internos.
- Não há criação, suspensão ou gestão de utilizadores.
- Não há RBAC, decisões humanas nem autorização de publicação.
- Não foi escolhido ou instalado um provedor de identidade.
- A implementação pressupõe tokens JWT RS256; tokens opacos ou algoritmos diferentes não são aceites.

## 7. Critérios de aceitação D1

- Configuração incompleta falha de forma segura.
- URLs HTTP ou malformadas são rejeitadas.
- Tokens sem Bearer, inválidos, expirados ou com claims incorretos recebem 401.
- Indisponibilidade JWKS recebe 503.
- A identidade deriva exclusivamente de claims validados criptograficamente.
- Papéis presentes no token não são convertidos em permissões.
- Testes automatizados cobrem sucesso e falhas.
- A API continua sem rotas editoriais públicas até D2/D3.

## 8. Histórico de alterações

| Data | Versão | Alteração |
|---|---|---|
| 03/11/2026 | 1.0 | Definição do contrato OIDC e dos limites da primeira entrega de autenticação. |
