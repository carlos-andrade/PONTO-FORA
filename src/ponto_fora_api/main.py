# PONTO-FORA — aplicação HTTP
# Identificador: PF-COD-API-001
# Versão: 1.1
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Ponto de entrada FastAPI, health check e consultas do núcleo editorial.
# SHA-256 (conteúdo normalizado): PENDING
# Commit de referência (base documental): eba38c76bd8fe4fbddf6fbef8a9419ebdd9319d4

import os

from fastapi import FastAPI

from ponto_fora_api import __version__
from ponto_fora_api.api.assignments import router as assignments_router

app = FastAPI(
    title="PONTO-FORA API",
    description="API da plataforma editorial PONTO-FORA.",
    version=__version__,
)

app.include_router(assignments_router)


@app.get("/health", tags=["Operação"])
def health_check() -> dict[str, str]:
    """Indica se o processo HTTP está a responder, sem validar dependências."""
    return {
        "status": "ok",
        "service": "ponto-fora-api",
        "version": __version__,
        "environment": os.getenv("PONTO_FORA_ENV", "local"),
    }
