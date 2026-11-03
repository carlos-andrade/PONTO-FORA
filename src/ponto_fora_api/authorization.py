"""Identity resolution and server-side RBAC authorization primitives."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ponto_fora_api.auth import AuthenticatedPrincipal
from ponto_fora_api.models import (
    AuthorizationEvent,
    ExternalIdentity,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    utc_now,
)


class AuthorizationError(Exception):
    """Base class for authorization failures."""


class UnknownIdentity(AuthorizationError):
    """OIDC subject has not been explicitly linked to an internal user."""


class InactiveUser(AuthorizationError):
    """Internal user is disabled."""


class PermissionDenied(AuthorizationError):
    """The internal user does not hold the requested active permission."""


def resolve_active_user(db: Session, principal: AuthenticatedPrincipal) -> User:
    identity = db.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.issuer == principal.issuer,
            ExternalIdentity.subject == principal.subject,
        )
    )
    if identity is None:
        raise UnknownIdentity("Identidade OIDC não associada a um utilizador interno.")
    user = db.get(User, identity.user_id)
    if user is None or user.status != "ACTIVE":
        raise InactiveUser("Utilizador interno inexistente ou desativado.")
    return user


def user_has_permission(
    db: Session,
    user_id: UUID,
    permission_key: str,
    *,
    now: datetime | None = None,
) -> bool:
    instant = now or datetime.now(UTC)
    statement = (
        select(Permission.id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .join(User, User.id == UserRole.user_id)
        .where(
            User.id == user_id,
            User.status == "ACTIVE",
            UserRole.status == "ACTIVE",
            UserRole.scope_type.is_(None),
            UserRole.scope_id.is_(None),
            UserRole.valid_from <= instant,
            (UserRole.valid_until.is_(None) | (UserRole.valid_until > instant)),
            Role.is_active.is_(True),
            Permission.key == permission_key,
            Permission.is_active.is_(True),
        )
        .limit(1)
    )
    return db.scalar(statement) is not None


def require_permission(db: Session, user_id: UUID, permission_key: str) -> None:
    if not user_has_permission(db, user_id, permission_key):
        raise PermissionDenied(f"Permissão necessária: {permission_key}.")


def grant_role(
    db: Session,
    *,
    user_id: UUID,
    role_key: str,
    actor_id: str,
    reason: str,
    valid_until: datetime | None = None,
) -> UserRole:
    if not reason.strip():
        raise ValueError("A concessão de papel exige fundamentação.")
    user = db.get(User, user_id)
    if user is None or user.status != "ACTIVE":
        raise InactiveUser("Não é possível atribuir papéis a utilizador inativo.")
    role = db.scalar(select(Role).where(Role.key == role_key, Role.is_active.is_(True)))
    if role is None:
        raise ValueError("Papel inexistente ou inativo.")
    now = utc_now()
    if valid_until is not None and valid_until <= now:
        raise ValueError("A validade final deve estar no futuro.")
    existing = db.scalar(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
            UserRole.status == "ACTIVE",
            UserRole.scope_type.is_(None),
            UserRole.scope_id.is_(None),
        )
    )
    if existing is not None:
        raise ValueError("O utilizador já possui este papel global ativo.")
    assignment = UserRole(
        id=uuid4(),
        user_id=user_id,
        role_id=role.id,
        status="ACTIVE",
        valid_from=now,
        valid_until=valid_until,
        granted_by=actor_id,
        granted_at=now,
    )
    event = AuthorizationEvent(
        user_id=user_id,
        actor_id=actor_id,
        event_type="ROLE_GRANTED",
        role_key=role_key,
        reason=reason.strip(),
        payload={"user_role_id": str(assignment.id)},
        occurred_at=now,
    )
    db.add_all([assignment, event])
    db.commit()
    db.refresh(assignment)
    return assignment


def revoke_role(
    db: Session,
    *,
    user_id: UUID,
    role_key: str,
    actor_id: str,
    reason: str,
) -> UserRole:
    if not reason.strip():
        raise ValueError("A revogação de papel exige fundamentação.")
    role = db.scalar(select(Role).where(Role.key == role_key))
    if role is None:
        raise ValueError("Papel inexistente.")
    assignment = db.scalar(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
            UserRole.status == "ACTIVE",
            UserRole.scope_type.is_(None),
            UserRole.scope_id.is_(None),
        )
    )
    if assignment is None:
        raise ValueError("Não existe atribuição global ativa deste papel.")
    now = utc_now()
    assignment.status = "REVOKED"
    assignment.revoked_by = actor_id
    assignment.revoked_at = now
    db.add(AuthorizationEvent(
        user_id=user_id,
        actor_id=actor_id,
        event_type="ROLE_REVOKED",
        role_key=role_key,
        reason=reason.strip(),
        payload={"user_role_id": str(assignment.id)},
        occurred_at=now,
    ))
    db.commit()
    db.refresh(assignment)
    return assignment
