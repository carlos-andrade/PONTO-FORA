# PONTO-FORA — testes de autenticação OIDC
# Identificador: PF-TEST-AUTH-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Testes unitários de configuração, validação JWT e falhas do provedor.
# SHA-256 (conteúdo normalizado): 277c3663041b048f38e0295dc200c31bb96d53c1529f01fd494caa2bd5635de9
# Commit de referência (base documental): 88db30df8317ad26a44fa4be7b2c794984cc9f1c

from unittest.mock import Mock

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jwt import PyJWKClientConnectionError

from ponto_fora_api import auth


@pytest.fixture
def settings() -> auth.OIDCSettings:
    return auth.OIDCSettings(
        issuer="https://identity.example.com/",
        audience="ponto-fora-api",
        jwks_url="https://identity.example.com/.well-known/jwks.json",
    )


@pytest.fixture
def credentials() -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="signed-token")


def test_settings_reject_insecure_issuer() -> None:
    with pytest.raises(auth.OIDCConfigurationError):
        auth.OIDCSettings(
            issuer="http://identity.example.com",
            audience="ponto-fora-api",
            jwks_url="https://identity.example.com/jwks",
        )


def test_settings_reject_url_with_credentials() -> None:
    with pytest.raises(auth.OIDCConfigurationError):
        auth.OIDCSettings(
            issuer="https://user:password@identity.example.com",
            audience="ponto-fora-api",
            jwks_url="https://identity.example.com/jwks",
        )


def test_settings_reject_excessive_clock_leeway() -> None:
    with pytest.raises(auth.OIDCConfigurationError):
        auth.OIDCSettings(
            issuer="https://identity.example.com",
            audience="ponto-fora-api",
            jwks_url="https://identity.example.com/jwks",
            leeway_seconds=121,
        )


def test_missing_bearer_credentials_are_rejected(settings) -> None:
    with pytest.raises(HTTPException) as error:
        auth.get_current_principal(credentials=None, settings=settings)
    assert error.value.status_code == 401
    assert error.value.headers["WWW-Authenticate"] == "Bearer"


def test_valid_token_returns_identity_without_roles(
    monkeypatch, settings, credentials
) -> None:
    jwks = Mock()
    jwks.get_signing_key_from_jwt.return_value = Mock(key="public-key")
    monkeypatch.setattr(auth.jwt, "PyJWKClient", Mock(return_value=jwks))
    decode = Mock(return_value={
        "sub": "user-123",
        "email": "editor@example.com",
        "name": "Editorial User",
        "roles": ["ADMIN"],
    })
    monkeypatch.setattr(auth.jwt, "decode", decode)

    principal = auth.get_current_principal(credentials=credentials, settings=settings)

    assert principal.subject == "user-123"
    assert principal.actor_id == "user-123"
    assert principal.issuer == settings.issuer
    assert principal.email == "editor@example.com"
    assert principal.name == "Editorial User"
    assert not hasattr(principal, "roles")
    assert decode.call_args.kwargs["algorithms"] == ["RS256"]
    assert decode.call_args.kwargs["audience"] == settings.audience
    assert decode.call_args.kwargs["issuer"] == settings.issuer


def test_invalid_signature_is_rejected(monkeypatch, settings, credentials) -> None:
    jwks = Mock()
    jwks.get_signing_key_from_jwt.return_value = Mock(key="public-key")
    monkeypatch.setattr(auth.jwt, "PyJWKClient", Mock(return_value=jwks))
    monkeypatch.setattr(
        auth.jwt, "decode", Mock(side_effect=jwt.InvalidSignatureError("invalid"))
    )
    with pytest.raises(HTTPException) as error:
        auth.get_current_principal(credentials=credentials, settings=settings)
    assert error.value.status_code == 401


def test_jwks_connection_failure_returns_service_unavailable(
    monkeypatch, settings, credentials
) -> None:
    jwks = Mock()
    jwks.get_signing_key_from_jwt.side_effect = PyJWKClientConnectionError("offline")
    monkeypatch.setattr(auth.jwt, "PyJWKClient", Mock(return_value=jwks))
    with pytest.raises(HTTPException) as error:
        auth.get_current_principal(credentials=credentials, settings=settings)
    assert error.value.status_code == 503
    assert error.value.headers["Retry-After"] == "30"


def test_token_without_subject_is_rejected(monkeypatch, settings, credentials) -> None:
    jwks = Mock()
    jwks.get_signing_key_from_jwt.return_value = Mock(key="public-key")
    monkeypatch.setattr(auth.jwt, "PyJWKClient", Mock(return_value=jwks))
    monkeypatch.setattr(auth.jwt, "decode", Mock(return_value={"exp": 2_000_000_000}))
    with pytest.raises(HTTPException) as error:
        auth.get_current_principal(credentials=credentials, settings=settings)
    assert error.value.status_code == 401


def test_malformed_token_header_is_rejected(monkeypatch, settings, credentials) -> None:
    jwks = Mock()
    jwks.get_signing_key_from_jwt.side_effect = jwt.DecodeError("malformed")
    monkeypatch.setattr(auth.jwt, "PyJWKClient", Mock(return_value=jwks))
    with pytest.raises(HTTPException) as error:
        auth.get_current_principal(credentials=credentials, settings=settings)
    assert error.value.status_code == 401
