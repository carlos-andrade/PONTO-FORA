# PONTO-FORA — aplicação HTTP
# Identificador: PF-COD-API-001
# Versão: 1.2
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Ponto de entrada FastAPI e health check técnico.
# SHA-256 (conteúdo normalizado): PENDING
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

import os

from fastapi import FastAPI

from ponto_fora_api import __version__

app = FastAPI(
    title="PONTO-FORA API",
    description="API da plataforma editorial PONTO-FORA.",
    version=__version__,
)


@app.get("/health", tags=["Operação"])
def health_check() -> dict[str, str]:
    """Confirma apenas que o processo HTTP está a responder."""
    return {
        "status": "ok",
        "service": "ponto-fora-api",
        "version": __version__,
        "environment": os.getenv("PONTO_FORA_ENV", "local"),
    }


# Rotas editoriais não são montadas até existir autenticação e RBAC.
