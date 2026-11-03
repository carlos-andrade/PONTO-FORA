# PONTO-FORA — autenticação OIDC
# Identificador: PF-COD-AUTH-001
# Versão: 1.0
# Data de criação: 03/11/2026
# Data da última atualização: 03/11/2026
# Estado: Em desenvolvimento controlado
# Responsável: Engenharia de Software
# Âmbito: Validação de tokens Bearer JWT emitidos por um provedor OIDC.
# SHA-256 (conteúdo normalizado): 25f6d78a201c5b686d672d658c1e81493738a9aa34417f14354ffd1b992aa480
# Commit de referência (base documental): eaf2197a52de48c498f284a60d1aaf805b49e5b1

from dataclasses import dataclass
from os import getenv
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKClientConnectionError, PyJWKClientError


bearer_scheme = HTTPBearer(auto_error=False, scheme_name="OIDC Bearer")


class OIDCConfigurationError(ValueError):
    """Configuração OIDC ausente ou insegura."""


@dataclass(frozen=True, slots=True)
class OIDCSettings:
    issuer: str
    audience: str
    jwks_url: str
    leeway_seconds: int = 30

    def __post_init__(self) -> None:
        if not self.issuer.strip() or not self.audience.strip():
            raise OIDCConfigurationError("OIDC issuer e audience são obrigatórios.")
        _validate_https_url(self.issuer, "OIDC_ISSUER")
        _validate_https_url(self.jwks_url, "OIDC_JWKS_URL")
        if not 0 <= self.leeway_seconds <= 120:
            raise OIDCConfigurationError("OIDC_LEEWAY_SECONDS deve estar entre 0 e 120.")

    @classmethod
    def from_env(cls) -> "OIDCSettings":
        issuer = getenv("OIDC_ISSUER", "").strip()
        audience = getenv("OIDC_AUDIENCE", "").strip()
        jwks_url = getenv("OIDC_JWKS_URL", "").strip()
        if not issuer or not audience or not jwks_url:
            raise OIDCConfigurationError(
                "Defina OIDC_ISSUER, OIDC_AUDIENCE e OIDC_JWKS_URL."
            )
        try:
            leeway = int(getenv("OIDC_LEEWAY_SECONDS", "30"))
        except ValueError as exc:
            raise OIDCConfigurationError(
                "OIDC_LEEWAY_SECONDS deve ser um número inteiro."
            ) from exc
        return cls(issuer, audience, jwks_url, leeway)


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Identidade autenticada; não contém papéis nem permissões editoriais."""

    subject: str
    issuer: str
    email: str | None = None
    name: str | None = None

    @property
    def actor_id(self) -> str:
        return self.subject


def _validate_https_url(value: str, setting_name: str) -> None:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
        or parsed.query
    ):
        raise OIDCConfigurationError(
            f"{setting_name} deve ser uma URL HTTPS válida, sem credenciais, "
            "query string ou fragmento."
        )


def get_oidc_settings() -> OIDCSettings:
    try:
        return OIDCSettings.from_env()
    except OIDCConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação não está configurada corretamente.",
        ) from exc


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: OIDCSettings = Depends(get_oidc_settings),
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais Bearer obrigatórias.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if not token or len(token) > 16_384:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        jwks = PyJWKClient(
            settings.jwks_url,
            cache_jwk_set=True,
            lifespan=300,
            timeout=5,
            cache_keys=True,
        )
        signing_key = jwks.get_signing_key_from_jwt(token)
    except PyJWKClientConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provedor de identidade temporariamente indisponível.",
            headers={"Retry-After": "30"},
        ) from exc
    except PyJWKClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.audience,
            issuer=settings.issuer,
            leeway=settings.leeway_seconds,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 512:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificador de utilizador válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = claims.get("email")
    name = claims.get("name")
    return AuthenticatedPrincipal(
        subject=subject,
        issuer=settings.issuer,
        email=email if isinstance(email, str) else None,
        name=name if isinstance(name, str) else None,
    )
