# PONTO-FORA — testes do endpoint de saúde
# Identificador: PF-COD-TEST-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Testes HTTP automatizados da API inicial.
# SHA-256 (conteúdo normalizado): dfa825008d3e5aabfee18e91892f5d356a5ac5d19644c74d3d81708c72ce6b21
# Commit de referência (base documental): ab40c30648ce632f24df6f7b767e7d026d23fffc

from fastapi.testclient import TestClient

from ponto_fora_api import __version__
from ponto_fora_api.main import app

client = TestClient(app)


def test_health_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ponto-fora-api",
        "version": __version__,
        "environment": "local",
    }


def test_openapi_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "PONTO-FORA API"
