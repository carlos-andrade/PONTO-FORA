"""One-time, local CLI bootstrap for the first platform administrator."""

import argparse
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ponto_fora_api.db import SessionLocal
from ponto_fora_api.models import (
    AuthorizationEvent,
    ExternalIdentity,
    Permission,
    Role,
    RolePermission,
    SystemBootstrap,
    User,
    UserRole,
)

CONFIRMATION_PHRASE = "CREATE-INITIAL-PLATFORM-ADMIN"
BOOTSTRAP_KEY = "initial-admin"
BOOTSTRAP_ACTOR = "bootstrap:cli"


class BootstrapError(Exception):
    """Base exception for bootstrap failures."""


class BootstrapAlreadyCompleted(BootstrapError):
    """A bootstrap marker or prior administrator assignment already exists."""


def _validate_identity(issuer: str, subject: str, display_name: str, email: str | None) -> None:
    parsed = urlsplit(issuer)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or issuer != issuer.strip()
    ):
        raise ValueError("Issuer deve ser uma URL HTTPS válida, sem credenciais, query ou fragmento.")
    if not subject.strip() or len(subject) > 512:
        raise ValueError("Subject é obrigatório e deve ter até 512 caracteres.")
    if not display_name.strip() or len(display_name) > 240:
        raise ValueError("Nome de apresentação é obrigatório e deve ter até 240 caracteres.")
    if email is not None and (not email.strip() or len(email) > 320):
        raise ValueError("Email, quando informado, deve ter até 320 caracteres.")


def bootstrap_first_admin(
    db: Session,
    *,
    issuer: str,
    subject: str,
    display_name: str,
    email: str | None = None,
    reason: str,
    confirmation: str,
) -> User:
    """Create the first platform administrator atomically and exactly once."""
    _validate_identity(issuer, subject, display_name, email)
    if confirmation != CONFIRMATION_PHRASE:
        raise ValueError("Confirmação explícita inválida.")
    if not reason.strip() or len(reason) > 1000:
        raise ValueError("Fundamentação obrigatória (máximo 1000 caracteres).")

    try:
        with db.begin():
            marker = db.get(SystemBootstrap, BOOTSTRAP_KEY)
            if marker is not None:
                raise BootstrapAlreadyCompleted("O bootstrap inicial já foi concluído.")

            prior_admin = db.scalar(
                select(UserRole.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.key == "PLATFORM_ADMIN")
                .limit(1)
            )
            prior_admin_event = db.scalar(
                select(AuthorizationEvent.id)
                .where(
                    AuthorizationEvent.role_key == "PLATFORM_ADMIN",
                    AuthorizationEvent.event_type.in_(
                        ["ROLE_GRANTED", "BOOTSTRAP_COMPLETED"]
                    ),
                )
                .limit(1)
            )
            if prior_admin is not None or prior_admin_event is not None:
                raise BootstrapAlreadyCompleted(
                    "Já existe histórico de atribuição de PLATFORM_ADMIN; "
                    "o bootstrap não pode substituir uma administração existente."
                )

            role = db.scalar(
                select(Role).where(Role.key == "PLATFORM_ADMIN", Role.is_active.is_(True))
            )
            if role is None:
                raise BootstrapError("Papel PLATFORM_ADMIN inexistente ou inativo.")

            required_permissions = db.scalars(
                select(Permission)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(
                    RolePermission.role_id == role.id,
                    Permission.key.in_(["identity.manage", "roles.manage"]),
                    Permission.is_active.is_(True),
                )
            ).all()
            if {permission.key for permission in required_permissions} != {
                "identity.manage",
                "roles.manage",
            }:
                raise BootstrapError(
                    "PLATFORM_ADMIN não possui as permissões técnicas mínimas esperadas."
                )

            now = datetime.now(UTC)
            user = User(
                id=uuid4(),
                display_name=display_name.strip(),
                email=email.strip() if email else None,
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
            db.add(user)
            db.flush()

            db.add(ExternalIdentity(
                user_id=user.id,
                issuer=issuer,
                subject=subject,
                created_at=now,
            ))
            db.add(UserRole(
                user_id=user.id,
                role_id=role.id,
                status="ACTIVE",
                scope_type=None,
                scope_id=None,
                valid_from=now,
                valid_until=None,
                granted_by=BOOTSTRAP_ACTOR,
                granted_at=now,
            ))
            db.add(AuthorizationEvent(
                user_id=user.id,
                actor_id=BOOTSTRAP_ACTOR,
                event_type="BOOTSTRAP_COMPLETED",
                role_key="PLATFORM_ADMIN",
                reason=reason.strip(),
                payload={"identity_issuer": issuer, "method": "local_cli"},
                occurred_at=now,
            ))
            db.add(SystemBootstrap(
                bootstrap_key=BOOTSTRAP_KEY,
                user_id=user.id,
                completed_at=now,
            ))
            db.flush()
            return user
    except IntegrityError as exc:
        db.rollback()
        raise BootstrapAlreadyCompleted(
            "Conflito de integridade durante o bootstrap; nenhuma alteração foi mantida. "
            "Verifique se outro processo concluiu a operação."
        ) from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cria uma única vez o primeiro administrador técnico PONTO-FORA."
    )
    parser.add_argument("--issuer", required=True, help="Issuer OIDC HTTPS exato.")
    parser.add_argument("--subject", required=True, help="Claim sub do utilizador OIDC.")
    parser.add_argument("--display-name", required=True, help="Nome de apresentação.")
    parser.add_argument("--email", help="Email informativo; nunca usado como identidade.")
    parser.add_argument("--reason", required=True, help="Fundamentação auditável da operação.")
    parser.add_argument(
        "--confirm",
        required=True,
        help=f"Escreva exatamente {CONFIRMATION_PHRASE}.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    with SessionLocal() as db:
        user = bootstrap_first_admin(
            db,
            issuer=args.issuer,
            subject=args.subject,
            display_name=args.display_name,
            email=args.email,
            reason=args.reason,
            confirmation=args.confirm,
        )
    print(f"Bootstrap concluído. Utilizador interno: {user.id}")
    print("A identidade OIDC foi associada e PLATFORM_ADMIN foi atribuído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
