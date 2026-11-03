# PONTO-FORA — aplicação HTTP inicial
# Identificador: PF-COD-API-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Ponto de entrada FastAPI e endpoint técnico de saúde.
# SHA-256 (conteúdo normalizado): 2deff6ae9348eec64aba63e80297b38cc6f4755e012a15710c8e22fa38ee60b4
# Commit de referência (base documental): ab40c30648ce632f24df6f7b767e7d026d23fffc

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
    """Indica se o processo HTTP está a responder.

    Este endpoint não verifica dependências externas nem representa
    uma declaração de prontidão para produção.
    """
    return {
        "status": "ok",
        "service": "ponto-fora-api",
        "version": __version__,
        "environment": os.getenv("PONTO_FORA_ENV", "local"),
    }
