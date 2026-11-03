# GUIA DE DESENVOLVIMENTO — PONTO-FORA

**Identificador:** PF-DOC-DEV-001  
**Versão:** 1.0  
**Data de criação:** 03/11/2026  
**Data da última atualização:** 03/11/2026  
**Estado:** Em desenvolvimento controlado  
**Responsável:** Engenharia de Software  
**Âmbito:** Preparação do ambiente local e execução da API inicial.  
**SHA-256 (conteúdo normalizado):** 482414b762d642d50266c2a24c99cb0e99eedbff58d541dc1b7f450850c05f2a  
**Commit de referência (base documental):** ab40c30648ce632f24df6f7b767e7d026d23fffc

## 1. Requisitos

- Python 3.12 ou superior, dentro da versão suportada pelo projeto.
- Git.
- Acesso ao repositório `carlos-andrade/PONTO-FORA`.

## 2. Preparar o ambiente

Na raiz do repositório:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

No Windows PowerShell, ativar o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Executar a API

```bash
uvicorn ponto_fora_api.main:app --reload
```

Endereços locais:

- Saúde: `http://127.0.0.1:8000/health`
- OpenAPI: `http://127.0.0.1:8000/docs`

A variável `PONTO_FORA_ENV` altera o identificador do ambiente devolvido pelo endpoint:

```bash
PONTO_FORA_ENV=development uvicorn ponto_fora_api.main:app --reload
```

## 4. Validar alterações

```bash
ruff check .
pytest
```

## 5. Limites desta fundação

O endpoint `/health` confirma apenas que a aplicação HTTP responde. Não verifica PostgreSQL, Redis, armazenamento, fornecedores de IA ou integrações externas.

Nesta fase não existem autenticação, persistência, máquina de estados, execução de agentes ou publicação. Esses componentes pertencem às fases seguintes e não devem ser simulados por respostas deste endpoint.

## 6. Critério de conclusão da Fase A

A Fase A só poderá ser considerada concluída depois de:
1. a instalação limpa das dependências funcionar;
2. a API iniciar localmente;
3. os testes passarem;
4. o lint passar;
5. o workflow CI ser executado com sucesso no GitHub;
6. os ficheiros e respetivos hashes serem relidos e verificados.
